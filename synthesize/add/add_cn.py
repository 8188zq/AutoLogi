import openai
import json
import re
import ast
from tqdm import tqdm
import argparse
import random
import requests
import logging
import time
import copy
import traceback
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from prompts.add import find_new_constraints_prompt_cn, find_new_constraints_prompt_en

def extract_json_blocks(markdown_text):
    pattern = re.compile(r'```json(.*?)```', re.DOTALL)
    code_blocks = pattern.findall(markdown_text)
    return code_blocks

def analyze_input(api_key, input_text, model_name='qwen-72b-instruct'):
    client = openai.OpenAI(api_key=api_key, base_url="")

    completion = client.chat.completions.create(
        model="qwen-72b-instruct",
        messages=[{'role': 'system', 'content': 'You are a helpful assistant.'},
                  {'role': 'user', 'content': input_text }],
        top_p=0.8,
        temperature=0.7,
        extra_body={
            'top_k': 20,
            'repetition_penalty': 1.05,
        },
    )
    content = completion.choices[0].message.content
    return content

CALL_URL = ''
HEADERS = {'Content-Type': 'application/json',
           "Authorization": f"Bearer {os.environ['DASHSCOPE_API_KEY']}"
          }

def dash_call(**kwargs):
    payload = copy.deepcopy(kwargs)
    assert 'model' in payload
    max_try = 8
    for i in range(max_try):
        try:
            ret = requests.post(CALL_URL, json=payload,
                                headers=HEADERS, timeout=180)
            if ret.status_code != 200:
                raise Exception(f"http status_code: {ret.status_code}\n{ret.content}")
            ret_json = ret.json()
            for output in ret_json['choices']:
                if output['finish_reason'] not in ['stop', 'function_call']:
                    raise Exception(f'openai finish with error...\n{ret_json}')
            return ret_json['choices'][0]['message']['content']
        except Exception as e:
            print(traceback.format_exc())
            time.sleep(10)
    raise Exception('Max Retry...')

def get_content(api_key, input_text, model_name='gpt-4'):
    seed = random.randint(0, 9999)
    messages=[{'role': 'system', 'content': 'You are a helpful assistant.'},
                  {'role': 'user', 'content': input_text }]
    call_args = dict(
            messages=messages,
            model = model_name,
        )
    api_key = os.getenv('DASHSCOPE_API_KEY')
    content = dash_call(**call_args)
    return content

def set_to_list(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

def save_data(data, save_path, debug=False):
    if debug:
        with open(save_path, "w") as f:
            f.write(json.dumps(data, ensure_ascii=False, default=set_to_list, indent=4))
    else:
        with open(save_path, "a") as f:
            f.write(repr(data))
            f.write("\n")
            f.flush()
        with open(save_path.replace(".jsonl","_for_read.jsonl"), "a") as f:
            f.write(json.dumps(data, ensure_ascii=False, default=set_to_list))
            f.write("\n")
            f.flush()

def count_calls(func):
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        args_repr = [repr(a) for a in args]  
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  
        signature = ", ".join(args_repr + kwargs_repr)  
        # signature = ", ".join(args_repr)
        wrapper.calls_args.append(signature)
        result = func(*args, **kwargs)
        if result:
            wrapper.true_calls_args.append(signature)
        return result
    
    def reset():
        wrapper.calls = 0
        wrapper.calls_args = []
        wrapper.true_calls_args = []

    wrapper.calls = 0
    wrapper.calls_args = []
    wrapper.true_calls_args = []  
    wrapper.reset = reset
    return wrapper

@count_calls
def verify_function(inputs, inputs_check, constraint_list):
    if not inputs_check(inputs):  
            return False
    for constraint in constraint_list:
        if not constraint(inputs): 
            return False
    return True

def extract_code_blocks(markdown_text):
    pattern = re.compile(r'```python(.*?)```', re.DOTALL)
    code_blocks = pattern.findall(markdown_text)
    return code_blocks

def extract_json_blocks(markdown_text):
    pattern = re.compile(r'```json(.*?)```', re.DOTALL)
    code_blocks = pattern.findall(markdown_text)
    return code_blocks

def parse(content):
    sections = content.split('### ')[1:]
    result = {}

    for section in sections:
        lines = section.split('\n', 1)
        if len(lines) == 2:
            key, value = lines
            # value = value.replace('`', '').strip()
            value = value.strip()
            result[key.strip()] = value
    return result

def traverse(example, Constraint_List_code):
    namespace = {"verify_function": verify_function}
    exec(Constraint_List_code, namespace)
    exec(example["Inputs_Check_code"],namespace)
    code_to_test = example["Traverse_code"]
    exec(code_to_test,namespace)
    exec(f"verify_function.reset()" + f"\ntot_calls = verify_function.calls" + f"\npara_list = verify_function.calls_args" + f"\ntrue_calls_args = verify_function.true_calls_args",namespace)
    result, total = namespace['count_valid_arrangements']()
    solution_space = [ast.literal_eval(x.split(', <function')[0]) for x in namespace['true_calls_args']]
    solution_space_size = len(solution_space)
    return solution_space, solution_space_size, result


def main(api_key, model_name, example, save_path, debug=False):
    temp = copy.deepcopy(example)
    temp["turn"] = 0
    save_data(temp, save_path, debug)
    if temp['solution_space_size']<=1:
        return
    max_retries = 3
    cur_retries = 0
    while cur_retries < max_retries:
        try:
            background = temp['question_dict']['background']
            logic_constraints = temp['question_dict']['logic_constraints']
            solution_space = temp['solution_space']
            Constraint_List_code = temp['Constraint_List_code']
            input_prompt = find_new_constraints_prompt_cn.replace("[[[background]]]", background).replace("[[[logic_constraints]]]", logic_constraints).replace("[[[solution_space]]]",repr(solution_space)).replace("[[[Constraint_List_code]]]", Constraint_List_code).strip()
            content = get_content(api_key, input_prompt, model_name)
            with open("/mnt/data/zq/COLLING_PAPER/add/debug/raw_content_log.json", "w") as f:
                f.write(content+"\n"+"*"*50+"\n")
                f.flush()
            parsed_content = parse(content)
            New_Constraints = extract_json_blocks(parsed_content.get('Constraints', content))
            Constraint_List_code = extract_code_blocks(parsed_content.get('Code',content))
            assert len(New_Constraints) >=1 and len(Constraint_List_code) >=1, f"Extract blocks not found!"
            New_Constraints = ast.literal_eval(New_Constraints[0].strip("\n").strip())["new_constraints"]
            Constraint_List_code = Constraint_List_code[0].strip("\n").strip()
            solution_space,solution_space_size,solution_space_size_v2 = traverse(temp, Constraint_List_code)
            if solution_space_size < 1:
                cur_retries += 1
                continue
            if solution_space_size < temp['solution_space_size']:
                temp['solution_space'] = solution_space
                temp['solution_space_size'] = solution_space_size
                temp['solution_space_size_v2'] = solution_space_size_v2
                temp['Constraint_List_code'] = Constraint_List_code
                temp['turn'] += 1
                if isinstance(New_Constraints,str):
                    New_Constraints = [New_Constraints]
                temp['question_dict']['logic_constraints'] = temp['question_dict']['logic_constraints'].strip("。")+";"+";".join(New_Constraints)
                save_data(temp, save_path, debug)
            else:
                cur_retries += 1
                continue
            if solution_space_size == 1:
                break
        except Exception as e:
            tb_str = traceback.format_exc()  
            print("An error occurred:", tb_str)
            cur_retries += 1

def run_concurrent_main(api_key, model_name, datas, save_path, debug=False):
    with ThreadPoolExecutor(max_workers=10) as executor:  
        future_to_data = {executor.submit(main, api_key, model_name, data, save_path, debug): data for data in datas}
        
        for future in tqdm(as_completed(future_to_data), total=len(datas)):
            data = future_to_data[future]
            try:
                future.result()  
            except Exception as exc:
                print(f"Data ID {data['id']} generated an exception: {exc}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the new code after the add of constrainsts and check the results!")
    parser.add_argument("--name", type=str, default="example")
    parser.add_argument("--debug", action='store_true', help="If set, runs in debug mode.")
    args = parser.parse_args()
    input_path = f"./synthesize/add/output_cn/{args.name}_prepocessed.jsonl"
    save_path = f"./synthesize/add/output_cn/{args.name}_final.jsonl"
    
    api_key = os.getenv('OPEN_AI_API_KEY')
    model_name = "gpt-4o-2024-08-06" 
    model_name = "gpt-4-turbo"
    
    with open(input_path, 'r') as f:
        datas = [ast.literal_eval(line) for line in f]
    run_concurrent_main(api_key, model_name, datas, save_path, args.debug)
        


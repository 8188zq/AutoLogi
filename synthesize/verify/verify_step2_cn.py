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
import os
import copy
from concurrent.futures import ThreadPoolExecutor, as_completed

from prompts.verify import build_verify_function_prompt_cn,build_verify_function_prompt_en
from utils.call_openai import call_openai

def set_to_list(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

def verify_function(inputs, inputs_check, constraint_list):
    if not inputs_check(inputs):
            return False
    for constraint in constraint_list:
        if not constraint(inputs):  
            return False
    return True

def save_data(data, save_path, debug=False):
    if debug:
        with open(save_path, "w") as f:
            f.write(json.dumps(data, ensure_ascii=False, default=set_to_list, indent=4))
    else:
        with open(save_path, "a") as f:
            f.write(repr(data))
            f.write("\n")
            f.flush()


def get_content(api_key, input_text, model_name='gpt-4 8K'):
    seed = random.randint(0, 9999)
    messages=[{'role': 'system', 'content': 'You are a helpful assistant.'},
                  {'role': 'user', 'content': input_text }]
    call_args = dict(
            messages=messages,
            model = model_name,
        )
    content = call_openai(**call_args)
    return content

def extract_code_blocks(markdown_text):
    pattern = re.compile(r'```python(.*?)```', re.DOTALL)
    code_blocks = pattern.findall(markdown_text)
    return code_blocks

def extract_json_blocks(markdown_text):
    pattern = re.compile(r'```json(.*?)```', re.DOTALL)
    code_blocks = pattern.findall(markdown_text)
    return code_blocks

def format_verify_prompt(data):
    prompt = build_verify_function_prompt_cn
    return prompt.replace("[[[background]]]", data['question_dict']['background'] ).replace("[[[logic_constraints]]]", data['question_dict']['logic_constraints'] ).strip()

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

def main(api_key, model_name, data, save_path, debug=False):
    input_prompt = format_verify_prompt(data)
    idx = data['id']
    max_retries = 3
    cur_retries = 0
    while cur_retries < max_retries:
        try:
            content = get_content(api_key, input_prompt, model_name)
            parsed_content = parse(content)
            Inputs_Check_code = extract_code_blocks(parsed_content['Inputs_Check_Function'])
            Constraint_List_code = extract_code_blocks(parsed_content['Constraint_List'])
            Inputs_Example = extract_code_blocks(parsed_content['Inputs_Example'])
            assert len(Inputs_Check_code) >=1 and len(Constraint_List_code) >=1 and len(Inputs_Example)>=1, f"Extract blocks not found!"
            Inputs_Check_code = Inputs_Check_code[0].strip("\n").strip()
            Constraint_List_code = Constraint_List_code[0].strip("\n").strip()
            Inputs_Example = Inputs_Example[0].strip("\n").strip()
            import traceback
            try:
                Inputs_Example = ast.literal_eval(Inputs_Example)
                namespace = {"Inputs_Example": Inputs_Example, "verify_function": verify_function}
                exec(Inputs_Check_code + "\n" + Constraint_List_code, namespace)
                assert namespace['inputs_check'](Inputs_Example) is True, f"Inputs check failed!"
                res = verify_function(Inputs_Example, namespace['inputs_check'], namespace['constraint_list'])
                if res is True:
                    data['verify_correctness'] = True
                else:
                    data['verify_correctness'] = False
                break
            except Exception as e:
                tb_str = traceback.format_exc()  
                print("An error occurred:", tb_str)
                raise e
        except Exception as e:
            print(f"Error: {e}")
            print(Inputs_Check_code + "\n" + Constraint_List_code)
            cur_retries += 1
    if cur_retries == max_retries:
        with open("./synthesize/verify/debug/failed_idx_step2.txt", "a") as f:
            f.write(f"{idx}\n")
        print(f"Failed to get content for input_idx: {idx}")
        return
    else:
        data["Analysis"] = parsed_content['Analysis']
        data['Inputs_Format'] = parsed_content['Inputs_Format']
        data['Inputs_Check_code'] = Inputs_Check_code
        data['Constraint_List_code'] = Constraint_List_code
        data['Inputs_Example'] = Inputs_Example
        if debug:
            print(f"{data}\n")
            return
        save_data(data, save_path, debug)

def run_concurrent_main(api_key, model_name, datas, save_path, debug=False):
    with ThreadPoolExecutor(max_workers=5) as executor:  
        future_to_data = {executor.submit(main, api_key, model_name, data, save_path, debug): data for data in datas}
        
        for future in tqdm(as_completed(future_to_data), total=len(datas)):
            data = future_to_data[future]
            try:
                future.result()
            except Exception as exc:
                print(f"Data ID {data['id']} generated an exception: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the best verify code and get the results!")
    parser.add_argument("--debug", action='store_true', help="If set, runs in debug mode.")
    parser.add_argument("--name", type=str, default="example")
    parser.add_argument("--verify_turn_id", type=int, default=1)
    parser.add_argument("--traverse_turn_id", type=int, default=1)
    parser.add_argument("--max_traverse_time", type=int, default=3)

    args = parser.parse_args()
    verify_turn_id = args.verify_turn_id
    traverse_turn_id = args.traverse_turn_id
    if verify_turn_id == 1:
        use_cache = False
    else:
        use_cache = True
    input_path = f"./synthesize/verify/output_cn/{args.name}.jsonl"
    save_path = f"./synthesize/verify/output_cn/{args.name}_v{verify_turn_id}.{traverse_turn_id}.jsonl"

    api_key = os.getenv("OPENAI_API_KEY")
    # model_name = "gpt-4o-2024-08-06" 
    model_name = "gpt-4-0613"
    cache_id = []
    cache = {}
    if args.debug:
        from prompts.verify import question_dict
        data = {}
        data['question_dict'] = question_dict
        data['id'] = 0 
        main(api_key, model_name, data, save_path, args.debug)
    else:
        with open(input_path, 'r') as f:
            datas = [json.loads(line) for line in f]
        if use_cache and verify_turn_id>1:
            cache_path = f"./synthesize/traverse/output_cn/{args.name}_v{verify_turn_id-1}.{args.max_traverse_time}.jsonl"
            with open(cache_path, "r") as f:
                for line in f:
                # data = json.loads(line)
                    data = ast.literal_eval(line)
                    if data.get("solution_space_size_v2",0) !=0:
                        cache_id.append(data['id'])
                        cache[data['id']] = data
            print(f"Cache id len: {len(cache_id)}")
            print(f"left jobs: {len(datas) - len(cache_id)}")

        for data in tqdm(datas) :
            if data['id'] in cache_id:
                save_data(cache[data['id']], save_path, args.debug)
        datas = list(filter(lambda data: data['id'] not in cache_id, datas))
        run_concurrent_main(api_key, model_name, datas, save_path, args.debug)
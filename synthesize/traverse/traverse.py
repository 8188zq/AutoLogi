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
from pebble import ProcessPool
from concurrent.futures import ThreadPoolExecutor, as_completed

from prompts.traverse import traverse_prompt_cn_v2, traverse_prompt_en_v2

def set_to_list(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

def count_calls(func):
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        args_repr = [repr(a) for a in args]  
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]  
        signature = ", ".join(args_repr + kwargs_repr)  
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

CALL_URL = ''
HEADERS = {'Content-Type': 'application/json',
           "Authorization": f"Bearer {os.environ['DASHSCOPE_API_KEY']}"
          }

def dash_call(**kwargs):
    payload = copy.deepcopy(kwargs)
    assert 'model' in payload
    max_try = 3
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
    content = dash_call(**call_args)
    return content

def extract_code_blocks(markdown_text):
    pattern = re.compile(r'```python(.*?)```', re.DOTALL)
    code_blocks = pattern.findall(markdown_text)
    return code_blocks

def format_traverse_prompt(data):
    prompt = traverse_prompt_en_v2
    return prompt.replace("[[[background]]]", data['question_dict']['background']).replace("[[[inputs_format]]]", data['Inputs_Format']).replace("[[[inputs_example]]]", repr(data['Inputs_Example'])).strip()



def main(data, api_key, model_name, save_path, debug=False):
    input_prompt = format_traverse_prompt(data)
    max_retries = 3
    cur_retries = 0
    while cur_retries < max_retries:
        namespace = {
            'verify_function': verify_function,
        }
        try:
            content = get_content(api_key, input_prompt, model_name)
            with open("./synthesize/traverse/debug/raw_content_log.json", "w") as f:
                f.write(content+"\n"+"*"*50+"\n")
                f.flush()
            code = extract_code_blocks(content)
            print("begin to extract code...")
            assert len(code) >=1 , f"Code blocks not found!"
            code = code[0].strip("\n").strip()
            with open("./synthesize/traverse/debug/code.json", "w") as f:
                f.write(json.dumps(code, ensure_ascii=False, indent=4) + "\n")
                f.flush()
            print("extracted code successfully!")
            import traceback
            try:
                # signal.alarm(10)
                code_to_test = data['Inputs_Check_code'] + "\n" + data['Constraint_List_code'] + "\n" + code + f"\nverify_function.reset()" + f"\ntot_calls = verify_function.calls" + f"\npara_list = verify_function.calls_args" + f"\ntrue_calls_args = verify_function.true_calls_args"
                exec(code_to_test, namespace)
                if namespace['tot_calls'] > 0:
                    data['domain_size'] = len(namespace['para_list'])
                    data['solution_space_size'] = len(namespace['true_calls_args'])
                    result, total = namespace['count_valid_arrangements']()
                    if 2*result != data['solution_space_size'] or 2*total != data['domain_size']:
                        data['traverse_success'] = False
                    else:
                        data['traverse_success'] = True
                else:
                    result, total = namespace['count_valid_arrangements']()
                    data['domain_size'] = len(namespace['para_list'])
                    data['solution_space_size'] = len(namespace['true_calls_args'])
                    if result != data['solution_space_size'] or total != data['domain_size']:
                        data['traverse_success'] = False
                    else:
                        data['traverse_success'] = True
                break
            except Exception as e:
                tb_str = traceback.format_exc()  
                print("An error occurred:", tb_str)
                raise e
        except Exception as e:
            print(f"Error: {e}")
            cur_retries += 1
        # finally:
        #     signal.alarm(0)
    if cur_retries == max_retries:
        idx = data["id"]
        with open("./synthesize/traverse/debug/failed_idx.txt", "a") as f:
            f.write(f"{idx}\n")
        print(f"Failed to get content for input_idx: {idx}")
        return
    else:
        data['Traverse_code'] = code
        data['solution_space_size_v2'] = result
        data['domain_size_v2'] = total
        if debug:
            print(f"{data}\n")
            return
        save_data(data, save_path, debug)
        return 
        # print(f"Parsed content: {parsed_content}\n")

def run_concurrent_main(api_key, model_name, datas, save_path, debug=False):
    with ProcessPool(max_workers=20) as pool:
        from functools import partial
        new_main = partial(main, api_key=api_key, model_name=model_name, save_path= save_path, debug=debug)
        future = pool.map(new_main, datas, timeout=40)
        iterator = future.result()
        while True:
            try:
                next(iterator)
            except StopIteration:
                break
            except TimeoutError as error:
                print(error)
            except Exception as error:
                print(error)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the best traverse code and get the results!")
    parser.add_argument("--debug", action='store_true', help="If set, runs in debug mode.")
    parser.add_argument("--name", type=str, default="example")
    parser.add_argument("--verify_turn_id", type=int, default=1)
    parser.add_argument("--traverse_turn_id", type=int, default=1)
    # parser.add_argument("--max_traverse_time", type=int, default=3)
    args = parser.parse_args()
    verify_turn_id = args.verify_turn_id
    traverse_turn_id = args.traverse_turn_id
    input_path = f"./synthesize/verify/output_en/{args.name}_v{verify_turn_id}.1.jsonl"
    cache_path = f"./synthesize/traverse/output_en/{args.name}_v{verify_turn_id}.{traverse_turn_id-1}.jsonl"
    save_path = f"./synthesize/traverse/output_en/{args.name}_v{verify_turn_id}.{traverse_turn_id}.jsonl"
    api_key = os.getenv("DASHSCOPE_API_KEY")
    model_name = "gpt-4o-2024-08-06" 
    model_name = "gpt-4-turbo"
    cache_id = []
    cache = {}
    use_cache = True
    if use_cache and traverse_turn_id>1:  
        with open(cache_path, "r") as f:
            for line in f:
                data = ast.literal_eval(line)
                if data.get("solution_space_size_v2",0) !=0:
                    cache[data['id']] = data
            print(f"Cache id len: {len(cache_id)}")

    if args.debug:
        idx = 0
        from prompts.traverse import question_dict_debug, inputs_format_debug, inputs_example_debug, inputs_check_debug, constraint_list_debug
        data = {}
        data['question_dict'] = question_dict_debug
        data['Inputs_Check_code'] = inputs_check_debug
        data['Constraint_List_code'] = constraint_list_debug
        data['Inputs_Format'] = inputs_format_debug
        data['Inputs_Example'] = inputs_example_debug
        main(api_key, model_name, data, save_path, args.debug)
    else:
        written_id = []
        with open(input_path, 'r') as f:
            datas = [ast.literal_eval(line) for line in f]
        for data in tqdm(datas) :
            if data.get("solution_space_size_v2",0) !=0:
                save_data(data, save_path, args.debug)
                written_id.append(data['id'])
                continue
            if data['id'] in cache_id:
                save_data(cache[data['id']], save_path, args.debug)
                written_id.append(data['id'])
                continue
            # main(data, api_key, model_name, args.save_path, args.debug)
        datas = list(filter(lambda data: data['id'] not in written_id, datas))
        run_concurrent_main(api_key, model_name, datas, save_path, args.debug)
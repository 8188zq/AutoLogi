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
import os

from prompts.merge_constraints import merge_constraints_prompt_cn,merge_constraints_prompt_en
from utils.call_openai import call_openai

def extract_json_blocks(markdown_text):
    pattern = re.compile(r'```json(.*?)```', re.DOTALL)
    code_blocks = pattern.findall(markdown_text)
    return code_blocks

def get_content(api_key, input_text, model_name='gpt-4 8K'):
    seed = random.randint(0, 9999)
    messages=[{'role': 'system', 'content': 'You are a helpful assistant.'},
                  {'role': 'user', 'content': input_text }]
    call_args = dict(
            messages=messages,
            max_completion_tokens=4096,
            model = model_name,
        )
    api_key = os.getenv('OPENAI_API_KEY', api_key)
    content = call_openai(**call_args)
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

def main(api_key, model_name, example, save_path, debug=False):
    logic_constraints_raw = example["question_dict"]["logic_constraints"]
    logic_constraints_list = re.split(r';|；', logic_constraints_raw)
    namespace = {"verify_function": verify_function}
    exec(example["Constraint_List_code"], namespace)
    exec(example["Inputs_Check_code"],namespace)
    code_to_test = example["Traverse_code"]
    exec(code_to_test,namespace)
    import itertools
    subsets = []
    original_set = namespace['constraint_list']
    nums_len = len(original_set)
    nums_set = list(range(nums_len))
    for length in range(len(original_set)): # 不加1，去掉自己
        possible_subsets = list(itertools.combinations(nums_set, length))
        filtered_subsets = [subset for subset in possible_subsets if nums_set[-1] in subset]
        if filtered_subsets:
            subsets.append(filtered_subsets[0])
        elif length == 0:  
            subsets.append([])
    for subset in subsets:
        namespace['constraint_list'] = [original_set[i] for i in subset]
        exec(f"verify_function.reset()" + f"\ntot_calls = verify_function.calls" + f"\npara_list = verify_function.calls_args" + f"\ntrue_calls_args = verify_function.true_calls_args",namespace)
        result, total = namespace['count_valid_arrangements']()
        if len(namespace['para_list']) > 0 and len(namespace['true_calls_args']) > 0 :
            success = True
        else:
            success = False
        temp = copy.deepcopy(example)
        last_str = temp["Constraint_List_code"].split("constraint_list = ")[-1]
        sub_str = f"[{','.join(['constraint_'+str(i+1) for i in subset])}]"
        temp['Constraint_List_code'] = temp['Constraint_List_code'].replace(last_str,sub_str)
        if len(logic_constraints_list) == nums_len and subset != []:
            temp['question_dict']['logic_constraints'] = ";".join([logic_constraints_list[i] for i in subset])
            temp['question_dict']['logic_constraints_update'] = True
        elif subset == []:
            continue
            temp['question_dict']['logic_constraints'] = "无"
            temp['question_dict']['logic_constraints_update'] = True
        else:
            max_retries = 3
            cur_retries = 0
            while cur_retries < max_retries:
                try:
                    input_prompt = merge_constraints_prompt_cn.replace("[[[origin_constraints_description]]]", logic_constraints_raw).replace("[[[Constraint_List_code]]]", temp['Constraint_List_code'])
                    content = get_content(api_key, input_prompt, model_name)
                    content_json = extract_json_blocks(content)[0].strip("\n").strip()
                    content_json = json.loads(content_json)
                    temp['question_dict']['logic_constraints'] = content_json['new_constraints_description']
                    temp['question_dict']['logic_constraints_update'] = True
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    cur_retries += 1
            if cur_retries == max_retries:        
                temp['question_dict']['logic_constraints_update'] = False
            else:
                temp['question_dict']['logic_constraints_update'] = True
        temp['domain_size'] = len(namespace['para_list'])
        temp['solution_space_size'] = len(namespace['true_calls_args'])
        temp['domain_size_v2'] = total
        temp['solution_space_size_v2'] = result
        if temp['domain_size']== temp['domain_size_v2'] and temp['solution_space_size']== temp['solution_space_size_v2']:
            temp['traverse_success'] = True
        else:
            temp['traverse_success'] = False
        temp['delete_success'] = success
        save_data(temp, save_path, debug)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the new code after the delete of constrainsts and check the results!")
    parser.add_argument("--name", type=str, default="example")
    parser.add_argument("--debug", action='store_true', help="If set, runs in debug mode.")
    args = parser.parse_args()
    input_path = f"./synthesize/traverse/output_cn/{args.name}_final.jsonl"
    save_path = f"./synthesize/delete/output_cn/{args.name}_final.jsonl"

    api_key = os.getenv('OPENAI_API_KEY')
    model_name = "gpt-4o-2024-08-06" 
    model_name = 'gpt-4-turbo'
    use_cache = False
    cache_id = set()
    if use_cache:
        with open(save_path, "r") as f:
            for line in f:
                data = ast.literal_eval(line)
                cache_id.add(data['id'])
    print(f"Cache id len: {len(cache_id)}")
    with open(input_path, 'r') as f:
        datas = [ast.literal_eval(line) for line in f]
    for data in tqdm(datas) :   
        if data['id'] in cache_id and data['id'] != 140:
            continue
        try:
            main(api_key, model_name, data, save_path, args.debug)
        except Exception as e:
            print(f"Error: {e}")
            print(f"Error processing data: {data['id']}")
            continue
        


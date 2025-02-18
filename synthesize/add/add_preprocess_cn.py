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

def extract_json_blocks(markdown_text):
    pattern = re.compile(r'```json(.*?)```', re.DOTALL)
    code_blocks = pattern.findall(markdown_text)
    return code_blocks

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

def main(example, save_path, debug=False):
    logic_constraints_raw = example["question_dict"]["logic_constraints"]
    logic_constraints_list = re.split(r';|；', logic_constraints_raw)
    namespace = {"verify_function": verify_function}
    exec(example["Constraint_List_code"], namespace)
    exec(example["Inputs_Check_code"],namespace)
    code_to_test = example["Traverse_code"]
    exec(code_to_test,namespace)
    exec(f"verify_function.reset()" + f"\ntot_calls = verify_function.calls" + f"\npara_list = verify_function.calls_args" + f"\ntrue_calls_args = verify_function.true_calls_args",namespace)
    result, total = namespace['count_valid_arrangements']()
    temp = copy.deepcopy(example)
    temp['solution_space'] = [ast.literal_eval(x.split(', <function')[0]) for x in namespace['true_calls_args']]
    if(len(temp['solution_space']) >= 500):
        temp['solution_space'] = temp['solution_space'][:500]
    save_data(temp, save_path, debug)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the new code after the add of constrainsts and check the results!")
    parser.add_argument("--name", type=str, default="example")
    parser.add_argument("--debug", action='store_true', help="If set, runs in debug mode.")
    args = parser.parse_args()
    input_path = f"./synthesize/traverse/output_cn/{args.name}_final.jsonl"
    save_path = f"./synthesize/add/output_cn/{args.name}_prepocessed.jsonl"
    
    with open(input_path, 'r') as f:
        datas = [ast.literal_eval(line) for line in f]
    for data in tqdm(datas) :    
        main(data, save_path, args.debug)
        


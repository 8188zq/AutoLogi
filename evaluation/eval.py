#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
import re
import sys
import ast
from collections import defaultdict
from pathlib import Path
from typing import List
from copy import deepcopy
import dataclasses
import argparse
from tqdm import tqdm

from run_code import run_code

INVALID_VALUE = -9999999

verify_fuction_code = """def verify_function(inputs, inputs_check, constraint_list):
    # 首先检查inputs是否有效
    if not inputs_check(inputs):  # 如果输入格式不满足
            return False
    
    # 遍历constraint_list，对每个约束函数进行检查
    for constraint in constraint_list:
        if not constraint(inputs):  # 如果约束不满足
            return False
            
    # 所有约束都已检查且满足
    return True"""

@dataclasses.dataclass
class InputExample:
    idx: int
    prompt: str
    Inputs_Check_code: str
    Constraint_List_code: str
    Traverse_code: str
    lang: str
    gen: str 


def get_prompt_list(input_jsonl_filename):
    inputs = []
    with open(input_jsonl_filename, "r", encoding='utf-8') as f:
        for l in f:
            example = json.loads(l)
            inputs.append(
                InputExample(
                    idx = example["idx"],
                    prompt = example["prompt"],
                    Inputs_Check_code = example["code"]["Inputs_Check_code"],
                    Constraint_List_code = example["code"]["Constraint_List_code"],
                    Traverse_code = example["code"]["Traverse_code"],
                    lang = example["lang"],
                    gen = example["gen"][0]
                )
            )
    return inputs

def extract_code(text: str) -> str:
        code_block_pattern = re.compile(r"```(?:\s*[\w]+)?\s*\n(.*?)```", re.DOTALL)
        code_blocks = code_block_pattern.findall(text)
        
        if code_blocks:
            return code_blocks[-1]
        else:
            return None

def extract_last_dict(content):
    stack = []  
    start_idx = None  
    last_dict = None 

    for i, char in enumerate(content):
        if char == '{':
            if not stack:
                start_idx = i
            stack.append('{')
        elif char == '}':
            if stack:
                stack.pop()
                if not stack:
                    last_dict = content[start_idx:i + 1]
    return last_dict

def extract_last_list(content):
    matches = re.findall(r"\[.*?\]", content, re.DOTALL)
    if matches:
        return matches[-1]
    else:
        return None
    
def compute_coding_pass1(inp):
    result = {}
    content = inp.gen
    func_args = None
    result["extraction_failed"] = 0
    result["error"] = None
    func_args  = extract_code(content)
    if func_args is None:
        last_dict = extract_last_dict(content)
        last_list = extract_last_list(content)
        if last_dict is not None:
            func_args = last_dict
        else:
            if last_list is not None:
                func_args = last_list
            else:
                return {"acc": 0, "error": "extraction_failed", "extraction_failed": 1}
    try:
        func_args = re.sub(r'//.*?\n', '', func_args)
        params = ast.literal_eval(func_args.replace("true","True").replace("false","False"))
    except (SyntaxError, ValueError, TypeError) as e:
        if "=" in func_args:
            try:
                params_str = func_args.split("=", 1)[1].strip()
                params = ast.literal_eval(params_str)
            except (SyntaxError, ValueError, TypeError) as e:
                return {"acc": 0, "error": "extraction_failed", "extraction_failed": 1 }
        else:
            try:
                params = json.loads(func_args)
            except:
                return {"acc": 0, "error": "extraction_failed", "extraction_failed": 1}
        
    # predictions = inp.Inputs_Check_code +"\n" + inp.Constraint_List_code + "\n" + verify_fuction_code+ "\n" + f"res = verify_function({params}, inputs_check, constraint_list)" + "\nassert res == True"
    test_program = inp.Inputs_Check_code +"\n" + inp.Constraint_List_code + "\n" + verify_fuction_code+ "\n" + f"res = verify_function({params}, inputs_check, constraint_list)" +"\nprint(res)"+ "\nassert res == True"
    
    timeout = 20
    output, error = run_code(test_program, timeout)

    return {"acc": 1 if output and output.strip() in ["True","true"] else 0, "error": error, "extraction_failed": 0}

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate AutoLogi based on input data and responses."
    )
    parser.add_argument(
        "--input_data",
        type=str,
        required=True,
        help="Path to input data (jsonl format).",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=False,
        default=".results/",
        help="Output directory for inference and eval results.",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        required=False,
        default="qwen2.5-72b-instruct",
    )
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Validate output directory
    if not os.path.exists(args.output_dir):
        try:
            os.makedirs(args.output_dir)
            logging.info(f"Make output directory: {args.output_dir}")
        except Exception as e:
            logging.error(f"Failed to make output directory: {e}")
            sys.exit(1)

    # Read input data
    logging.info(f"Reading input data from {args.input_data}...")
    inputs = get_prompt_list(args.input_data)
    
    # Perform evaluations
    outputs = []
    for inp in tqdm(inputs):
        output = compute_coding_pass1(inp)
        output["idx"] = inp.idx
        outputs.append(output)
    with open(os.path.join(args.output_dir, f"{args.model_name}_eval_results.jsonl"), "w", encoding='utf-8') as f:
        num = 0
        acc = 0
        for output in outputs:
            num += 1
            if output["acc"] == 1:
                acc += 1
            f.write(json.dumps(output, ensure_ascii=False) + "\n")
            f.flush()
        if num > 0:
            score = acc / num
        else:
            score = 0
        print(f"acc: {score}")



if __name__ == "__main__":
    # python /mnt/workspace/AutoLogi/evaluation/eval.py --input_data ./model_output/qwen2.5_72b_instruct_response_example_en.jsonl --output_dir ./eval_results/
    main()
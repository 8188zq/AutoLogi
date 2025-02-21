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

from prompts.verify import Dividing_definition_constraints_prompt_cn,Dividing_definition_constraints_prompt_en
from utils.call_openai import call_openai

def save_data(data, save_path, debug=False):
    if debug:
        with open(save_path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    else:
        with open(save_path, "a") as f:
            json.dump(data, f, ensure_ascii=False)
            f.write("\n")
            f.flush()

def get_content(api_key, input_text, model_name):
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
    prompt = Dividing_definition_constraints_prompt_en
    return prompt.replace("[[[question]]]", data['question']).strip()

def remove_bracket_numbers(s):
    return re.sub(r'[\(\（]\d+[\)\）]', '', s)

def main(api_key, model_name, data, save_path, debug=False):
    data['question'] = data['question'].replace("\n\n", "\n")
    input_prompt = format_verify_prompt(data)
    input_prompt = remove_bracket_numbers(input_prompt)
    idx = data['id']
    max_retries = 3
    cur_retries = 0
    while cur_retries < max_retries:
        try:
            content = get_content(api_key, input_prompt, model_name)
            with open("./synthesize/verify/debug/raw_content_log.json", "w") as f:
                f.write(content+"\n"+"*"*50+"\n")
                f.flush()
            json_content = extract_json_blocks(content)
            assert len(json_content) >=1 , f"json blocks not found!"
            json_content = json_content[0].strip("\n").strip()
            content_dict = json.loads(json_content)
            data['question_dict'] = content_dict  
            break
        except Exception as e:
            print(f"Error: {e}")
            cur_retries += 1
    if cur_retries == max_retries:
        with open("./synthesize/verify/debug/failed_idx.txt", "a") as f:
            f.write(f"{idx}\n")
        print(f"Failed to get content for input_idx: {idx}")
        return
    else:
        if debug:
            print(f"{data}\n")
            return
        save_data(data, save_path, debug)
        # print(f"Parsed content: {parsed_content}\n")
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the best verify code and get the results!")
    parser.add_argument("--debug", action='store_true', help="If set, runs in debug mode.")
    parser.add_argument("--name", type=str, default="example")

    args = parser.parse_args()
    input_path = f"./training-data/{args.name}.jsonl"
    save_path = f"./synthesize/verify/output_en/{args.name}.jsonl"
    api_key = os.getenv("OPENAI_API_KEY")
    model_name = "gpt-4o-2024-08-06" 
    # model_name = "gpt-4-0613"
    cache_id = []
    use_cache = False
    with open(input_path, 'r') as f:
        datas = [json.loads(line) for line in f]
    for data in tqdm(datas) :
        if data['id'] in cache_id:
            continue
        main(api_key, model_name, data, save_path, args.debug)
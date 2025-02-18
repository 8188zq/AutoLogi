import json
import ast
import re
import itertools
import argparse

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="depulicate the output of convert to the final format.")
    parser.add_argument("--name", type=str, default="example")
    parser.add_argument("--debug", action='store_true', help="If set, runs in debug mode.")
    args = parser.parse_args()
    input_path = f"./synthesize/convert/output_en/{args.name}_final.jsonl"
    output_path = f"./synthesize/convert/output_en/{args.name}_final_deduplicated.jsonl"


    with open(input_path, 'r') as f:
        datas = [ast.literal_eval(line) for line in f]

    datas.sort(key=lambda data: data['id'])

    new_datas = []
    def deduplicate_by_question(dict_list):
        seen_questions = set()
        deduplicated_list = []
        for d in dict_list:
            question = d.get("prompt")
            if question not in seen_questions:
                seen_questions.add(question)
                deduplicated_list.append(d)
        return deduplicated_list

    new_datas = deduplicate_by_question(datas)

    for data in new_datas:
        save_data(data, output_path)
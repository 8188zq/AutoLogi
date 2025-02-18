import ast
import argparse
import json

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

def main(input_path, save_path):
    with open(input_path, "r") as f:
        for line in f:
            data = ast.literal_eval(line)
            if data.get("solution_space_size_v2",0) !=0:
                save_data(data,save_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the best traverse code and get the results!")
    parser.add_argument("--debug", action='store_true', help="If set, runs in debug mode.")
    parser.add_argument("--name", type=str, default="example")
    parser.add_argument("--max_verify_time", type=int, default=2)
    parser.add_argument("--max_traverse_time", type=int, default=3)

    args = parser.parse_args()
    input_path = f"./synthesize/traverse/output_en/{args.name}_v{args.max_verify_time}.{args.max_traverse_time}.jsonl"
    save_path = f"./synthesize/traverse/output_en/{args.name}_final.jsonl"
    main(input_path, save_path)
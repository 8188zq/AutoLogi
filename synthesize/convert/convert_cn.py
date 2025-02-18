import json
import ast
import re
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

def question_convert(background,logic_constraints):
    constraints_list = re.split(r';|；', logic_constraints)
    question = background + "\n\n" + "请你生成一个安排方案满足以下约束： "
    if constraints_list[-1] == "无":
        question += "无"
    else:
        for i in range(len(constraints_list)):
            question += f"({i+1}) {constraints_list[i]} "
    return question

def prompt_convert(question,input_format,example):
    prompt = """[[[input_text]]]
    
请你一步一步思考，你的安排方案必须按照为以下输入格式要求来进行回答：
[[[input_format]]]
下面提供一个输入样例（注意这只是一个合法输入的例子，不一定是正确方案）：
```json
[[[example]]]
```"""
    input_format = input_format.replace("`inputs`","inputs",1)
    input_format = input_format.replace("inputs","在回答的最后，你需要给出一个输入，以表示你的最终安排方案, 其中 inputs",1)
    return prompt.replace("[[[input_text]]]", question).replace("[[[input_format]]]", input_format).replace("[[[example]]]", example)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert the output of add and delete to the final format.")
    parser.add_argument("--name", type=str, default="example")
    parser.add_argument("--debug", action='store_true', help="If set, runs in debug mode.")
    args = parser.parse_args()
    delete_path = f"./synthesize/delete/output_cn/{args.name}_final.jsonl"
    add_path = f"./synthesize/add/output_cn/{args.name}_final.jsonl"
    output_path = f"./synthesize/convert/output_cn/{args.name}_final.jsonl"


    datas = []
    with open(delete_path, 'r') as f:
        delete_datas = [ast.literal_eval(line) for line in f]
        for data in delete_datas:
            temp = {}
            question = question_convert(data['question_dict']['background'], data['question_dict']['logic_constraints'])
            input_format = data['Inputs_Format']
            example = repr(data['Inputs_Example'])
            code = {
                "Inputs_Check_code": data["Inputs_Check_code"],
                "Constraint_List_code": data["Constraint_List_code"],
                "Traverse_code": data["Traverse_code"],
            }
            prompt = prompt_convert(question,input_format,example)
            temp["prompt"] = prompt
            temp["question"] = question
            temp["logi_constraints"] = data['question_dict']['logic_constraints']
            temp["input_format"] = input_format
            temp["example"] = example
            temp["code"] = code
            temp["id"] = data["id"]
            temp["lang"] = "zh_cn"
            datas.append(temp)
            
    with open(add_path, 'r') as f:
        add_datas = [ast.literal_eval(line) for line in f]
        for data in add_datas:
            temp = {}
            question = question_convert(data['question_dict']['background'], data['question_dict']['logic_constraints'])
            input_format = data['Inputs_Format']
            example = repr(data['Inputs_Example'])
            code = {
                "Inputs_Check_code": data["Inputs_Check_code"],
                "Constraint_List_code": data["Constraint_List_code"],
                "Traverse_code": data["Traverse_code"],
            }
            prompt = prompt_convert(question,input_format,example)
            temp["prompt"] = prompt
            temp["question"] = question
            temp["logi_constraints"] = data['question_dict']['logic_constraints']
            temp["input_format"] = input_format
            temp["example"] = example
            temp["code"] = code
            temp["turn"] = data["turn"]
            temp["id"] = data["id"]
            temp["lang"] = "zh_cn"
            datas.append(temp)

    with open(output_path, 'w') as f:
        for data in datas:
            save_data(data, output_path, debug=False)

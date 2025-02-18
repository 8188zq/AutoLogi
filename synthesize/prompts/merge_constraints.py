merge_constraints_prompt_cn = """下面会先给出包含若干个constraint_i的函数，以及constrainst_list = [...],其中constrainst_list内的内容是实际上有用的constraint，
你需要归纳并出“实际上用到的”constraints文字要求，要求间用‘；’分割，即归纳且仅归纳constrainst_list内的constraint_i的函数。
例子：
Input:
{
"origin_constraints_description": "扶夷站在灏韵站之东、胡瑶站之西，并与胡瑶站相邻；韮上站与银岭站相邻；韮上站与灏韵站相邻并且在灏韵站之东。",
"code": "def constraint_1(inputs):\n    if inputs.index(\"扶夷站\") < inputs.index(\"灏韵站\"):\n        return False\n    return True\n\ndef constraint_2(inputs):\n    if inputs.index(\"扶夷站\") > inputs.index(\"胡瑶站\") or abs(inputs.index(\"扶夷站\") - inputs.index(\"胡瑶站\")) != 1:\n        return False\n    return True\n\ndef constraint_3(inputs):\n    if abs(inputs.index(\"韮上站\") - inputs.index(\"银岭站\")) != 1:\n        return False\n    return True\n\ndef constraint_4(inputs):\n    if abs(inputs.index(\"韮上站\") - inputs.index(\"灏韵站\")) != 1 or inputs.index(\"韮上站\") < inputs.index(\"灏韵站\"):\n        return False\n    return True\n\nconstraint_list = [constraint_1,constraint_4]",
}
Output:
```json
{
"new_constraints_description": "扶夷站在灏韵站之东；韮上站与灏韵站相邻并且在灏韵站之东。"
}
```
下面你来做：
Input:
{
"origin_constraints_description": "[[[origin_constraints_description]]]",
"code": "[[[Constraint_List_code]]]",
}
Output:
"""

merge_constraints_prompt_en = """Below, a function containing several constraint_i will be given, along with constrainst_list = [...], where the contents of constrainst_list are the actually useful constraints.
You need to summarize and output the "actually used" constraints text requirements, separated by ';', that is, summarize and only summarize the constraint_i function in constrainst_list.
Example:
Input:
{
"origin_constraints_description": "Fuyi Station is east of Haoyun Station and west of Huyao Station, and is adjacent to Huyao Station; Jiu Shang Station is adjacent to Yinling Station; Jiu Shang Station is adjacent to Haoyun Station and is east of Haoyun Station.",
"code": "def constraint_1(inputs):\n    if inputs.index(\"Fuyi Station\") < inputs.index(\"Haoyun Station\"):\n        return False\n    return True\n\ndef constraint_2(inputs):\n    if inputs.index(\"Fuyi Station\") > inputs.index(\"Huyao Station\") or abs(inputs.index(\"Fuyi Station\") - inputs.index(\"Huyao Station\")) != 1:\n        return False\n    return True\n\ndef constraint_3(inputs):\n    if abs(inputs.index(\"Jiu Shang Station\") - inputs.index(\"Yinling Station\")) != 1:\n        return False\n    return True\n\ndef constraint_4(inputs):\n    if abs(inputs.index(\"Jiu Shang Station\") - inputs.index(\"Haoyun Station\")) != 1 or inputs.index(\"Jiu Shang Station\") < inputs.index(\"Haoyun Station\"):\n        return False\n    return True\n\nconstraint_list = [constraint_1,constraint_4]",
}
Output:
```json
{
"new_constraints_description": "Fuyi Station is east of Haoyun Station; Jiu Shang Station is adjacent to Haoyun Station and is east of Haoyun Station."
}
```
Now it's your turn:
Input:
{
"origin_constraints_description": "[[[origin_constraints_description]]]",
"code": "[[[Constraint_List_code]]]",
}
Output:
"""
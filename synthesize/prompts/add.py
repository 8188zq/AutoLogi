find_new_constraints_prompt_en = """The following will provide 1. A logical reasoning question, including some descriptions required by logic_constraint 2. All solutions that satisfy all constraints, as well as descriptions of these solution formats. 3. The verification function code corresponding to these constraints
You need to use this information to 1. Find a new, stricter constraint (which must exclude some solutions), and also require that there are solutions that can satisfy this new constraint among the provided solutions (the number of new constraints must be 1). 2. And update the corresponding verification function code so that this new constraint can be checked by the verification function.
An example (please refer to the example for the format of the title and code block in the Output):
Input:
{
"background": "A supermarket is neatly arranged with 7 rows of shelves from front to back, placing 7 types of goods: stationery, snacks, condiments, daily necessities, wine, grain and oil, and beverages, each type of goods occupies one row.",
"logic_constraints": "The wine is in front of the condiments; there are 3 rows between the stationery and the condiments; the grain and oil is after the snacks, with 2 rows in between; the daily necessities are either in front of or behind the stationery.",
"solution_space": [
    "['Stationery', 'Daily necessities', 'Snacks', 'Wine', 'Condiments', 'Grain and oil', 'Beverages']",
    "['Stationery', 'Daily necessities', 'Wine', 'Snacks', 'Condiments', 'Beverages', 'Grain and oil']",
    "['Snacks', 'Stationery', 'Daily necessities', 'Grain and oil', 'Wine', 'Condiments', 'Beverages']",
    "['Snacks', 'Daily necessities', 'Stationery', 'Grain and oil', 'Wine', 'Beverages', 'Condiments']",
    "['Snacks', 'Daily necessities', 'Stationery', 'Grain and oil', 'Beverages', 'Wine', 'Condiments']",
    "['Snacks', 'Wine', 'Condiments', 'Grain and oil', 'Beverages', 'Daily necessities', 'Stationery']",
    "['Daily necessities', 'Stationery', 'Wine', 'Snacks', 'Beverages', 'Condiments', 'Grain and oil']",
    "['Daily necessities', 'Stationery', 'Beverages', 'Snacks', 'Wine', 'Condiments', 'Grain and oil']",
    "['Wine', 'Stationery', 'Daily necessities', 'Snacks', 'Beverages', 'Condiments', 'Grain and oil']",
    "['Wine', 'Snacks', 'Stationery', 'Daily necessities', 'Grain and oil', 'Beverages', 'Condiments']",
    "['Wine', 'Snacks', 'Condiments', 'Beverages', 'Grain and oil', 'Daily necessities', 'Stationery']",
    "['Wine', 'Condiments', 'Beverages', 'Snacks', 'Daily necessities', 'Stationery', 'Grain and oil']",
    "['Beverages', 'Stationery', 'Daily necessities', 'Snacks', 'Wine', 'Condiments', 'Grain and oil']",
    "['Beverages', 'Snacks', 'Stationery', 'Daily necessities', 'Grain and oil', 'Wine', 'Condiments']"
  ],
"Constraint_List_code": "def constraint_1(inputs):\n    if inputs.index(\"Wine\") >= inputs.index(\"Condiments\"):\n        return False\n    return True\n\ndef constraint_2(inputs):\n    if abs(inputs.index(\"Stationery\") - inputs.index(\"Condiments\")) != 4:\n        return False\n    return True\n\ndef constraint_3(inputs):\n    if inputs.index(\"Grain and oil\") <= inputs.index(\"Snacks\") or inputs.index(\"Grain and oil\") - inputs.index(\"Snacks\") != 3:\n        return False\n    return True\n\ndef constraint_4(inputs):\n    if abs(inputs.index(\"Daily necessities\") - inputs.index(\"Stationery\")) != 1:\n        return False\n    return True\n\nconstraint_list = [constraint_1, constraint_2, constraint_3, constraint_4]",
}
Output:
### Analysis
By observing the provided solutions, we can summarize some unique features of some solutions in this solution space, and then based on these features, we can find new stricter constraints, while still having solutions that can satisfy after adding new constraints.

### Constraints
xxx
```json
{
"new_constraints": "Beverages cannot be placed in the first and last rows",
}
```

### Code
```python
def constraint_1(inputs):
    if inputs.index("Wine") >= inputs.index("Condiments"):
        return False
    return True
            
def constraint_2(inputs):
    if abs(inputs.index("Stationery") - inputs.index("Condiments")) != 4:
        return False
    return True
    
def constraint_3(inputs):
    if inputs.index("Grain and oil") <= inputs.index("Snacks") or inputs.index("Grain and oil") - inputs.index("Snacks") != 3:
        return False
    return True
    
def constraint_4(inputs):
    if abs(inputs.index("Daily necessities") - inputs.index("Stationery")) != 1:
        return False
    return True
    
def constraint_5(inputs):
    # Beverages cannot be placed in the first and last rows
    if inputs.index("Beverages") == 0 or inputs.index("Beverages") == len(inputs) - 1:
        return False
    return True

constraint_list = [constraint_1, constraint_2, constraint_3, constraint_4, constraint_5]
```
Now it's your turn:
Input:
{
"background": "[[[background]]]",
"logic_constraints": "[[[logic_constraints]]]",
"solution_space": [[[solution_space]]],
"Constraint_List_code": "[[[Constraint_List_code]]]",    
}
Output:"""

find_new_constraints_prompt_cn = """下面会提供1、一道逻辑推理题，包含一些logic_constraint要求的描述 2、满足所有constraint的所有解，以及对这些解格式的描述。 3、对应这些constraint的验证函数代码
你需要根据这些信息，1、找到一个新的更严格的constraint(必须排除掉一些解)，同时还要求提供的这些解存在能满足这个新的constraint的解（新constraint个数必须是1个）。 2、并更新对应的验证函数代码，使得这个新的constraint能够被验证函数检查到。
一个例子(Output中标题和代码块的格式请参照例子)：
Input:
{
"background": "某超市从前到后整齐排列着7排货架，放置着文具、零食、调料、日用品、酒、粮油和饮料7类商品，每类商品占据一排。",
"logic_constraints": "酒类排在调料类之前；文具类和调料类中间隔着3排；粮油类在零食类之后，中间隔着2排；日用品类紧挨在文具类前一排或者后一排。",
"solution_space": [
    "['文具', '日用品', '零食', '酒', '调料', '粮油', '饮料']",
    "['文具', '日用品', '酒', '零食', '调料', '饮料', '粮油']",
    "['零食', '文具', '日用品', '粮油', '酒', '调料', '饮料']",
    "['零食', '日用品', '文具', '粮油', '酒', '饮料', '调料']",
    "['零食', '日用品', '文具', '粮油', '饮料', '酒', '调料']",
    "['零食', '酒', '调料', '粮油', '饮料', '日用品', '文具']",
    "['日用品', '文具', '酒', '零食', '饮料', '调料', '粮油']",
    "['日用品', '文具', '饮料', '零食', '酒', '调料', '粮油']",
    "['酒', '文具', '日用品', '零食', '饮料', '调料', '粮油']",
    "['酒', '零食', '文具', '日用品', '粮油', '饮料', '调料']",
    "['酒', '零食', '调料', '饮料', '粮油', '日用品', '文具']",
    "['酒', '调料', '饮料', '零食', '日用品', '文具', '粮油']",
    "['饮料', '文具', '日用品', '零食', '酒', '调料', '粮油']",
    "['饮料', '零食', '文具', '日用品', '粮油', '酒', '调料']"
  ],
"Constraint_List_code": "def constraint_1(inputs):\n    if inputs.index(\"酒\") >= inputs.index(\"调料\"):\n        return False\n    return True\n\ndef constraint_2(inputs):\n    if abs(inputs.index(\"文具\") - inputs.index(\"调料\")) != 4:\n        return False\n    return True\n\ndef constraint_3(inputs):\n    if inputs.index(\"粮油\") <= inputs.index(\"零食\") or inputs.index(\"粮油\") - inputs.index(\"零食\") != 3:\n        return False\n    return True\n\ndef constraint_4(inputs):\n    if abs(inputs.index(\"日用品\") - inputs.index(\"文具\")) != 1:\n        return False\n    return True\n\nconstraint_list = [constraint_1, constraint_2, constraint_3, constraint_4]",
}
Output:
### Analysis
观察提供的解决方案，我们可以归纳出这些solution space中的一些解的独有的特点，然后根据这些特点，我们就可以找到新的更严格的约束条件，同时使新增约束条件后也仍有解能满足。

### Constraints
xxx
```json
{
"new_constraints": "饮料类不能排在第一排和最后一排",
}
```

### Code
```python
def constraint_1(inputs):
    if inputs.index("酒") >= inputs.index("调料"):
        return False
    return True
            
def constraint_2(inputs):
    if abs(inputs.index("文具") - inputs.index("调料")) != 4:
        return False
    return True
    
def constraint_3(inputs):
    if inputs.index("粮油") <= inputs.index("零食") or inputs.index("粮油") - inputs.index("零食") != 3:
        return False
    return True
    
def constraint_4(inputs):
    if abs(inputs.index("日用品") - inputs.index("文具")) != 1:
        return False
    return True
    
def constraint_5(inputs):
    # 饮料类不能排在第一排和最后一排
    if inputs.index("饮料") == 0 or inputs.index("饮料") == len(inputs) - 1:
        return False
    return True

constraint_list = [constraint_1, constraint_2, constraint_3, constraint_4, constraint_5]
```
下面你来做：
Input:
{
"background": "[[[background]]]",
"logic_constraints": "[[[logic_constraints]]]",
"solution_space": [[[solution_space]]],
"Constraint_List_code": "[[[Constraint_List_code]]]",    
}
Output:
"""
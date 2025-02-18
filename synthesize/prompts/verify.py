Dividing_definition_constraints_prompt_cn = """提供一个问题的描述，这个描述中有一些是问题的背景以及定义(一般就是开头一两句)，也有一些是逻辑的限制条件，你需要把这两部分划分出来，可以自己重新组织语言，但不要改变原题意。
Input:
"某超市从前到后整齐排列着7排货架，放置着文具、零食、调料、日用品、酒、粮油和饮料7类商品，每类商品\n占据一排。已知：\n酒类排在调料类之前；\n文具类和调料类中间隔着3排；\n粮油类在零食类之后，中间隔着2排；\n日用品类紧挨在文具类前一排或者后一排。\n零食类排在第1排"
Output:
```json
{
    "background": "某超市从前到后整齐排列着7排货架，放置着文具、零食、调料、日用品、酒、粮油和饮料7类商品，每类商品占据一排。",
    "logic_constraints": "酒类排在调料类之前；文具类和调料类中间隔着3排；粮油类在零食类之后，中间隔着2排；日用品类紧挨在文具类前一排或者后一排；零食类排在第1排。"
}
```
Input:
[[[question]]]
Output:
"""

Dividing_definition_constraints_prompt_en = """Provide a description of a problem, which contains some background and definition of the problem (usually the first one or two sentences), as well as some logical constraints. You need to divide these two parts, you can reorganize the language, but do not change the original meaning of the problem.
Input:
"A supermarket is neatly arranged with 7 rows of shelves from front to back, displaying 7 categories of goods: stationery, snacks, condiments, daily necessities, alcohol, grains and oils, and beverages, each occupying one row. It is known that: \nThe alcohol is placed before the condiments; \nThere are 3 rows between the stationery and the condiments; \nThe grains and oils are after the snacks, with 2 rows in between; \nThe daily necessities are either in the row before or after the stationery; \nThe snacks are in the first row."
Output:
```json
{
    "background": "A supermarket is neatly arranged with 7 rows of shelves from front to back, displaying 7 categories of goods: stationery, snacks, condiments, daily necessities, alcohol, grains and oils, and beverages, each occupying one row.",
    "logic_constraints": "The alcohol is placed before the condiments; There are 3 rows between the stationery and the condiments; The grains and oils are after the snacks, with 2 rows in between; The daily necessities are either in the row before or after the stationery; The snacks are in the first row."
}
```
Input:
[[[question]]]
Output:"""

build_verify_function_prompt_en = """The Input describes a problem in a real-life scenario along with some logical constraints. There may be several solutions that satisfy all the above constraints. The goal is to determine whether a particular solution meets all the conditions of the problem.
The approach is to first analyze, then define the inputs (a dict) to represent any possible solution to be verified based on the background and definitions. Therefore, you need to provide the specification of the inputs and an example. Note that the definition of the inputs should be based on the background and definitions, not on the logical constraints. Do not include the logical constraints in the specification! Also, if the order of the elements does not affect the result, prefer to use a set, but if the elements may be repeated or the order affects the result, prefer to use a list. Then write an 'inputs_check' function to verify the validity of the inputs; then extract all the logical constraints of the problem and convert them into corresponding constraint functions. You need to provide a constraint_list, which contains all the extracted constraint functions, to ensure that it does not repeat with the judgment of inputs_check; finally, form the final verify_function, this function is as follows:
```python
def verify_function(inputs, inputs_check, constraint_list):
    # First check if the inputs are valid
    if not inputs_check(inputs):  # If the input format is not satisfied
            return False
    
    # Traverse the constraint_list and check each constraint function
    for constraint in constraint_list:
        if not constraint(inputs):  # If the constraint is not satisfied
            return False
            
    # All constraints have been checked and satisfied
    return True
```
Here is an example:
Input:
Background and definition: A class plans to select two girls from Emily, Sophia, and Olivia, and three boys from James, Michael, William, David, and Robert to form a five-person college student teaching team for voluntary teaching in the mountains.
Logical constraints: (1) Sophia and Robert cannot be selected at the same time; (2) James and Song Kaiwen cannot be selected at the same time; (3) Michael and Robert cannot be selected at the same time.
Output:
### Analysis
First, we need to define the format of inputs based on the content of the background and definitions, and it cannot include logical constraints. We can design inputs as a dictionary, which includes two keys: "female" and "male", corresponding to the selected girls and boys list. Check it, it does not include the content of logical constraints! Elements are not repeated and the order does not matter, so use a set.

### Inputs_Format
Inputs is a dictionary, containing two keys: "female" and "male".
inputs["female"] is a set containing 2 elements, including the names of the selected girls (strings). The value range is ["Emily", "Sophia", "Olivia"].
inputs["male"] is a set containing 3 elements, including the names of the selected boys (strings). The value range is ["James", "Michael", "William", "David", "Robert"].

### Inputs_Example
```python
{
    "female": {"Emily", "Sophia"},
    "male": {"James", "Michael", "William"}
}
```

### Inputs_Check_Function
```python
def inputs_check(inputs):
    # Check if inputs is a dictionary
    if not isinstance(inputs, dict):
        return False
    # Check if inputs contains "female" and "male" two keys
    if "female" not in inputs or "male" not in inputs:
        return False
    # Check if the values corresponding to "female" and "male" are sets
    if not isinstance(inputs["female"], set) or not isinstance(inputs["male"], set):
        return False
    # Check if the sets corresponding to "female" and "male" contain the correct number of elements
    if len(inputs["female"]) != 2 or len(inputs["male"]) != 3:
        return False
    # Check if the elements of the sets corresponding to "female" and "male" are correct
    if not inputs["female"].issubset({"Emily", "Sophia", "Olivia"}) or not inputs["male"].issubset({"James", "Michael", "William", "David", "Robert"}):
        return False
    return True
```

### Constraint_List
Create three constraint functions below to meet the requirements in the problem description:

Sophia and Robert cannot be selected at the same time;
James and David cannot be selected at the same time;
Michael and Robert cannot be selected at the same time.

```python
def constraint_1(inputs):
    if "Sophia" in inputs["female"] and "Robert" in inputs["male"]:
        return False
    return True

def constraint_2(inputs):
    if "James" in inputs["male"] and "David" in inputs["male"]:
        return False
    return True

def constraint_3(inputs):
    if "Michael" in inputs["male"] and "Robert" in inputs["male"]:
        return False
    return True

constraint_list = [constraint_1, constraint_2, constraint_3]
```
Now it's your turn:
Input:
Background and Definitions: [[[background]]]
Logical Constraints: [[[logic_constraints]]]
Output:"""

build_verify_function_prompt_cn = """Input中描述了一个实际场景中的问题以及一些逻辑限制，可能会存在若干满足所有上述限制的方案。目标是判断某一个方案是否满足题意的所有条件。
做法是首先进行分析，然后根据背景和定义的内容来规定用inputs（一个dict）来代表任一可能的待验证方案，因此你需要给出inputs的规范，和一个示例，注意，这个inputs的定义应该基于背景和定义，而不是基于逻辑限制条件，不要把逻辑限制条件加入规范！此外如果元素顺序不影响结果优先使用set，但如果元素可能重复或者顺序影响结果优先使用list。；接着写一个'inputs_check'函数来验证inputs的合法性；然后提取出问题的所有逻辑限制转换成对应的约束函数，你需要给出一个constraint_list,这个列表中包含提取出的所有约束函数，确保不会和inputs_check的判断重复；最后组成最后的verify_fuction,这个函数完成如下：
```python
def verify_function(inputs, inputs_check, constraint_list):
    # 首先检查inputs是否有效
    if not inputs_check(inputs):  # 如果输入格式不满足
            return False
    
    # 遍历constraint_list，对每个约束函数进行检查
    for constraint in constraint_list:
        if not constraint(inputs):  # 如果约束不满足
            return False
            
    # 所有约束都已检查且满足
    return True
```
这是一个例子：
Input:
背景和定义：某班打算从方如芬、郭嫣然、何之莲三名女生中选拔两人，从彭友文、裘志节、任向阳、宋文凯、唐晓华五名男生中选拔三人组成大学生五人支教小组到山区义务支教。
逻辑限制条件：（1）郭嫣然和唐晓华不可以同时入选；（2）彭友文和宋凯文不可以同时入选；（3）裘志节和唐晓华不可以同时入选。

Output:
### Analysis
首先，我们需要根据背景和定义的内容去定义inputs的格式，并且不能包含逻辑限制条件，我们可以把inputs设计为一个字典，其中包含两个键："female"和"male"，它们分别对应选中的女生和男生名单。检查一下，确实没包含逻辑限制条件的内容！元素不重复且顺序无影响，所以使用set。

### Inputs_Format
inputs是一个字典，包含两个键："female"和"male"。
inputs["female"]是一个包含2个元素的set，包含选中的女生名字（字符串）。取值范围是["方如芬","郭嫣然","何之莲"]。
inputs["male"]是一个包含3个元素的set，包含选中的男生名字（字符串）。取值范围是["彭友文","裘志节","任向阳","宋文凯","唐晓华"]。

### Inputs_Example
```python
{
    "female": {"方如芬", "郭嫣然"},
    "male": {"彭友文", "裘志节", "任向阳"}
}
```

### Inputs_Check_Function
```python
def inputs_check(inputs):
    # 检查inputs是否为字典
    if not isinstance(inputs, dict):
        return False
    # 检查inputs是否包含"female"和"male"两个键
    if "female" not in inputs or "male" not in inputs:
        return False
    # 检查"female"和"male"对应的值是否为set
    if not isinstance(inputs["female"], set) or not isinstance(inputs["male"], set):
        return False
    # 检查"female"和"male"对应的set是否包含正确数量的元素
    if len(inputs["female"]) != 2 or len(inputs["male"]) != 3:
        return False
    # 检查"female"和"male"对应的set的元素是否正确
    if not inputs["female"].issubset({"方如芬", "郭嫣然", "何之莲"}) or not inputs["male"].issubset({"彭友文", "裘志节", "任向阳", "宋文凯", "唐晓华"}):
        return False
    return True
```

### Constraint_List
下面创建三个约束函数，用来满足问题描述中的要求：

郭嫣然和唐晓华不同时入选；
彭友文和宋文凯不同时入选；
裘志节和唐晓华不同时入选。

```python
def constraint_1(inputs):
    if "郭嫣然" in inputs["female"] and "唐晓华" in inputs["male"]:
        return False
    return True

def constraint_2(inputs):
    if "彭友文" in inputs["male"] and "宋文凯" in inputs["male"]:
        return False
    return True

def constraint_3(inputs):
    if "裘志节" in inputs["male"] and "唐晓华" in inputs["male"]:
        return False
    return True

constraint_list = [constraint_1, constraint_2, constraint_3]
```
下面你来完成：
Input:
背景和定义：[[[background]]]
逻辑限制条件：[[[logic_constraints]]]
Output:"""

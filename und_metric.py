import os
import json
import re
import math
import statistics
import numpy as np
import openai
from openai import OpenAI
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def read_json_file(file_path):
    """
    Reads a JSON file and returns the parsed data as a Python object.

    :param file_path: The path to the JSON file
    :return: The data parsed from the JSON file
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def save_json_file(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return data

def clean_string(s: str) -> str:
    """
    Remove all non-alphanumeric characters from the input string,
    including punctuation, whitespace, and escape characters.

    :param s: The original string.
    :return: A new string containing only letters and digits.
    """
    # Replace any character that is NOT a letter or digit with ''
    return re.sub(r'[^A-Za-z0-9]+', '', s)

def word_level_ac(texts, response, window_size: int = 5, step: int = 5):
    if isinstance(texts, list):
        gt = ""
        for item in texts:
            gt += clean_string(item)
    if isinstance(texts, str):
        gt = clean_string(texts)

    if isinstance(response, list):
        ocr = ""
        for item in response:
            ocr += clean_string(item)
    if isinstance(response, str):
        ocr = clean_string(response)

    results = []
    n = len(gt)
    for i in range(0, n - window_size + 1, step):
        substr = gt[i: i + window_size]
        found = substr in ocr
        # print(found)
        results.append(found)
    if not results:
        print(0.0)
        return 0.0

    ac = sum(results) / len(results)
    # print(ac)
    return ac

def logo_ocr_ac(texts, response):
    if isinstance(texts, list):
        gt = ""
        for item in texts:
            gt += clean_string(item)
    if isinstance(texts, str):
        gt = clean_string(texts)

    if isinstance(response, list):
        ocr = ""
        for item in response:
            ocr += clean_string(item)
    if isinstance(response, str):
        ocr = clean_string(response)

    lower_gt = gt.lower()
    lower_ocr = ocr.lower()

    if lower_gt==lower_ocr:
        return 1
    else:
        return 0

def real_poster_ac(texts, response, word_mode = False):
    if isinstance(texts, list):
        gt = []
        for item in texts:
            gt.append(clean_string(item).lower())
    if isinstance(texts, str):
        gt = [clean_string(texts).lower()]

    if isinstance(response, list):
        ocr = ""
        for item in response:
            ocr += clean_string(item).lower()
    if isinstance(response, str):
        ocr = clean_string(response).lower()

    if word_mode == False:
        results = []
        for i in range(0,len(gt)):
            substr = gt[i]
            if substr in ocr:
                found = 1
                results.append(found)
            else:
                found = 0
                results.append(found)

        ac = sum(results)/len(results)

    if word_mode==True:
        ac = word_level_ac(gt, ocr)

    return ac

def font_matching_ac(options, response):
    if isinstance(options, list):
        gt = ""
        for item in options:
            gt += (clean_string(item))
    if isinstance(options, str):
        gt = clean_string(options)

    if isinstance(response, list):
        answer = ""
        for item in response:
            answer += clean_string(item)
    if isinstance(response, str):
        answer = clean_string(response)

    if len(answer) > 20:
        return 0

    if gt in answer:
        return 1
    else:
        return 0

def font_attr_ac(options, response):
    if isinstance(options, list):
        gt = ""
        for item in options:
            gt += (clean_string(item))
    if isinstance(options, str):
        gt = clean_string(options)

    if isinstance(response, list):
        answer = ""
        for item in response:
            answer += clean_string(item)
    if isinstance(response, str):
        answer = clean_string(response)

    # if len(answer)>20:
    #     return 0

    if gt in answer:
        return 1
    else:
        return 0

def font_effect_ac(options, response):
    if isinstance(options, list):
        gt = ""
        for item in options:
            gt += (clean_string(item))
    if isinstance(options, str):
        gt = clean_string(options)

    if isinstance(response, list):
        answer = ""
        for item in response:
            answer += clean_string(item)
    if isinstance(response, str):
        answer = clean_string(response)

    # if len(answer)>20:
    #     return 0

    if gt in answer:
        return 1
    else:
        return 0

def font_effect_2_ac(options: list, response):
    if isinstance(response, list):
        answer = ""
        for item in response:
            answer += clean_string(item)
    if isinstance(response, str):
        answer = clean_string(response)

    if options[0] in answer:
        color_ac = 1
    else:
        color_ac = 0

    result = []
    for i in range(1,len(options)):
        found = options[i] in answer
        result.append(found)
    if len(result)==0:
        return color_ac, None
    effect_ac = sum(result)/len(result)
    # if len(answer)>20:
    #     return 0

    return color_ac, effect_ac

def layout_comparison_ac(gt, response):
    if isinstance(response, list):
        answer = ""
        for item in response:
            answer += clean_string(item)
    if isinstance(response, str):
        answer = clean_string(response)
    answer = answer[0]
    if gt in answer:
        return 1
    else:
        return 0

def extract_numbers_float(s):

    numbers = []
    for num_str in re.findall(r'\d+\.\d+|\d+', s):  # match floats or integers
        if '.' in num_str:
            numbers.append(float(num_str))
        else:
            numbers.append(int(num_str))
    return numbers

def extract_numbers_float2(s):
    """Extract all floating-point numbers from a string, ignoring integers."""
    numbers = []
    for num_str in re.findall(r'\d+\.\d+', s):  # only match floats (must contain a decimal point)
        numbers.append(float(num_str))
    return numbers

def group_numbers_into_fours(num_list):
    """
    Group a list of numbers into fours and verify that the total length is a multiple of 4.

    Args:
    num_list -- A list of numbers, e.g., [1,2,3,4,5,6,7,8]

    Returns:
    A 2D list after grouping, e.g., [[1,2,3,4], [5,6,7,8]]

    Exceptions:
    ValueError -- Raised when the input list length is not a multiple of 4
    """
    n = len(num_list)

    # verify that the length is a multiple of 4
    # if n % 4 != 0:
    #     raise ValueError(f"Number of elements {n} is not a multiple of 4, cannot group completely")

    # Slice the list with a step of 4
    result = [num_list[i:i + 4] for i in range(0, n-3, 4)]
    return result

def clean_string_for_box(input_str):
    # Regex match: keep brackets [], numbers, spaces, and commas
    return re.sub(r'[^\[\], .\d]', '', input_str)

def parse_bbox_string(bbox_str):

    """
    """
    try:
        # Use literal_eval to parse the string into a Python object
        bbox_str = clean_string_for_box(bbox_str)
        bbox_nums = extract_numbers_float2(bbox_str)
        bboxes = group_numbers_into_fours(bbox_nums)
        # bboxes = ast.literal_eval(bbox_str)
        return bboxes
    except Exception as e:
        print("Error parsing bbox string:", e)
        return []

def calculate_iou(box1, box2):
    """
    """

    # Parse coordinates
    # print("box 1",box1)
    # print("box 2",box2)
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2

    # Calculate intersection region coordinates
    x_left = max(x1_1, x1_2)
    y_top = max(y1_1, y1_2)
    x_right = min(x2_1, x2_2)
    y_bottom = min(y2_1, y2_2)

    if x1_1 > x2_1: return 0.0
    if y1_1 > y2_1: return 0.0

    if x1_2 > x2_2: return 0.0
    if y1_2 > y2_2: return 0.0

    # Handle cases with no intersection
    if x_right < x_left or y_bottom < y_top:
        return 0.0

    # Calculate intersection area
    intersection_area = (x_right - x_left) * (y_bottom - y_top)

    # Calculate individual areas
    box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)

    # Calculate union area
    union_area = box1_area + box2_area - intersection_area

    # 计算IoU
    iou = intersection_area / union_area
    return iou

def calculate_centerpoint(norm_gt_bboxs, norm_pre_bbox):
    x1_1, y1_1, x2_1, y2_1 = norm_gt_bboxs
    x1_2, y1_2, x2_2, y2_2 = norm_pre_bbox

    cx1 = (x1_1 + x2_1) / 2.0
    cy1 = (y1_1 + y2_1) / 2.0

    # Calculate center of the second box
    cx2 = (x1_2 + x2_2) / 2.0
    cy2 = (y1_2 + y2_2) / 2.0

    # Euclidean distance
    dist = math.hypot(cx1 - cx2, cy1 - cy2)

    return dist

def calculate_area_ratio(box1, box2):
    """
    """

    # Parse coordinates
    # print("box 1",box1)
    # print("box 2",box2)
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2

    # Calculate individual areas
    box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
    if box1_area <= 0:
        raise
    if box2_area <= 0:
        return 0.0

    return box1_area/ box2_area

def denorm_bbox(norm_bbox,size):
    bbox = [0,0,0,0]
    width,height = size
    bbox[0] = int(norm_bbox[0] * width)
    bbox[1] = int(norm_bbox[1] * height)
    bbox[2] = int(norm_bbox[2] * width)
    bbox[3] = int(norm_bbox[3] * height)
    return bbox

def norm_bbox(norm_bbox,size):
    bbox = [0,0,0,0]
    width,height = size
    bbox[0] = (norm_bbox[0] / width)
    bbox[1] = (norm_bbox[1] / height)
    bbox[2] = (norm_bbox[2] / width)
    bbox[3] = (norm_bbox[3] / height)
    return bbox

def bbox_number_types(bboxes):
    """
    Determine whether each number in a list of bboxes is an integer or a float.

    :param bboxes: List[List[float]], each bbox is [x1, y1, x2, y2]
    :return: List[List[str]], same structure as bboxes, each position returns "int" or "float"
    """
    result = []
    for box in bboxes:
        types = []
        for num in box:
            # If it's equal to its integer cast, treat it as an integer
            if isinstance(num, (int,)) or (isinstance(num, float) and num.is_integer()):
                types.append("int")
            else:
                types.append("float")
        result.append(types)
    return result

def extract_last_bracket_list(s: str) -> list:
    """
    Locates the last '[' and the last ']' in the string and extracts the content between them,
    splitting it by commas and returning it as a Python list.

    Args:
        s (str): Input string

    Returns:
        list: List of elements after splitting (whitespace removed), returns empty list if no matching brackets are found
    """
    # Find the last '[' and the last ']'
    last_open = s.rfind('[')
    last_close = s.rfind(']')

    # If either doesn't exist or they are in the wrong order, return empty list
    if last_open == -1 or last_close == -1 or last_open > last_close:
        return []

    # Extract the substring in the middle
    content = s[last_open + 1:last_close]

    # Split by comma and remove leading/trailing whitespace from each element
    # If empty elements should be supported, content.split(',') could be used instead
    items = [int(item.strip()) for item in content.split(',') if item.strip()]

    return items

def list_iou(list1, list2):
    """
    Calculates the Intersection over Union (IoU) of elements in two lists (or any iterable).

    Args:
        list1 (list): First list
        list2 (list): Second list

    Returns:
        float: IoU value in range [0, 1]. Returns 1.0 if both are empty.
    """
    set1 = set(list1)
    set2 = set(list2)

    if not set1 and not set2:
        return 1.0  # Both empty, define IoU as 1

    intersection = set1 & set2
    union = set1 | set2

    iou = len(intersection) / len(union)
    return iou

def k_option_norm(rate, k):

    grade = ((k*rate) - 1) / (k - 1)

    return grade

def refuse_option(text):
    if isinstance(text, list):
        response = ""
        for item in text:
            response += clean_string(item)
    if isinstance(text, str):
        response = clean_string(text)
    gt_list = ["A","B","C","D","E","F","G","H","I"]
    """ situation 1 No letter there"""
    none_flag = False
    for item in gt_list:
        if item in response:
            none_flag = True
    if none_flag==False: return True

    """ situation 2 """
    if len(response)>5:
        count = 0
        num = 0
        for item in gt_list:
            count = max(response.count(item), count)
            if response.count(item):
                num += 1
        if (count<=1)&(num>1):
            return True

def extract_score_from_text(text):
    """
    Extract numerical score from text
    
    Args:
        text (str): Text containing the score
    
    Returns:
        float: Extracted score, or None if extraction fails
    """
    # Try to match various score formats
    # Format 1: direct number (e.g. "7.5", "8", "9.0")
    # Format 2: "X/10" or "X out of 10"
    # Format 3: "score: X" or "rating: X"
    
    patterns = [
        r'(\d+\.?\d*)\s*/\s*10',  # "7.5/10" or "8 / 10"
        r'(\d+\.?\d*)\s*out\s*of\s*10',  # "7.5 out of 10"
        r'(?:score|rating|分数|评分)[:：\s]+(\d+\.?\d*)',  # "score: 7.5" or "rating: 8"
        r'(\d+\.?\d*)\s*(?:分|points?)',  # "7.5 points" or "8 points"
        r'\b(\d+\.?\d*)\b',  # Any independent number
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                score = float(match.group(1))
                # Ensure score is within reasonable range (0-10)
                if 0 <= score <= 10:
                    return score
            except (ValueError, IndexError):
                continue
    
    return None

def mllm_api(client, prompt = None, model=None):
    if isinstance(prompt, str):
        
        response = client.chat.completions.create(
            model= model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ],
                }
            ],
            max_tokens=5000,
        )

        response = response.choices[0].message.content
    if isinstance(prompt, list):
        response = []
        for p in prompt:
            response.append(mllm_api(client, p, model))
    return response

def task_2_ocr(data):
    """  simple ocr and hard ocr  """
    pure_words_ocr = []
    colorful_char_rotate_ocr = []
    for item in data:
        if item["task"] == "simple ocr":
            gt = item["gt"]
            response = item["response"]
            # if word_level_ac(gt, response) < 0.1:
            #     # print(response)
            #     continue
            pure_words_ocr.append(word_level_ac(gt, response))
        if item["task"] == "hard ocr":
            gt = item["gt"]
            response = item["response"]
            # if word_level_ac(gt, response)<0.1:
            #     # print(response)
            #     continue
            colorful_char_rotate_ocr.append(word_level_ac(gt, response))
    pw_wr1 = sum(pure_words_ocr) / len(pure_words_ocr)
    cw_wr1 = sum(colorful_char_rotate_ocr) / len(colorful_char_rotate_ocr)
    pure_words_ocr = []
    colorful_char_rotate_ocr = []
    for item in data:
        if item["task"] == "simple ocr":
            gt = item["gt"]
            response = item["response"]
            if word_level_ac(gt, response) < 0.1:
            #     # print(response)
                continue
            pure_words_ocr.append(word_level_ac(gt, response))
        if item["task"] == "hard ocr":
            gt = item["gt"]
            response = item["response"]
            if word_level_ac(gt, response)<0.1:
            #     # print(response)
                continue
            colorful_char_rotate_ocr.append(word_level_ac(gt, response))

    pw_wr2 = sum(pure_words_ocr) / len(pure_words_ocr)
    cw_wr2 = sum(colorful_char_rotate_ocr) / len(colorful_char_rotate_ocr)
    pw_r = len(pure_words_ocr) / 400
    cW_r = len(colorful_char_rotate_ocr) / 400

    return pw_wr1, pw_wr2, pw_r,  cw_wr1, cw_wr2, cW_r

def task_font_size(data):
    """  font size robustness  """
    font_size_list = [80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 25, 20, 15]
    font_size_dic = {}
    font_size_dic2 = {}
    for size in font_size_list:
        result1 = []
        for item in data:
            if item["task"] == "font size ocr":
                if size == item["subtask"]:
                    gt = item["gt"]
                    response = item["response"]
                    # if word_level_ac(gt, response)<0.1:
                    #     continue

                    result1.append(word_level_ac(gt, response))
        font_size_dic[str(size)] = sum(result1)/len(result1)
        font_size_dic2[str(size)] = len(result1)

    # print(f"font size robustness:")
    # for size in font_size_list:
    #     print(f"font size {size} : {font_size_dic[str(size)]:5f}  total imgs: {font_size_dic2[str(size)]}")

    font_size_dic3 = {}
    font_size_dic4 = {}
    for size in font_size_list:
        result2 = []
        for item in data:
            if item["task"] == "font size ocr":
                if size == item["subtask"]:
                    gt = item["gt"]
                    response = item["response"]
                    if word_level_ac(gt, response)<0.1:
                        continue

                    result2.append(word_level_ac(gt, response))
        font_size_dic3[str(size)] = sum(result2)/len(result2)
        font_size_dic4[str(size)] = len(result2)

    # print(f"font size robustness:")
    # for size in font_size_list:
    #     print(f"font size {size} : {font_size_dic3[str(size)]:5f}  total imgs: {font_size_dic4[str(size)]}")

    values = list(font_size_dic.values())
    mean = statistics.mean(values)
    std = statistics.stdev(values)  # sample standard deviation (ddof=1)

    values3 = list(font_size_dic3.values())
    mean3 = statistics.mean(values3)
    std3 = statistics.stdev(values3)

    recall_num = list(font_size_dic4.values())
    mean_r = statistics.mean(recall_num)

    # print(f"Mean: {mean:.3f} Std: {std:.3f} Mean: {mean3:.3f} Std: {std3:.3f} reacall_num: {mean_r}")
    # print(f"Mean: {mean:.3f} Std: {std:.3f} Mean: {mean3:.3f} Std: {std3:.3f} reacall_num: {mean_r:.3f}")

    return mean, std, mean3, std3, mean_r/100

def task_logo_cor(data):
    """  logo ocr  """
    result = []
    for item in data:
        if item["task"] == "logo ocr":
            gt = item["gt"]
            response = item["response"]
            result.append(logo_ocr_ac(gt, response))
    # print(f"logo  ocr  accuracy: {sum(result)/len(result):.3f}  total imgs: {len(result)}")
    return sum(result)/len(result)

def task_poster_ocr(data):
    """  real poster ocr  """
    result = []
    for item in data:
        if item["task"] == "poster ocr":
            if "gt" in item:
                gt = item["gt"]
            if "texts" in item:
                gt = item["texts"]
            response = item["response"]
            ac = real_poster_ac(gt, response)
            if ac<0.05: continue
            result.append(ac)
    # print(f"poster ocr accuracy (entity-level): {sum(result)/len(result):.3f}  total imgs: {len(result)}")
    return sum(result)/len(result)

def task_font_matching_1(data):
    """  font matching 1  """
    result = []
    for item in data:
        if item["task"] == "font matching 1":
            if "gt" in item:
                gt = item["gt"]
            if "texts" in item:
                gt = item["texts"]
            response = item["response"]
            if refuse_option(response):
                continue
            # print(response)
            result.append(font_matching_ac(gt, response))
    # print(f"font matching 1 accuracy: {sum(result) / len(result):5f}  total imgs: {len(result)}")
    return sum(result) / len(result)

def task_font_matching_2(data):
    """  font matching 2  """
    result = []
    for item in data:
        if item["task"] == "font matching 2":
            if "gt" in item:
                gt = item["gt"]
            if "texts" in item:
                gt = item["texts"]
            response = item["response"]
            if refuse_option(response):
                continue
            # print(response)
            result.append(font_matching_ac(gt, response))
    # print(f"font matching 2 accuracy: {sum(result) / len(result):5f}  total imgs: {len(result)}")
    return sum(result) / len(result)

def task_font_attr(data):
    """  font attributes  """
    result = []
    for item in data:
        if item["task"] == "font attributes":
            if "gt" in item:
                gt = item["gt"]
            if "texts" in item:
                gt = item["texts"]
            response = item["response"]
            if refuse_option(response):
                continue
            # print(response)
            result.append(font_attr_ac(gt, response))
    # print(f"font attributes accuracy: {sum(result) / len(result):5f}  total imgs: {len(result)}")

    font_attr_list = []
    font_attr_dic = {}
    for item in data:
        if item["task"] == "font attributes":
            font_attr_list.append(item["subtask"])
    font_attr_list = list(set(font_attr_list))
    # print(font_attr_list)
    for attr in font_attr_list:
        result2 = []
        for item in data:
            if item["task"] == "font attributes":
                if item["subtask"] == attr:
                    if "gt" in item:
                        gt = item["gt"]
                    if "texts" in item:
                        gt = item["texts"]
                    response = item["response"]
                    result2.append(font_attr_ac(gt, response))
        font_attr_dic[attr]= sum(result2) / len(result2)

    # for attr in font_attr_list:
        # print(f"attr {attr}:  {font_attr_dic[attr]:5f}")
    return sum(result) / len(result)

def task_font_effect(data):
    """  font effect  """
    result = []
    for item in data:
        if item["task"] == "font effect":
            if "gt" in item:
                gt = item["gt"]
            if "texts" in item:
                gt = item["texts"]
            response = item["response"]
            # print(response)
            result.append(font_effect_ac(gt, response))
    # print(f"font effect accuracy: {sum(result) / len(result):.5f}  total imgs: {len(result)}")

    font_effect_list = []
    font_effect_dic = {}
    for item in data:
        if item["task"] == "font effect":
            font_effect_list.append(item["subtask"])
    font_effect_list = list(set(font_effect_list))
    # print(font_effect_list)

    for effect in font_effect_list:
        result2 = []
        for item in data:
            if item["task"] == "font effect":
                if item["subtask"] == effect:
                    if "gt" in item:
                        gt = item["gt"]
                    response = item["response"]
                    result2.append(font_effect_ac(gt, response))
        font_effect_dic[effect] = sum(result2) / len(result2)
    # for effect in font_effect_list:
    #     print(f"attr {effect}:  {font_effect_dic[effect]:5f}")

    return sum(result) / len(result)

def task_font_effect_2(data):
    """  font effect 2 """
    result_c = []
    result_e = []
    for item in data:
        if item["task"] == "font effect 2":
            if "gt" in item:
                gt = item["gt"]
            if "texts" in item:
                gt = item["texts"]
            response = item["response"]
            # print(response)
            color_ac, effect_ac = font_effect_2_ac(gt, response)
            result_c.append(color_ac)
            if effect_ac != None:
                result_e.append(effect_ac)

    # print(f"font effect 2  color accuracy: {sum(result_c) / len(result_c):5f}  total imgs: {len(result_c)}")
    # print(f"font effect 2 effect accuracy: {sum(result_e) / len(result_e):5f}  total imgs: {len(result_e)}")

    return sum(result_c) / len(result_c), sum(result_e) / len(result_e)

def task_layout_comparison(data):
    """  layout comparison  """
    result = []
    for item in data:
        if item["task"] == "layout comparison":
            if "gt" in item:
                gt = item["gt"]
            # if "texts" in item:
            #     gt = item["texts"]
            response = item["response"]
            # print(response)
            result.append(layout_comparison_ac(gt, response))
    # print(f"layout disorder comparison accuracy: {sum(result) / len(result):5f}  total imgs: {len(result)}")
    return sum(result) / len(result)

def task_rotation(data):
    """  rotation  """
    a_result = []
    r_result = []
    r1_result = []
    r2_result = []
    r3_result = []

    for item in data:
        response = item["response"]
        if isinstance(response, list):
            answer = ""
            for content in response:
                answer += content
        if isinstance(response, str):
            answer = response

        if item["task"] == "rotation":
            if "gt" in item:
                gt = item["gt"]
            if "alignment" in item:
                gt_align = item["alignment"]
            if "rotation" in item:
                gt_rotate = item["rotation"]

            r_ac = 0
            if "counterclockwise rotation" in gt_rotate:
                if "counterclockwise rotation" in answer:
                    r1_ac = 1
                else:
                    r1_ac = 0
                r1_result.append(r1_ac)
            if "no rotation" in gt_rotate:
                if "no rotation" in answer:
                    r2_ac = 1
                else:
                    r2_ac = 0
                r2_result.append(r2_ac)

            if "clockwise rotation" in gt_rotate:
                if "counterclockwise rotation" in answer:
                    r3_ac = 0
                elif "clockwise rotation" in answer:
                    r3_ac = 1
                else:
                    r3_ac = 0
                r3_result.append(r3_ac)

            for a in gt_align:
                a_ac = 0
                if a in answer:
                    a_ac = 1
                a_result.append(a_ac)


    r_result.extend(r1_result)
    r_result.extend(r2_result)
    r_result.extend(r3_result)


    # print(f"alignment accuracy: {sum(a_result) / len(a_result):5f}  total imgs: {len(a_result)}")
    # print(f"rotation  accuracy: {sum(r1_result) / len(r1_result):5f}  total imgs: {len(r1_result)}")
    # print(f"rotation  accuracy: {sum(r2_result) / len(r2_result):5f}  total imgs: {len(r2_result)}")
    # print(f"rotation  accuracy: {sum(r3_result) / len(r3_result):5f}  total imgs: {len(r3_result)}")

    return sum(a_result) / len(a_result), sum(r_result) / len(r_result)

def task_text_localization(data, max_box_num=30):
    """  text localization  """
    ratio_list = []
    wrong_recall = 0
    iou_list = []
    center_bias_list = []
    area_ratio_list = []
    for item in data:
        if item["task"] == "text localization":
            if "gt" in item:
                gt_bboxs = item["gt"]
            if "text_bbox" in item:
                gt_bboxs = item["text_bbox"]
            width, height = item["size"]
            response = item["response"]
            if isinstance(response, list):
                answer = ""
                for content in response:
                    answer += content
            if isinstance(response, str):
                answer = response


            pre_bboxs = parse_bbox_string(answer)
            # new_item["text_bbox"] = pre_bboxs
            # new_item["text_bbox"] = [denorm_bbox(pre_bboxs[i], [width, height]) for i in range(len(pre_bboxs))]
            bbox_type =  bbox_number_types(pre_bboxs)

            ratio = min(len(pre_bboxs) / len(gt_bboxs) , 1)
            ratio_list.append(ratio)
            if ratio != 1:
                # print(f"{ratio:3f} boxes: {len(gt_bboxs)}")
                wrong_recall += 1
            # else:
            """At most 5 bboxes"""
            incount_bbox_num = min(len(gt_bboxs), len(pre_bboxs), max_box_num)
            for i in range(incount_bbox_num):
                # print(pre_bboxs[i])
                # if (sum(pre_bboxs[i])/len(pre_bboxs[i]))>1:
                """calculate iou"""
                iou1 = calculate_iou(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [width, height]))
                # if (sum(pre_bboxs[i])/len(pre_bboxs[i]))<1:
                iou2 = calculate_iou(norm_bbox(gt_bboxs[i], [width, height]), pre_bboxs[i])

                iou3 = calculate_iou(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [1024, 1024]))

                iou4 = calculate_iou(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [1000, 1000]))

                ious = [iou1, iou2, iou3, iou4]
                max_iou = max(ious)
                max_index = ious.index(max_iou)

                """calculate center distance"""
                dis1 = calculate_centerpoint(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [width, height]))
                # if (sum(pre_bboxs[i])/len(pre_bboxs[i]))<1:
                dis2 = calculate_centerpoint(norm_bbox(gt_bboxs[i], [width, height]), pre_bboxs[i])

                dis3 = calculate_centerpoint(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [1024, 1024]))

                dis4 = calculate_centerpoint(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [1000, 1000]))

                dis_list = [dis1, dis2, dis3, dis4]
                min_center_dis = min(dis_list)
                index = dis_list.index(min_center_dis)

                """calculate area ratio"""
                area_r_1 = calculate_area_ratio(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [width, height]))
                # if (sum(pre_bboxs[i])/len(pre_bboxs[i]))<1:
                area_r_2 = calculate_area_ratio(norm_bbox(gt_bboxs[i], [width, height]), pre_bboxs[i])

                area_r_3 = calculate_area_ratio(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [1024, 1024]))

                area_r_4 = calculate_area_ratio(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [1000, 1000]))

                area_r_t = [abs(area_r_1 - 1 ), abs(area_r_2 - 1 ), abs(area_r_3 - 1 ), abs(area_r_4 - 1 )]
                area_r_s = [area_r_1, area_r_2, area_r_3, area_r_4]
                value = min(area_r_t)
                index = area_r_t.index(value)
                area_r = area_r_s[index]
                # print("area_r",area_r)


                iou_list.append(max_iou)
                center_bias_list.append(min_center_dis)
                area_ratio_list.append(area_r)

    # print("wrong recall rate:", wrong_recall / len(ratio_list))
    # print(f"ratio mean: {sum(ratio_list)/len(ratio_list)}  ration vat: {statistics.pstdev(ratio_list)} ")
    # print("box total: ",len(iou_list))
    # print(f"iou mean: {sum(iou_list) / len(iou_list):5f}")
    # print(f"iou pstdev: {statistics.pstdev(iou_list):5f}")
    #
    # print(f"center shift mean : {sum(center_bias_list) / len(center_bias_list):5f}")
    # print(f"center shift pstdev: {statistics.pstdev(center_bias_list):5f}")
    #
    # print(f"area_ratio mean: {sum(area_ratio_list) / len(area_ratio_list):5f}")
    # print(f"area_ratio pstdev: {statistics.pstdev(area_ratio_list):5f}")
    return sum(iou_list) / len(iou_list), sum(ratio_list)/len(ratio_list)

def task_layout_generation(data):
    """  layout generation  """
    ratio_list = []
    wrong_recall = 0
    iou_list = []
    center_bias_list = []
    area_ratio_list = []
    for item in data:
        if item["task"] == "layout generation":
            if "gt" in item:
                gt_bboxs = item["gt"]
            if "text_bbox" in item:
                gt_bboxs = item["text_bbox"]
            width, height = item["size"]
            response = item["response"]
            if isinstance(response, list):
                answer = ""
                for content in response:
                    answer += content
            if isinstance(response, str):
                answer = response


            pre_bboxs = parse_bbox_string(answer)
            # new_item["text_bbox"] = pre_bboxs
            # new_item["text_bbox"] = [denorm_bbox(pre_bboxs[i], [width, height]) for i in range(len(pre_bboxs))]
            bbox_type =  bbox_number_types(pre_bboxs)

            ratio = min(len(pre_bboxs) / len(gt_bboxs), 1)
            # ratio = len(pre_bboxs) / len(gt_bboxs)
            ratio_list.append(ratio)
            if ratio != 1:
                # print(f"{ratio:3f} boxes: {len(gt_bboxs)}")
                wrong_recall += 1
            # else:
            """最多算5个bbox"""
            incount_bbox_num = min(len(gt_bboxs), len(pre_bboxs))
            for i in range(incount_bbox_num):
                # print(pre_bboxs[i])
                # if (sum(pre_bboxs[i])/len(pre_bboxs[i]))>1:
                """calculate iou"""
                iou1 = calculate_iou(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [width, height]))
                # if (sum(pre_bboxs[i])/len(pre_bboxs[i]))<1:
                iou2 = calculate_iou(norm_bbox(gt_bboxs[i], [width, height]), pre_bboxs[i])

                iou3 = calculate_iou(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [1024, 1024]))

                iou4 = calculate_iou(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [1000, 1000]))

                ious = [iou1, iou2, iou3, iou4]
                max_iou = max(ious)
                max_index = ious.index(max_iou)

                """calculate center distance"""
                dis1 = calculate_centerpoint(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [width, height]))
                # if (sum(pre_bboxs[i])/len(pre_bboxs[i]))<1:
                dis2 = calculate_centerpoint(norm_bbox(gt_bboxs[i], [width, height]), pre_bboxs[i])

                dis3 = calculate_centerpoint(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [1024, 1024]))

                dis4 = calculate_centerpoint(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [1000, 1000]))

                dis_list = [dis1, dis2, dis3, dis4]
                min_center_dis = min(dis_list)
                index = dis_list.index(min_center_dis)

                """calculate area ratio"""
                area_r_1 = calculate_area_ratio(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [width, height]))
                # if (sum(pre_bboxs[i])/len(pre_bboxs[i]))<1:
                area_r_2 = calculate_area_ratio(norm_bbox(gt_bboxs[i], [width, height]), pre_bboxs[i])

                area_r_3 = calculate_area_ratio(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [1024, 1024]))

                area_r_4 = calculate_area_ratio(norm_bbox(gt_bboxs[i], [width, height]), norm_bbox(pre_bboxs[i], [1000, 1000]))

                area_r_t = [abs(area_r_1 - 1 ), abs(area_r_2 - 1 ), abs(area_r_3 - 1 ), abs(area_r_4 - 1 )]
                area_r_s = [area_r_1, area_r_2, area_r_3, area_r_4]
                value = min(area_r_t)
                index = area_r_t.index(value)
                area_r = area_r_s[index]
                if area_r >1 :
                    area_r = 1/area_r
                # print("area_r",area_r)


                iou_list.append(max_iou)
                center_bias_list.append(min_center_dis)
                area_ratio_list.append(area_r)

    # print("wrong recall rate:", wrong_recall / len(ratio_list))
    # print(f"ratio mean: {sum(ratio_list)/len(ratio_list):.3f}  ration vat: {statistics.pstdev(ratio_list):.3f} ")
    rate = sum(ratio_list)/len(ratio_list)
    # print("box total: ",len(iou_list))
    # print(f"iou mean: {sum(iou_list) / len(iou_list):.3f}")
    # print(f"iou pstdev: {statistics.pstdev(iou_list):5f}")

    # print(f"center shift mean : {sum(center_bias_list) / len(center_bias_list):.3f}")
    bias = sum(center_bias_list) / len(center_bias_list)
    # print(f"center shift pstdev: {statistics.pstdev(center_bias_list):.3f}")

    # print(f"area_ratio mean: {sum(area_ratio_list) / len(area_ratio_list):.3f}")
    area_rate = sum(area_ratio_list) / len(area_ratio_list)
    # print(f"area_ratio pstdev: {statistics.pstdev(area_ratio_list):.3f}")

    return bias, area_rate, rate

def task_empty_space(data):
    """  empty space  """
    result = []
    wrong_recall_list = []
    for item in data:
        if item["task"] == "empty space":
            if "gt" in item:
                gt = item["gt"]
            response = item["response"]
            if isinstance(response, list):
                answer = ""
                for content in response:
                    answer += content
            if isinstance(response, str):
                answer = response

            answer = extract_last_bracket_list(answer)
            ac = list_iou(gt, answer)
            # print(ac)
            result.append(ac)
            if len(gt)==len(answer):
                wrong_recall = 1
            else:
                wrong_recall = 0
            wrong_recall_list.append(wrong_recall)

    # print(f"empty space accuracy: {sum(result) / len(result):.5f}  total imgs: {len(result)}")
    # print(f"empty space recall  : {sum(wrong_recall_list) / len(wrong_recall_list):.5f}  total imgs: {len(wrong_recall_list)}")

    return sum(result) / len(result) , sum(wrong_recall_list)/len(wrong_recall_list)

def task_alignment(data):
    """  align """
    a_result = []

    for item in data:
        response = item["response"]
        if isinstance(response, list):
            answer = ""
            for content in response:
                answer += content
        if isinstance(response, str):
            answer = response

        if item["task"] == "alignment":
            if "gt" in item:
                gt = item["gt"]
            if "alignment" in item:
                gt_align = item["alignment"]


            for a in gt_align:
                a_ac = 0
                if a in answer:
                    a_ac = 1
                a_result.append(a_ac)




    # print(f"alignment accuracy: {sum(a_result) / len(a_result):5f}  total imgs: {len(a_result)}")
    # print(f"rotation  accuracy: {sum(r1_result) / len(r1_result):5f}  total imgs: {len(r1_result)}")
    # print(f"rotation  accuracy: {sum(r2_result) / len(r2_result):5f}  total imgs: {len(r2_result)}")
    # print(f"rotation  accuracy: {sum(r3_result) / len(r3_result):5f}  total imgs: {len(r3_result)}")

    return sum(a_result) / len(a_result)

def task_style_understanding(data):
    result = []
    for item in data:
        if item["task"] == "style understanding":

            gt = item["gt"]
            response = item["response"]
            if isinstance(response, list):
                answer = ""
                for content in response:
                    answer += content
            if isinstance(response, str):
                answer = response
            answer = answer.strip()
            answer = answer.lower()
            response = response.lower()
            if len(response)>30:
                response = response[:30]
            else:
                response = response
            gt = gt.lower()
            if answer in gt or gt in answer:
                result.append(1)
            else:
                # print(item)
                result.append(0)
    return sum(result) / len(result)

def task_composition_understanding(client, data, json_item):
    todo_items = [item for item in data if item["task"]=="composition understanding"]
    prompt_templet = 'Please help me determine if the content in the Description contains Key Information. If it does, answer directly with "Yes"; if it does not, answer directly with "No". Please respond only with "Yes" or "No", without any additional output.'
    def process_item(item):
        if "judge" in item: return item
        promts = [prompt_templet +"\n"+ "Description: " + item["response"] +"\n"+ "Key Information: " + gt for gt in item["gt"]]
        item["judge"] = mllm_api(client, prompt = promts, model= "gpt-5")
        return item
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(process_item, item): item for item in todo_items}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing "):
            result = future.result()


    score_list = []
    points = 0
    for item in todo_items:
        item_point_list = []
        if "judge" in item:
            for content in item["judge"]:
                if "Yes" in content:
                    points += 1
                    item_point_list.append(1)
                else:
                    item_point_list.append(0)
        score = sum(item_point_list)/len(item_point_list)
        score_list.append(score)
    try:
        save_json_file(data, json_item)
        print(f"JSON file saved successfully: {json_item}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

    return sum(score_list) / len(score_list)

def task_intention_understanding(client, data, json_item):
    todo_items = [item for item in data if item["task"]=="intention understanding"]
    prompt_templet = 'Please help me determine if the content in the Description contains Key Information. If it does, answer directly with "Yes"; if it does not, answer directly with "No". Please respond only with "Yes" or "No", without any additional output.'
    def process_item(item):
        if "judge" in item: return item
        promts = [prompt_templet +"\n"+ "Description: " + item["response"] +"\n"+ "Key Information: " + gt for gt in item["gt"]]
        item["judge"] = mllm_api(client, prompt = promts, model= "gpt-5")
        return item
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(process_item, item): item for item in todo_items}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing "):
            result = future.result()


    score_list = []
    points = 0
    for item in todo_items:
        item_point_list = []
        for content in item["judge"]:
            if "Yes" in content:
                points += 1
                item_point_list.append(1)
            else:
                item_point_list.append(0)
        score = sum(item_point_list)/len(item_point_list)
        score_list.append(score)
    try:
        save_json_file(data, json_item)
        print(f"JSON file saved successfully: {json_item}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

    return sum(score_list) / len(score_list)

def task_overall_rating(data):
    """
    Compare model response score with ground truth score
    Calculate Mean Absolute Error (MAE) using vector comparison method
    
    Args:
        data: List containing task data
    
    Returns:
        float: Cosine similarity
    """
    result_scores = []
    gt_scores = []
    
    for item in data:
        if item["task"] == "overall rating":
            # Extract ground truth score
            if "gt" in item:
                gt = item["gt"]
                # If gt is already a number, use it directly; otherwise try to extract from string
                if isinstance(gt, (int, float)):
                    gt_score = float(gt)
                else:
                    gt_score = extract_score_from_text(str(gt))
                
                if gt_score is None:
                    continue
            else:
                continue
            
            # Extract score from response
            response = item["response"]
            if isinstance(response, list):
                answer = ""
                for content in response:
                    answer += str(content)
            elif isinstance(response, str):
                answer = response
            else:
                continue
            
            answer = answer.strip()
            result_score = extract_score_from_text(answer)
            
            if result_score is not None:
                result_scores.append(result_score)
                gt_scores.append(gt_score)
    
    # Check if there is valid data
    if len(result_scores) == 0 or len(gt_scores) == 0:
        print("Warning: No valid score data found")
        return 0.0
    
    # Convert to numpy array for calculation (refer to compare_score_lists method in AF_score.py)
    arr_result = np.array(result_scores)
    arr_gt = np.array(gt_scores)
    
    def controll_mean_variance(scores, target_mean=0, target_std=2.0):
        # Modulate mean and variance of scores to target_mean and target_std
        arr_scores = np.array(scores)
        mean = np.mean(arr_scores)
        std = np.std(arr_scores)
        if std == 0:
            return scores
        return (scores - mean) * (target_std / std) + target_mean

    arr_result = controll_mean_variance(arr_result, target_mean=0, target_std=3.0)
    arr_gt = controll_mean_variance(arr_gt, target_mean=0, target_std=3.0)

    
    # Calculate cosine similarity of differences
    cosine_similarity = np.dot(arr_result, arr_gt) / (np.linalg.norm(arr_result) * np.linalg.norm(arr_gt))
    return cosine_similarity

if __name__=="__main__":
    output_file_path = r"C:\Users\11978\Desktop\PosterIQ\metricIQ\metric_results.txt"
    output_file = open(output_file_path, 'w', encoding='utf-8')
    
    def print_and_log(text):
        """Print to console and write to file simultaneously"""
        print(text)
        output_file.write(text + '\n')
        output_file.flush()  
    
    jsonlist = [

        "./Qwen3-VL-8B-Instruct_bench.json",

    ]
    
    client = OpenAI(
        base_url="https://xxx",
        # replace sk-xxx with your own key
        api_key='sk-xxx'
    )

    try:
        for json_item in jsonlist:
            print_and_log("--------------------------------")
            print_and_log(os.path.basename(json_item))
            data = read_json_file(json_item)
            """ocr"""
            logo_ac = task_logo_cor(data)
            poster_ac = task_poster_ocr(data)
            print_and_log(f"logo ocr & poster ocr")
            print_and_log(f"{logo_ac:.3f} & {poster_ac:.3f}")
            """robost ocr"""
            pw_wr1, pw_wr2, pw_r,  cw_wr1, cw_wr2, cW_r = task_2_ocr(data)
            print_and_log(f"simple ocr & hard ocr")
            print_and_log(f"{pw_wr1:.3f} & {cw_wr1:.3f}")
            """font size ocr"""
            mean, std, mean3, std3, mean_r = task_font_size(data)
            print_and_log(f"font size mean & font size std")
            print_and_log(f"& {mean:.3f} & {std:.3f}") # The following are for after finishing recall rate
            
            """font task"""
            fm1 = task_font_matching_1(data)
            fm2 = task_font_matching_2(data)
            fm = (fm1 + fm2) /2
            fm_score = k_option_norm(fm, k=9)
            
            fattr = task_font_attr(data)
            fattr_score = k_option_norm(fattr, k=2)
            
            fe1 = task_font_effect(data)
            fc,fe2 = task_font_effect_2(data)
            fe1_score = k_option_norm(fe1,k=9)
            fc_score, fe2_score = k_option_norm(fc,k=16), k_option_norm(fe2, k=48)
            print_and_log(f"font match & font attr & font effect 1 & font color & font effect 2")
            print_and_log(f"& {fm_score:.3f} & {fattr_score:.3f} & {fe1_score:.3f} & {fc_score:.3f} & {fe2_score:.3f}")
            
            """text localization"""
            top1_iou, _ = task_text_localization(data, max_box_num=1)
            top3_iou, _ = task_text_localization(data, max_box_num=3)
            top5_iou, _ = task_text_localization(data, max_box_num=5)
            mean_iou, recall = task_text_localization(data, max_box_num=30)
            # print(f"{top1_iou:.3f} & {top3_iou:.3f} & {top5_iou:.3f} & {mean_iou:.3f} & {recall:.3f}")
            print_and_log(f"text localization")
            print_and_log(f"top1 iou & top3 iou & mean iou & recall")
            print_and_log(f"{top1_iou:.3f} & {top3_iou:.3f} & {mean_iou:.3f} & {recall:.3f}")
            """text positioning"""
            a, r = task_rotation(data)
            a, r = k_option_norm(a, k=3), k_option_norm(r, k=3)
            print_and_log(f"text positioning")
            print_and_log(f"rotation")
            print_and_log(f"{r:.3f}")
            ac = task_alignment(data)
            ac = k_option_norm(ac, k=3)
            print_and_log(f"alignment")
            print_and_log(f"{ac:.3f}")
            """empty space"""
            iou, match = task_empty_space(data)
            print_and_log(f"empty space")
            print_and_log(f"iou & match")
            print_and_log(f"{iou:.3f} & {match:.3f}")
            """layout comparison"""
            vs = task_layout_comparison(data)
            vs_score = k_option_norm(vs, k=2)
            print_and_log(f"layout comparison")
            print_and_log(f"{vs_score:.3f}")
            """layout generation"""
            bias, area_rate, rate = task_layout_generation(data)
            print_and_log(f"layout generation")
            print_and_log(f"bias & area rate & rate")
            print_and_log(f"{bias:.3f} & {area_rate:.3f} & {rate:.3f}")
            
            
            
            """style understanding"""
            ac = task_style_understanding(data)
            ac  = k_option_norm(vs, k=17)
            print_and_log(f"style understanding")
            print_and_log(f"{ac:.3f}")
            """composition understanding"""
            points = task_composition_understanding(client,data,json_item)
            print_and_log(f"composition understanding")
            print_and_log(f"& {points:.3f}")
            """intention understanding"""
            points = task_intention_understanding(client,data,json_item)
            print_and_log(f"intention understanding")
            print_and_log(f"& {points:.3f}")
            save_json_file(data, json_item)
            
            
            
            """overall rating"""
            cos_sim = task_overall_rating(data)
            print_and_log(f"overall rating")
            print_and_log(f"{cos_sim:.3f}")
        
        print_and_log("--------------------------------")
        print_and_log(f"\nAll results have been saved to: {output_file_path}")
    
    finally:
        # Ensure the file is correctly closed
        output_file.close()
        print(f"File closed: {output_file_path}")
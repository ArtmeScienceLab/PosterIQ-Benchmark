import os
import json
import base64
from PIL.Image import new
from openai import OpenAI
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data
def save_json_file(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
def merge_json(json_list,folder_path):
    data = []
    for json_file in json_list:
        data.extend(read_json_file(json_file))
    save_json_file(data, os.path.join(folder_path, "merge.json"))
    return data

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def mllm_api(client, prompt = None, image_path = None, model=None):
    extension = image_path.split('.')[-1]
    base64_image = encode_image(image_path)
    extension = image_path.split('.')[-1]
    
    if isinstance(prompt, str):
        
        response = client.chat.completions.create(
            model= model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                         ,
                        {
                        "type": "image_url",
                        "image_url": {
                             "url": f"data:image/{extension};base64,{base64_image}"
                            }
                        },
                    ],
                }
            ],
            max_tokens=5000,
        )

        response = response.choices[0].message.content
    if isinstance(prompt, list):
        response = []
        for p in prompt:
            response.append(mllm_api(client, p, image_path, model))
    return response

def compute_yes_score(data):
    yes_score = 0
    for item in data:
        if isinstance(item["judge"], list):
            miniscore = 0
            for content in item["judge"]:
                if content.lower() == "yes":
                    miniscore += 1
            yes_score += miniscore / len(item["judge"])
        elif item["judge"].lower() == "yes":
            yes_score += 1
    return yes_score / len(data)

def compute_style_score(data):
    yes_score = 0
    for item in data:
        if isinstance(item["judge"], list):
            miniscore = 0
            for content in item["judge"]:
                if content.lower() == item["style"].lower():
                    miniscore += 1
            yes_score += miniscore / len(item["judge"])
        elif item["judge"].lower() == item["style"].lower():
            yes_score += 1
    return yes_score / len(data)

def compute_font_score(data):
    font_score = 0
    font_attr_dict = {"angular": 0, "artistic": 0, "attention-grabbing": 0, "attractive": 0, "bad": 0, "boring": 0, "calm": 0, "capitals": 0, "charming": 0, "clumsy": 0, "complex": 0, "cursive": 0, "delicate": 0, "disorderly": 0, "display": 0, "dramatic": 0, "formal": 0, "fresh": 0, "friendly": 0, "gentle": 0, "graceful": 0, "happy": 0, "italic": 0, "legible": 0, "modern": 0, "monospace": 0, "playful": 0, "pretentious": 0, "serif": 0, "sharp": 0, "sloppy": 0, "soft": 0, "strong": 0, "technical": 0, "thin": 0, "warm": 0, "wide": 0}
    for item in data:
        for attr in font_attr_dict.keys():
            if attr.lower() in item["judge"].lower():
                font_attr_dict[attr] += 1
                
    for attr in font_attr_dict.keys():
        font_score += font_attr_dict[attr] / len(data)
    return font_score/len(font_attr_dict.keys())


def process_item_list(new_item,client,judge_model,prompt_templet):
    image_path = new_item["local_path"]
    prompt = [prompt_templet + gt for gt in new_item["gt"]]
    count = 0
    while True:
        try:
            new_item["judge"] = mllm_api(client, prompt, image_path, judge_model)
            break
        except Exception as e:
            print(f"Error {new_item['name']} {e}")
            time.sleep(1)
            count += 1
            if count > 10:
                break
            new_item["judge"] = "error"
            continue
    return new_item

def process_item_single(new_item,client,judge_model,prompt_templet):
    image_path = new_item["local_path"]
    prompt = prompt_templet
    count = 0
    while True:
        try:
            new_item["judge"] = mllm_api(client, prompt, image_path, judge_model)
            break
        except Exception as e:
            print(f"Error {new_item['name']} {e}")
            time.sleep(1)
            count += 1
            if count > 10:
                break
            new_item["judge"] = "error"
            continue
    return new_item

def task_dense_generation(data,folder_path,model_name,client):
    todo_items = []
    for item in data:
        if item["task"] == "poster dense":
            new_item = {}
            new_item["task"] = item["task"]
            new_item["name"] = item["name"]
            new_item["path"] = item["path"]
            new_item["local_path"] = os.path.join(folder_path, item["path"])
            new_item["prompt"] = item["prompt"]
            new_item["gt"] = item["gt"]
            image_path = os.path.join(folder_path, item["path"]) 
            if not os.path.exists(image_path):
                continue
            todo_items.append(new_item)
            

    prompt_templet = 'Please evaluate the generated image. If the image matches the following key information, respond only with "Yes". If it does not match, respond only with "No". Do not include any explanations or additional text. Key information: '

            
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(process_item_list, new_item,client,"gpt-5-2025-08-07",prompt_templet): new_item for new_item in todo_items}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing "):
            result = future.result()
    
    print("task_dense_generation images:",len(todo_items))
    score = compute_yes_score(todo_items)
    print("task_dense_generation score:",score)
    return todo_items,score

def task_font_generation(data,folder_path,model_name,client):
    todo_items = []
    for item in data:
        if item["task"] == "poster font":
            new_item = {}
            new_item["task"] = item["task"]
            new_item["name"] = item["name"]
            new_item["path"] = item["path"]
            new_item["local_path"] = os.path.join(folder_path, item["path"])
            new_item["prompt"] = item["prompt"]
            image_path = os.path.join(folder_path, item["path"]) 
            if not os.path.exists(image_path):
                continue
            todo_items.append(new_item)
    prompt_templet = 'Please evaluate the generated image. The image contains several visible text fonts. Carefully observe the shapes, strokes, and overall visual style of the text. From the following attribute set, select only the attributes that are likely present in the fonts visible in the image. \nReturn your answer as a Python-style list of strings (e.g., ["modern", "strong", "legible"]). \nDo not include any explanations or additional text.\nAttribute set:\n[angular, artistic, attention-grabbing, attractive, bad, boring, calm, capitals, charming, clumsy, complex, cursive, delicate, disorderly, display, dramatic, formal, fresh, friendly, gentle, graceful, happy, italic, legible, modern, monospace, playful, pretentious, serif, sharp, sloppy, soft, strong, technical, thin, warm, wide]'
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(process_item_single, new_item,client,"gpt-5-2025-08-07",prompt_templet): new_item for new_item in todo_items}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing "):
            result = future.result()
    
    print("task_font_generation images:",len(todo_items))
    score = compute_font_score(todo_items)
    print("task_font_generation score:",score)
    return todo_items,score

def task_style_generation(data,folder_path,model_name,client):
    todo_items = []
    for item in data:
        if item["task"] == "poster style":
            new_item = {}
            new_item["task"] = item["task"]
            new_item["name"] = item["name"]
            new_item["path"] = item["path"]
            new_item["local_path"] = os.path.join(folder_path, item["path"])
            new_item["prompt"] = item["prompt"]
            new_item["style"] = item["style"]
            image_path = os.path.join(folder_path, item["path"]) 
            if not os.path.exists(image_path):
                continue
            todo_items.append(new_item)
    prompt_templet = "You are a professional visual design analyst. Task: Given an input poster image, identify its *dominant visual style* based on composition, color palette, typography, and artistic features. Return only one style name from the following list: \n['Flat Design', 'Illustrative Style', 'Minimalist Style', 'New Chinese Aesthetic', 'Japanese Style', 'Cinema 4D Style', 'Retro Style', 'Diffuse Glow Style', 'Acid Graphics', 'Papercut Style', 'Pixel Art', 'Pop Art', 'Vaporwave Style', 'Cyberpunk Style', 'Glitch Art', 'Memphis Style', 'Typographic Minimalism'] \nGuidelines:\n- Do not add explanations or probabilities. \n- Output must exactly match one of the items in the list.\n         "

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(process_item_single, new_item,client,"gpt-5-2025-08-07",prompt_templet): new_item for new_item in todo_items}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing "):
            result = future.result()
    print("task_style_generation images:",len(todo_items))
    score = compute_style_score(todo_items)
    print("task_style_generation score:",score)
    return todo_items,score

def task_composition_generation(data,folder_path,model_name,client):
    todo_items = []
    for item in data:
        if item["task"] == "poster composition":
            new_item = {}
            new_item["task"] = item["task"]
            new_item["name"] = item["name"]
            new_item["path"] = item["path"]
            new_item["local_path"] = os.path.join(folder_path, item["path"])
            new_item["prompt"] = item["prompt"]
            new_item["gt"] = item["gt"]
            image_path = os.path.join(folder_path, item["path"]) 
            if not os.path.exists(image_path):
                continue
            todo_items.append(new_item)
    prompt_templet = 'Please evaluate the generated image. If the image matches the following key information, respond only with "Yes". If it does not match, respond only with "No". Do not include any explanations or additional text. Key information: '
 
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(process_item_list, new_item,client,"gemini-2.5-pro",prompt_templet): new_item for new_item in todo_items}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing "):
            result = future.result()
    print("task_composition_generation images:",len(todo_items))
    score = compute_yes_score(todo_items)
    print("task_composition_generation score:",score)
    return todo_items,score


def task_intention_generation(data,folder_path,model_name,client):
    todo_items = []
    for item in data:
        if item["task"] == "poster intention":
            new_item = {}
            new_item["task"] = item["task"]
            new_item["name"] = item["name"]
            new_item["path"] = item["path"]
            new_item["local_path"] = os.path.join(folder_path, item["path"])
            new_item["prompt"] = item["prompt"]
            new_item["gt"] = item["gt"]
            image_path = os.path.join(folder_path, item["path"]) 
            if not os.path.exists(image_path):
                continue
            todo_items.append(new_item)

    prompt_templet = 'Please evaluate the generated image. If the image matches the following key information, respond only with "Yes". If it does not match, respond only with "No". Do not include any explanations or additional text. Key information: '

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(process_item_list, new_item,client,"gpt-5-2025-08-07",prompt_templet): new_item for new_item in todo_items}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing "):
            result = future.result()
    print("task_intention_generation images:",len(todo_items))
    score = compute_yes_score(todo_items)
    print("task_intention_generation score:",score)
    return todo_items,score

if __name__ == "__main__":
    client = OpenAI(
        base_url="https://xxx",
        # sk-xxx替换为自己的key
        api_key='sk-xxx'
    )

    save_dir = r".\metricIQgen"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    model_folderlist = [
        ".\image_gen_run\gemini-3-pro-image",
        ".\image_gen_run\gpt-image-1.5"
    ]
        

    
    data = read_json_file(r".\gen_task\merge.json")
    for model_folder in model_folderlist:
        model_name = model_folder.split("\\")[-1]
        print("--------------------------------")
        print(model_name)
        items_dense,score_dense = task_dense_generation(data,model_folder,model_name,client)
        items_font,score_font = task_font_generation(data,model_folder,model_name,client)
        items_style,score_style = task_style_generation(data,model_folder,model_name,client)
        items_composition,score_composition = task_composition_generation(data,model_folder,model_name,client)
        items_intention,score_intention = task_intention_generation(data,model_folder,model_name,client)
        data = items_dense + items_font + items_style + items_composition + items_intention
        save_json_file(data, os.path.join(save_dir, model_name+"_score.json"))
        
        print(f"{model_name} dense score: {score_dense:.3f}, font score: {score_font:.3f}, style score: {score_style:.3f}, composition score: {score_composition:.3f}, intention score: {score_intention:.3f}")
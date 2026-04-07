import requests
import json
from tqdm import tqdm
import os
import base64
import re
from concurrent.futures import ThreadPoolExecutor, as_completed


def read_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json_file(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def merge_json(json_list,output_dir):
    data = []
    for json_file in json_list:
        data.extend(read_json_file(json_file))
    save_json_file(data, os.path.join(output_dir, "merge.json"))
    return data

def gen_api(item,output_dir=None, model="gemini-2.5-flash-image"):
    prompt = item["prompt"]
    path = item["path"]

    output_path = os.path.join(output_dir, path)
    
    if os.path.exists(output_path):
        print(f'{output_path} already exists!')
        return item
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # replace with your own api and key
    url = "https://xxx"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-xxx"
    }
    data = {
        "extra_body": {
            "imageConfig": {
                "aspectRatio": "2:3"
            }
        },
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    }



    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_json = response.json()
        save_image_from_response(response_json, output_path)
    else:
        print(f"Error {response.status_code}: {response.text}")
        
        
def save_image_from_response(response_json, output_path):
    try:

        if 'choices' in response_json and response_json['choices']:
            message = response_json['choices'][0].get('message', {})
            
            if 'images' in message and message['images']:
                image_url = message['images'][0]['imageUrl']['url']
                if image_url.startswith('data:image'):
                    # 解析base64数据
                    base64_data = image_url.split(',')[1]
                    image_data = base64.b64decode(base64_data)
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    print(f'{output_path} saved (base64)')
                    return True
            

            content = message.get('content', '')
            url_match = re.search(r'https?://[^\s\)]+', content)
            if url_match:
                image_url = url_match.group(0)
                image_data = requests.get(image_url).content
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                print(f'{output_path} saved (URL)')
                return True
        
        if 'data' in response_json and response_json['data']:
            image_url = response_json['data'][0]['url']
            image_data = requests.get(image_url).content
            with open(output_path, 'wb') as f:
                f.write(image_data)
            print(f'{output_path} saved (URL)')
            return True
        
        print(f'{output_path} failed - no image found!')
        return False
    except Exception as e:
        print(f'{output_path} error: {e}')
        return False
    
if __name__ == "__main__":
    
    mode = "debug"

    if mode == "debug":
        prompt = "Please generate a 2:3 aspect ratio poster with the following composition: \nThis is a poster for the film. In the center is a figure shown from the upper torso up, with the outline of the shoulders and neck. The palette is predominantly cool, with teal and violet blending into a neon gradient split into three bands—left, center, and right. The central band is triangular, and the dividing lines run from the top of the head, pass through the eyes, and converge at the edge of the chin, creating an atmosphere that’s cool yet gentle, like moonlight. Three bluish‑violet light sources illuminate the face in contrast, resulting in a clean, minimalist composition.\n\nCentered at the bottom, “MOONLIGHT” appears in a glowing pale‑cyan sans‑serif type, with densely set credits beneath the title."
        output_path = r".\gemini-2.5-flash-image-4008.jpg"
        item = {
            "prompt": prompt,
            "path": output_path
        }
        gen_api(item,output_path)
        
    elif mode == "run":
        jsonlist=os.listdir(r".\gen_task")
        
        merge_json(jsonlist,r".\gen_task")
        
        for json_file in jsonlist:
            data = read_json_file(json_file)
            for item in tqdm(data):
                gen_api(item)
        

    
    # max_workers = 10
    # with ThreadPoolExecutor(max_workers=max_workers) as executor:
    #     futures = {executor.submit(api, item): item for item in data}
    #     for future in tqdm(as_completed(futures), total=len(futures), desc="Processing images"):
    #         result = future.result()
    #         print(result)
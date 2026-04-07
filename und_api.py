import os
import openai
from openai import OpenAI
import base64
from tqdm import tqdm
import time
import json
from pathlib import Path
from threading import Lock
from typing import Any
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed



_json_write_lock = Lock()

def save_json_file(
    data: Any,
    file_path: str,
    indent: int = 4,
    temp_suffix: str = ".tmp"
) -> None:
    """

    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = f"{file_path}{temp_suffix}"

    with _json_write_lock:
        try:

            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)


                f.flush()
                os.fsync(f.fileno())


            os.replace(temp_path, file_path)

        except Exception as e:
            # 出错则删除临时文件
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except OSError:
                pass
            raise RuntimeError(f"save json failed: {e}") from e

def read_json_file(file_path):
    """
    Reads a JSON file and returns the parsed data as a Python object.

    :param file_path: The path to the JSON file
    :return: The data parsed from the JSON file
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.standard_b64encode(image_file.read()).decode("utf-8")

def merge_json_lists(folder_path):
    """
    """

    json_list = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith('.json') and os.path.isfile(os.path.join(folder_path, f))
    ]

    merged_list = []

    for file_path in json_list:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    merged_list.extend(data)
                else:
                    print(f"waring: {file_path} is not list. skipped")
        except Exception as e:
            print(f"processing {file_path} error: {str(e)}")

    return merged_list


def und_api(image_path, prompt = None, model=None):
    if prompt == None:
        prompt = "What's in this image?"

    base64_image = encode_image(image_path)
    client = OpenAI(
        base_url="https://xxx",
        api_key='sk-xxx'
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                             "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    },
                ],
            }
        ],
        max_tokens=5000,
    )

    return response


def process_tasks(item,folder_path):
    if "response" in item: return None
    max_retries = 4
    retry_wait = 10
    prompt = item["prompt"]
    image_path = os.path.join(folder_path, item["path"])
    for attempt in range(max_retries):
        try:
            response = und_api(image_path, prompt, model)
            item["response"] = response.choices[0].message.content
            print(item["response"])
            save_json_file(tasks, saved_josn)
            break
        except Exception as e:
            print(f"[Warning] Request failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_wait} seconds... (attempt {attempt + 1})")
                time.sleep(retry_wait)
            else:
                print("[Error] Reached max retries. Skipping this item.")
                item["error"] = str(e)


if __name__ == "__main__":
    folder_path = r".\data"
    json_folder_path = r".\und_task"
    save_dir = r".\posterIQrun"
    model = "claude-sonnet-4-5-20250929"
    saved_josn = os.path.join(save_dir,f"{model}_bench.json")
    
    if not os.path.exists(saved_josn):
        tasks = merge_json_lists(json_folder_path)
        save_json_file(tasks, saved_josn)

    tasks = read_json_file(saved_josn)
    
    mode = "single_thread"
    
    if mode == "multi_thread":
        # multi thread mode and save json after all items
        max_threads = 20
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(process_tasks, item, folder_path) for item in tasks]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing tasks"):
                future.result()
        save_json_file(tasks, saved_josn)

    elif mode == "single_thread":
        # single thread mode and save json after each item
        max_retries = 4
        retry_wait = 10
        
        for item in tqdm(tasks):
            if "response" in item: continue

            prompt = item["prompt"]
            image_path = os.path.join(folder_path, item["path"])
            for attempt in range(max_retries):
                try:
                    response = und_api(image_path, prompt, model)
                    item["response"] = response.choices[0].message.content
                    print(item["response"])
                    save_json_file(tasks, saved_josn)
                    break
                except Exception as e:
                    print(f"[Warning] Request failed: {e}")
                    if attempt < max_retries - 1:
                        print(f"Retrying in {retry_wait} seconds... (attempt {attempt + 1})")
                        time.sleep(retry_wait)
                    else:
                        print("[Error] Reached max retries. Skipping this item.")
                        item["error"] = str(e)





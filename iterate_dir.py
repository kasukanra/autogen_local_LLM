import os
from dotenv import load_dotenv
import string
import base64
import requests
import imghdr
import cv2
from PIL import Image
from detect_utils import best_crop, presets

# Load variables from .env file
load_dotenv()

import openai

# Access the variables
work_dir = os.getenv("WORK_DIR")
upscale_dataset = os.getenv("UPSCALE_DATASET")
final_dataset = os.getenv("FINAL_DATASET")
trigger_word = os.getenv("TRIGGER_WORD")
model = os.getenv("MODEL")
local_llava_cpp_api = os.getenv("LOCAL_LLAVA_CPP_API")

# Define paths
current_dir = os.getcwd()
dataset_path = os.path.join(work_dir, upscale_dataset)
final_dataset_path = os.path.join(work_dir, final_dataset)

# Print current settings
print("current working directory: ", current_dir)
print("this is dataset_path", dataset_path)

# Define headers and task
headers = {"Content-Type": "application/json"}
task = "please describe this image in as much detail as possible."
instruction = "please rephrase this so that it is a description separated by ONLY commas and NO periods: {}"

def save_progress(img_id):
    with open("progress.txt", "w") as f:
        f.write(str(img_id))

def load_progress():
    try:
        with open("progress.txt", "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def describe_image_cpp(file_path, img_id):
    with open(file_path, 'rb') as f:
        img_bytes = f.read()
        img_format = imghdr.what(None, img_bytes)
        img_str = base64.b64encode(img_bytes).decode('utf-8')

        image_data = [{"data": img_str, "id": img_id}]
        prompt = f"USER:[img-{img_id}]{task}\nASSISTANT:"

        payload = {
            "prompt": prompt, 
            "n_predict": 4096,
            "temperature": 0.1,
            "image_data": image_data
        }

        response = requests.post(local_llava_cpp_api, headers=headers, json=payload)
        json_data = response.json()

        description = json_data["content"]
        print("this is description cpp", description)
        return description

def get_response_text(instruction):
    response = openai.ChatCompletion.create(
        model=model, 
        messages=[{"role": "user", "content": f"### Instruction: {instruction}.\n###Response: "}],
        stop=["### Instruction:"],
        temperature=0.1,
        max_tokens=-1,
        stream=False
    )

    response_data = response.choices[0].message.content
    cleaned_content = (response_data.replace('.', ',')
                                     .replace(';', ',')
                                     .replace(':', ',')
                                     .replace('(', ',')
                                     .replace(')', ',')
                                     .replace(' - ', ', '))
    if cleaned_content and cleaned_content[-1] in string.punctuation:
        cleaned_content = cleaned_content[:-1]

    return f"{trigger_word}, {cleaned_content}"

def save_image_and_text(img_path, description_text, presets):
    dir_name = os.path.basename(os.path.dirname(img_path))
    new_dir_path = os.path.join(work_dir, final_dataset, dir_name)
    
    if not os.path.exists(new_dir_path):
        os.makedirs(new_dir_path)
    
    existing_files = [name for name in os.listdir(new_dir_path) if os.path.isfile(os.path.join(new_dir_path, name))]
    new_file_index = len(existing_files) // 2 + 1
    
    file_ext = os.path.splitext(img_path)[1]
    if file_ext not in ['.jpg', '.jpeg', '.png']:
        raise ValueError(f"Unsupported file format: {file_ext}")
    
    new_img_name = f"{dir_name}_{str(new_file_index).zfill(2)}{file_ext}"
    new_img_path = os.path.join(new_dir_path, new_img_name)
    
    processed_img, best_preset = best_crop(img_path, presets)
    print("this is the best_preset", best_preset)
    cv2.imwrite(new_img_path, processed_img)
    
    new_txt_name = f"{dir_name}_{str(new_file_index).zfill(2)}.txt"
    new_txt_path = os.path.join(new_dir_path, new_txt_name)
    
    with open(new_txt_path, 'w') as f:
        f.write(description_text)
    
    print(f"Image saved to: {new_img_path}")
    print(f"Description saved to: {new_txt_path}")

def batch_process_images():
    # Load the last processed image ID
    last_processed_id = load_progress()

    img_id = 0
    # Batch process
    for dirpath, dirnames, filenames in os.walk(dataset_path):
        dirnames.sort()  # Sort the directories in-place
        if dirpath != dataset_path:
            print("Current directory:", dirpath)
        
            for filename in sorted(filenames):  # Sort the filenames
                file_path = os.path.join(dirpath, filename)
                img_id += 1

                if img_id <= last_processed_id:
                    print(f"Skipping {file_path} (ID: {img_id}) as it has been processed before.")
                    continue

                try:
                    description = describe_image_cpp(file_path, img_id)
                    embedded_instruction = instruction.format(description)
                    response_text = get_response_text(embedded_instruction)
                    print("this is response_text", response_text)
                    save_image_and_text(file_path, response_text, presets)
                    save_progress(img_id)

                except Exception as e:
                    print(f"An error occurred while processing {file_path} (ID: {img_id}): {e}")

if __name__ == "__main__":
    batch_process_images()
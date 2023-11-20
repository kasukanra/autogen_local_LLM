import os
from dotenv import load_dotenv
import base64
import requests
import imghdr
import replicate

# Load variables from .env file
load_dotenv()

# Access the variables
email_address = os.getenv("EMAIL_ADDRESS")
password = os.getenv("PASSWORD")
work_dir = os.getenv("WORK_DIR")
temp_dataset = os.getenv("TEMP_DATASET")
local_vision_api = os.getenv("LOCAL_VISION_API")
preset = os.getenv("PRESET")
replicate_api_key = os.getenv("REPLICATE")

# Declare replicate api_key
os.environ["REPLICATE_API_TOKEN"] = replicate_api_key


print("this is local_api", local_vision_api)
current_dir = os.getcwd()
print("current working directory: ", current_dir)

dataset_path = os.path.join(work_dir, temp_dataset)
print("this is dataset_path", dataset_path)


CONTEXT = "You are LLaVA, a large language and vision assistant trained by UW Madison WAIV Lab. You are able to understand the visual content that the user provides, and assist the user with a variety of tasks using natural language. Follow the instructions carefully and explain your answers in detail.### Human: Hi!### Assistant: Hi there! How can I help you today?\n"

api_endpoint = local_vision_api + "/generate"

task = "please describe this image as accurately and objectively as possible. there should be no complete sentences. the description should start with describing the overall image structure, starting with the camera perspective and view. it should then describe the features of the person such as hair color, eye color, expression, and pose. afterwards, it should describe the clothing and its corresponding colors. lastly, the background should be described. if the image is blurry or grainy, that should be added at the very end."

# task = "please describe this image in as much detail as possible."

# first_iteration_result = None

# Iterate through each subdirectory in the search directory
# for dirpath, dirnames, filenames in os.walk(dataset_path):
#     if dirpath != dataset_path:  # Skip the initial directory
#         # Print the current directory name
#         print("Current directory:", dirpath)
    
#         for filename in filenames:
#             # Print the name of each file
#             file_path = os.path.join(dirpath, filename)
#             print(file_path)

#             if first_iteration_result is None:
#                 first_iteration_result = file_path

# print("this is first_iteration_result", first_iteration_result)


def describe_image_replicate(img_path):
    output = replicate.run(
        "yorickvp/llava-13b:6bc1c7bb0d2a34e413301fee8f7cc728d2d4e75bfab186aa995f63292bda92fc",
        input={
            "image": open(img_path, "rb"),
            "prompt": task,
            "temperature": 0.2
        }
    ) 

    result = ""
    for item in output:
        result += item

    return result

index_to_get = 2  # 0-based index, so 1 will get the second file

file_counter = 0
desired_file_path = None

for dirpath, dirnames, filenames in os.walk(dataset_path):
    if dirpath != dataset_path:  # Skip the initial directory
        # Print the current directory name
        print("Current directory:", dirpath)
    
        for filename in filenames:
            # Print the name of each file
            file_path = os.path.join(dirpath, filename)
            print(file_path)

            if file_counter == index_to_get:
                desired_file_path = file_path
                break  # break out of the inner loop when the desired file is found
            
            file_counter += 1

        if desired_file_path:  # If the desired file is found, break out of the outer loop
            break

print("this is desired_file_path", desired_file_path)

result = describe_image_replicate(desired_file_path)
print("this is replicate description")
print(result)

# def describe_image(file_path):
#     with open(file_path, 'rb') as f:
#         img_bytes = f.read()
#         img_format = imghdr.what(None, img_bytes)
        
#         # print(f"Detected image format: {img_format}")

#         img_str = base64.b64encode(img_bytes).decode('utf-8')
#         img_data_uri = f"data:image/{img_format};base64,{img_str}"

#         prompt = CONTEXT + f'### Human: {task} \n<img src="{img_data_uri}">### Assistant: '

#         payload = {
#             'prompt': prompt,
#             'stopping_strings': ['\n###'],
#             'preset': preset 
#         }

#         response = requests.post(api_endpoint, json=payload)
#         json_data = response.json()

#         result_text = json_data['results'][0]['text']
#         print(result_text)

# # Iterate through each subdirectory in the search directory
# for dirpath, dirnames, filenames in os.walk(dataset_path):
#     if dirpath != dataset_path:  # Skip the initial directory
#         # Print the current directory name
#         print("Current directory:", dirpath)
    
#         for filename in filenames:
#             # Print the name of each file
#             file_path = os.path.join(dirpath, filename)
#             print(file_path)

#             # Call the describe_image function
#             describe_image(file_path)

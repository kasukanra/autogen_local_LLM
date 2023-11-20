import autogen
from selenium import webdriver
from bs4 import BeautifulSoup
import requests
import time
import os
import io
from PIL import Image
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

from pinterest_utils import fetch_image

# Load variables from .env file
load_dotenv()

# Access the variables
work_dir = os.getenv("WORK_DIR")
print("this is work_dir", work_dir)

config_list = autogen.config_list_from_json(env_or_file="OAI_CONFIG_LIST.json")
# config_list = autogen.config_list_from_json(env_or_file="OAI_CONFIG_LIST_LLM.json")

llm_config = {
    "request_timeout": 600,
    "seed": 50,
    "config_list": config_list,
    "temperature": 0,
    "functions":[
        {
            "name": "fetch_image",
            "description": "Queries Pinterest with a search string then downloads the imaages into the corresponding folder",
            "parameters": {
                "type": "object",
                "properties": {
                    "var": {
                        "type": "string",
                        "description": "The query string to be used."
                    }
                },
                "required": ["var"]
            }
        }
    ]
}

# you can have a default_auto_reply here
user_proxy = autogen.UserProxyAgent(
    name="Admin",
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "work_dir": work_dir,
        "use_docker": False
    },
    system_message="""Reply TERMINATE if the task has been solved at full satisfaction. Otherwise, reply CONTINUE, or the reason why the task is not solved yet."""
)

# agents
technical_engineer = autogen.AssistantAgent(
    name="Technical_Engineer",
    llm_config=llm_config,
    system_message="""You are a Technical Engineer. You will execute fetch_image function to download images. You will receive queries from the Prompt_Engineer that you must carry out. You will execute function calls sequentially and in order. You cannot procede to the next query without finishing execution of your current query. Once you are finished, speak with Prompt_Engineer to get the next prompt, then execute it.

    If there is only a single query in the list from Prompt Engineer, then you are finished after executing that single query.
    """,
    function_map={
        "fetch_image": fetch_image
    },
    code_execution_config=False
)

prompt_engineer = autogen.AssistantAgent(
    name="Prompt_Engineer",
    llm_config=llm_config,
    system_message="""You are a Prompt Engineer. Generate a list of search queries relative to the task at hand. For now, I only need 10 search queries. Out of the 10 search queries, 8 queries should be of human beings with 5 of them being female and 3 of them being male. The remaining two queries must be related to realistic architecture of buildings designs and inspirational fashion outfits. 
    
    Revise the list based on feedback from admin. You MUST GET admin approval before proceeding.
    
    The queries will then be passed to the Technical Engineer who will execute the code given to it on each of the search queries.
    """
)

# start the "group chat" between agents and humans
groupchat = autogen.GroupChat(
    agents=[user_proxy, technical_engineer, prompt_engineer], 
    messages=[], 
    max_round=50
)

manager = autogen.GroupChatManager(
    groupchat=groupchat, 
    llm_config=llm_config
)

task="""
    I want you to create a dataset of images from the website pinterest. 
    I would like the images to focus on pretty beautiful Asian females and handsome Asian males. Please focus on idols, celebrities, and fashion models. I also want a small amount of realistic architecture designs and inspirational fashion outfits.
"""
# Start the Chat!
user_proxy.initiate_chat(
    manager,
    message=task
)
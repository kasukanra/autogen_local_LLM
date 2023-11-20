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

load_dotenv()

email_address = os.getenv("EMAIL_ADDRESS")
password = os.getenv("PASSWORD")
work_dir = os.getenv("WORK_DIR")
temp_dataset = os.getenv("TEMP_DATASET")

def save_soup_to_file(soup, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(str(soup.prettify()))

def transform_link_to_original(link):
    return link.replace("/236x/", "/originals/")

def verify_and_remove_corrupted_image(filename):
    try:
        with Image.open(filename) as im:
            im.verify()
    except:
        print(f"Corrupted image detected and deleted: {filename}")
        os.remove(filename)

def login_to_pinterest(driver, email_address, password):
    wait = WebDriverWait(driver, 3)  # waits up to 10 seconds
    loginButton = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-id='login-button']")))
    # loginButton = driver.find_element(By.CSS_SELECTOR, "div[data-test-id='login-button']")
    loginButton.click()
    time.sleep(1)

    email_elem = driver.find_element(By.ID, "email")
    email_elem.send_keys(email_address)

    password_elem = driver.find_element(By.ID, "password")
    password_elem.send_keys(password)

    redLoginButton = driver.find_element(By.CLASS_NAME, "SignupButton")
    redLoginButton.click()
    time.sleep(3)

def fetch_image(var):
    # try:
    #     os.chdir(os.path.join(os.getcwd(), 'images'))
    # except:
    #     pass

    # Replace spaces in 'var' with underscores and use it as directory name
    dir_name = var.replace(" ", "_")

    dataset_path = os.path.join(work_dir, temp_dataset)

    print("this is dataset_path", dataset_path)
    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

    # Make the directory under 'dataset' folder
    full_path = os.path.join(dataset_path, dir_name)
    print("this is full_path", full_path)

    # Create the directory if it doesn't exist
    if not os.path.exists(full_path):
        os.makedirs(full_path)

    # original working directory
    original_cwd = os.getcwd()
    # Change the current working directory to the newly created/identified directory
    os.chdir(full_path)
    
    scroll_num=3
    sleep_timer=3
    url=f'https://pinterest.com/search/pins/?q={var}'

    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    # options.add_argument("--headless") 
    driver = webdriver.Chrome(executable_path='/usr/bin/chromedriver', options=options)
    driver.get(url)

    time.sleep(3)

    # Login to Pinterest
    # login_to_pinterest(driver, email_address, password)
    # driver.get(url)  # Reload page after login

    for _ in range(1, scroll_num):
        driver.execute_script("window.scrollTo(1,1000000)")
        print('scroll-down')
        time.sleep(sleep_timer)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # save_soup_to_file(soup, 'pinterest_page.html')

    for link in soup.findAll('img'):
        src_link = link.get('src')
        if "i.pinimg.com" not in src_link:
            continue

        original_link = transform_link_to_original(src_link)
        image_filename = original_link.strip('https://i.pinimg.com/originals/ad/ea/a1.jpg').replace('/', '_') + '.png'
        
        # Fetch the image
        im = requests.get(original_link)

        # Check the response status and content type
        if im.status_code != 200 or 'image' not in im.headers.get('content-type', ''):
            print(f"Invalid response for link: {original_link}")
            continue

        # Use PIL's Image to check dimensions and handle potential errors
        try:
            image = Image.open(io.BytesIO(im.content))
            width, height = image.size
        except IOError:
            print(f"Unable to process the image from link: {original_link}")
            continue

        if width >= 512 and height >= 512:  # Only save images that are 512x512 or larger
            with open(image_filename, 'wb') as f:
                f.write(im.content)
            verify_and_remove_corrupted_image(image_filename) 

    os.chdir(original_cwd)
    driver.quit()

    return

def fetch_images_from_pinterest(query):
    fetch_image(query)

if __name__ == "__main__":
    query = "bts taehyung"
    fetch_images_from_pinterest(query)
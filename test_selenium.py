from selenium import webdriver
import time

def open_browser_and_navigate():
    # Set up Chrome options
    options = webdriver.ChromeOptions()
    # This line is optional, it will open Chrome in headless mode (without GUI)
    # options.add_argument("--headless")

    # Open a new instance of Chrome
    browser = webdriver.Chrome(options=options)

    # Navigate to a website
    browser.get("https://www.google.com")

    # Print the title (for verification)
    print(browser.title)
    
    # Keep the browser open for 10 seconds
    time.sleep(10)
    
    # Close the browser
    browser.quit()

if __name__ == "__main__":
    open_browser_and_navigate()

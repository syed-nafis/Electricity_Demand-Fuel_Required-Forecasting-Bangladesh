from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import time

# Define your desired download directory (replace with your actual folder path)
# Change this to the folder where files should be saved
download_dir = " "

# Set up Chrome options
options = webdriver.ChromeOptions()

prefs = {
    "download.default_directory": download_dir,  # Sets the download directory
    "download.prompt_for_download": False,  # Disables the download prompt
    "directory_upgrade": True,
    "safebrowsing.enabled": True  # Disable safe browsing protection for automated download
}
options.add_experimental_option("prefs", prefs)
options.add_argument('--headless')
options.add_argument('--disable-gpu')

# Initialize the Chrome WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Navigate to the webpage
driver.get("https://erp.pgcb.gov.bd/w/report/eyJpdiI6Ik53OTZRKzRRTVoxUUY4a3RMb250Y0E9PSIsInZhbHVlIjoiQmxnNjFqUUROVnk2RFh1OHJ0NGVkQT09IiwibWFjIjoiZDBlYmM3ZTUzMzBkNDM4NTNkZDQxYjc0YTc2NDQ3YTYzYmY1MjRjNDRjNTQ2MmQwOGM5MzY4MGRjNTIwYTFlYiIsInRhZyI6IiJ9/show_report")

actions = ActionChains(driver)

time.sleep(5)  # Wait for page to load

# Function to scroll to the bottom of the page to load all 30 files
def scroll_page():
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # Wait for new content to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

# Function to download files from the current page
def download_files(action):
    download_links = driver.find_elements(By.TAG_NAME, 'a')
    for link in download_links:
        file_url = link.get_attribute('href')
        if(file_url is None):
            continue
        if 'download' in file_url:
            print(f"Downloading file from {file_url}")
            actions.move_to_element(link).click().perform()
            time.sleep(2)  # Pause for download to start

# Loop through all pages (assume 132 pages)
for page in range(1, 133):
    print(f"Processing page {page}")
    
    # Scroll to load all files on the current page
    scroll_page()
    
    # Download all files on the current page
    download_files(actions)
    
    # Find and click the "Next" button to go to the next page (adjust the selector based on your page structure)
    try:
        print(f"in page {page}")
        # Wait until the "Next" button is clickable
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//a[@class="page-link" and @rel="next"]'))
        )
        # Or if you prefer using the href directly:
        next_page_url = next_button.get_attribute('href')
        driver.get(next_page_url)  # Navigate to the next page using the URL
        time.sleep(5)  # Wait for the next page to load
        print(f"going to next page {page}")
    except:
        print("No more pages.")
        break

# Close the driver
driver.quit()
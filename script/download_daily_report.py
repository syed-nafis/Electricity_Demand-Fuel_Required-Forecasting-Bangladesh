import os
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from urllib.parse import urlparse

import time

# Define your desired download directory (replace with your actual folder path)
# Change this to the folder where files should be saved
path = " "
last_page_number = 133  # Default last page number if not provided

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Download daily reports from PGCB")
    parser.add_argument("--path", help="Path to the directory where the downloaded files would be saved")
    parser.add_argument("--last_page_number", help="last Page number till you want to download the files", type=int, default=132)

    args = parser.parse_args()

    path = args.path if args.path else path  # Default path if not provided
    last_page_number = args.last_page_number if args.last_page_number else last_page_number

    print(f"Downloading files in {path}...")

    # Set up Chrome options
    options = webdriver.ChromeOptions()

    # Define your desired download directory (replace with your actual folder path)
    download_dir = path  # Change this to the folder where files should be saved
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
    driver.get("https://erp.powergrid.gov.bd/w/report/eyJpdiI6IldsU2ZQTGkvbkRnQU9FMjZ5UHhmeGc9PSIsInZhbHVlIjoiQzhONVl5ZGxRY3E3T3ZVNCtLZGt1Zz09IiwibWFjIjoiN2JiNTI5MzNhOWIxZDVjY2NkMmFlZWU4ZDU1N2I4OWZlYjNlZWM1ZGU4NzRiNWU4ZjQ3ZDc1ODRlMTk3MDc0YyIsInRhZyI6IiJ9/show_report")

    actions = ActionChains(driver)

    time.sleep(5)  # Wait for page to load

    # Get the list of existing files in the download directory
    existing_files = set(os.listdir(download_dir))

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
                # Extract the file name from the URL
                file_name = os.path.basename(urlparse(file_url).path)

                # Check if the file already exists
                if file_name in existing_files:
                    print(f"File already exists: {file_name}. Skipping download.")
                    continue
                
                # Download the file
                print(f"Downloading file: {file_name} from {file_url}")
                action.move_to_element(link).click().perform()
                time.sleep(2)  # Pause for download to start
                existing_files.add(file_name)  # Add the file to the existing list

    # Loop through all pages (assume 132 pages)
    for page in range(1, last_page_number):
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
        except Exception as e:
            print(f"No more pages or error: {e}")
            break

    # Close the driver
    driver.quit()
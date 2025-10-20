import os
import argparse
from config import base_url
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs
import time

def get_last_page_number(driver, base_url):
    """
    Retrieves the last page number from the pagination.
    """
    driver.get(base_url)
    time.sleep(1)  # Wait for page to load
    pagination_links = driver.find_elements(By.CSS_SELECTOR, "a.page-link")
    if not pagination_links:
        return 1  # Return 1 if no pagination links are found
    last_page_link = pagination_links[-2]
    
    if last_page_link.text:
        last_page_number = int(last_page_link.text)
    else:
        print("Last page link has no text; defaulting to 1")
        return 1 # Return 1 if the last page link has no text
    return last_page_number

def setup_selenium_driver(download_dir, headless=True):
    """
    Sets up the Selenium Chrome WebDriver with specified download directory and options.
    """
    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    if headless:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def scroll_page(driver):
    """
    Scrolls to the bottom of the page to load all content.
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # Wait for new content to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def download_files(action, driver, existing_files):
    """
    Downloads files from the current page, skipping existing files.
    """
    download_links = driver.find_elements(By.TAG_NAME, 'a')
    for link in download_links:
        file_url = link.get_attribute('href')
        if file_url and 'download' in file_url:
            # Extract the filename from the URL's "title" parameter
            parsed_url = urlparse(file_url)
            query_params = parse_qs(parsed_url.query)
            title = query_params.get('title', [None])[0]
            if title:
                file_name = title + ".xlsx"  # Append the .xlsx extension
            else:
                file_name = "unknown_file.xlsx"  # Handle cases where the title is missing

            if file_name in existing_files:
                print(f"File already exists: {file_name}. Skipping download.")
                continue
            print(f"Downloading file: {file_name} from {file_url}")
            action.move_to_element(link).click().perform()
            time.sleep(5)  # Pause for download to start
            existing_files.add(file_name)

def navigate_to_next_page(driver, page):
    """
    Navigates to the next page using the 'Next' button.
    """
    try:
        print(f"in page {page}")
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//a[@class="page-link" and @rel="next"]'))
        )
        next_page_url = next_button.get_attribute('href')
        driver.get(next_page_url)  # Navigate to the next page using the URL
        time.sleep(5)  # Wait for the next page to load
        print(f"going to next page {page}")
        return True  # Successfully navigated to the next page
    except Exception as e:
        print(f"No more pages or error: {e}")
        return False  # Failed to navigate to the next page

def selenium_downloader(base_url, path, last_page_number):
    """
    Main function to orchestrate the download process.
    """
    download_dir = os.path.join(path, "daily_reports")
    os.makedirs(download_dir, exist_ok=True)

    driver = setup_selenium_driver(download_dir)
    actions = ActionChains(driver)
    driver.get(base_url)
    time.sleep(5)

    existing_files = set(os.listdir(download_dir))

    if not last_page_number:
        last_page_number = get_last_page_number(driver, base_url)

    print(f"Downloading files in {download_dir}...")
    print(f"Downloading files up to page number: {last_page_number}")

    for page in range(1, last_page_number):
        print(f"Processing page {page}")
        scroll_page(driver)
        download_files(actions, driver, existing_files)
        if not navigate_to_next_page(driver, page):
            break

    driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download daily reports from PGCB")
    parser.add_argument("--path", help="Path to the directory where the downloaded files would be saved")
    parser.add_argument("--last_page_number", help="Last page number to download files from", type=int)
    parser.add_argument("--base_url", help="Base URL of the daily_reports", default=base_url)

    args = parser.parse_args()

    path = args.path + "/" if args.path else os.getcwd()
    last_page_number = args.last_page_number
    base_url = args.base_url

    selenium_downloader(base_url, path, last_page_number)
import os
import bs4
import time
import requests
import argparse
from config import base_url
from urllib.parse import urlparse, parse_qs


def get_last_page_number(soup):

    # Find the pagination section
    pagination = soup.find('ul', class_='pagination')
    if not pagination:
        return 1  # If no pagination found, assume only one page

    # Find all page number links
    page_links = pagination.find_all('a')
    page_numbers = []

    for link in page_links:
        try:
            page_num = int(link.text)
            page_numbers.append(page_num)
        except ValueError:
            continue  # Ignore non-numeric links

    return max(page_numbers) if page_numbers else 1

def get_file_extension(file_url):

    if '.xlsx' in file_url: return '.xlsx'
    elif '.xls' in file_url:    return  '.xls'
    else:   return '.xlsx'
    

def download_file(file_url, download_dir, title=None):
    
    extension = get_file_extension(file_url)

    if title:
        file_name = os.path.join(download_dir, title + extension)  # Add .xlsx extension
    else:
        file_name = os.path.join(download_dir, "unknown" + extension)  # Handle missing title

    print(f"Downloading {file_url}...")
    try:
        file_response = requests.get(file_url, verify=False, stream=True)  # Use stream=True
        file_response.raise_for_status()  # Check for HTTP errors

        with open(file_name, 'wb') as file:  # Open in binary write mode
            for chunk in file_response.iter_content(chunk_size=8192):  # Iterate over data in chunks
                file.write(chunk)
        print(f"Saved to {file_name}")

    except requests.exceptions.RequestException as e:
        print(f"Download failed for {file_url}: {e}")
    except Exception as e:
        print(f"Error saving file {file_name}: {e}")


def download_files_from_page(url, download_dir, soup):
    # Find all anchor tags on the page
    anchor_tags = soup.find_all('a', href=lambda href: href and "https://erp.powergrid.gov.bd/web/files/download" in href)

    # Iterate through all anchor tags and download files
    for tag in anchor_tags:
        href = tag.get('href')
        if href:
            file_url = href
            parsed_url = urlparse(file_url)
            query_params = parse_qs(parsed_url.query)
            title = query_params.get('title', [None])[0]  # Get the title from the URL
            download_file(file_url, download_dir, title)


def process_page(page_url, download_dir):

    print(f"Processing page {page_url}")

    try:
        response = requests.get(page_url, verify=False)
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        download_files_from_page(page_url, download_dir, soup)
        time.sleep(1)  # Be polite and wait a second

    except requests.exceptions.RequestException as e:
        print(f"Error accessing page {page_url}: {e}")
    except Exception as e:
        print(f"Error processing page {page_url}: {e}")


def bs4_downloader(base_url, path, last_page_number=None):

    # Send a GET request to the webpage
    response = requests.get(base_url, verify = False)
    response.raise_for_status()  # Check if the request was successful

    # Parse the HTML content using BeautifulSoup
    soup = bs4.BeautifulSoup(response.text, 'html.parser')

    
    if last_page_number is None:
        last_page_number = get_last_page_number(soup)
    print(f"Downloading files in {path}...")
    print(f"Downloading files up to page number: {last_page_number}")

    # Create a directory to save downloaded files if it doesn't exist
    download_dir = os.path.join(path, "daily_reports")
    os.makedirs(download_dir, exist_ok=True)

    # Loop through all pages and download files
    starting_page_number = int(base_url.split("page=")[-1]) if "page=" in base_url else 1
    for page_num in range(starting_page_number, last_page_number + 1):
        page_url = base_url.split("page=")[0] + "page=" + str(page_num)
        process_page(page_url, download_dir)


if __name__ == "__main__":
    # Set the URL of the webpage containing the links
    parser = argparse.ArgumentParser(description="Download daily reports from PGCB using BeautifulSoup")
    parser.add_argument("--path", help="Path to the directory where the downloaded files would be saved")
    parser.add_argument("--last_page_number", help="last Page number till you want to download the files", type=int)
    parser.add_argument("--base_url", help="Base URL of the daily_reports", default=base_url)
    args = parser.parse_args()  # Parse the arguments here!

    path = args.path + "/" if args.path else os.getcwd()
    last_page_number = args.last_page_number
    base_url = args.base_url

    bs4_downloader(base_url, path, last_page_number)
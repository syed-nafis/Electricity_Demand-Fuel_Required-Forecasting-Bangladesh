import os
import argparse
from config import base_url
from bs4_downloader import bs4_downloader
from selenium_downloader import selenium_downloader

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download daily reports from PGCB")
    parser.add_argument("--path", help="Path to the directory where the downloaded files would be saved")
    parser.add_argument("--last_page_number", help="Last page number to download files from", type=int)
    parser.add_argument("--sele", help="Choose downloader: selenium or bs4", choices=["selenium", "bs4"], default="bs4")
    #selenium commandline option
    parser.add_argument("--csv", action="store_true", help="use bs4 downloader")
    parser.add_argument("--selenium", action="store_true", help="use selenium downloader")

    args = parser.parse_args()

    path = args.path + "/" if args.path else os.getcwd()
    last_page_number = args.last_page_number
    base_url = args.base_url
    
    if args.bs4:
        print("Using BeautifulSoup downloader : ")
        bs4_downloader(base_url, path, last_page_number)
    if args.selenium:
        print("Using Selenium downloader : ")
        selenium_downloader(base_url, path, last_page_number)
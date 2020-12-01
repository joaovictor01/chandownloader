import requests
from bs4 import BeautifulSoup
import json
import wget
import os
import pathlib
import sys

thread_number = ""

# Create an Image Folder for the media of the thread to be stored
def create_img_folder(url):
    global thread_number
    board = url.split("/")[3]
    thread_number = str(url.split("thread/")[1])
    path = f'4chan/{board}/{thread_number}'
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    return path


def download_all(url,path):
    global thread_number
    r = requests.get(url, verify=False)
    soup = BeautifulSoup(r.content, 'html.parser')
    divMedia = soup.find_all("div", {"class": "fileText"})

    # Download all media files from the thread
    for tag in divMedia:
        hrefTag = tag.find_all("a")
        for media in hrefTag:
            try:
                filename = media["href"].split("/")[-1].strip()
                wget.download("https:"+media["href"],
                              f"{path}/{filename}")
            except Exception as e:
                print(e)
                print("Failed to download.")


def main():
    url = input("Insert the thread link here: ")
    path = create_img_folder(url)
    try:
        download_all(url,path)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()

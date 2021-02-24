import requests
from bs2json import bs2json
from bs4 import BeautifulSoup
import json
import wget
import os
from pathlib import Path
import sys
import urllib.request, urllib.error, urllib.parse

thread_number = ""

# Create an Image Folder for the media of the thread to be stored
def create_img_folder(url):
    global thread_number
    board = url.split("/")[3]
    thread_number = str(url.split("thread/")[1])
    path = Path.joinpath(Path.home(), f'4chan/{board}/{thread_number}')
    Path(path).mkdir(parents=True, exist_ok=True)
    print(f'\nCaminho da pasta criada é: {path}')
    return path


def download_thread_json(url, path):
    thread_json_url = f"{url.replace('boards.4chan','a.4cdn')}.json"
    print(thread_json_url)
    wget.download(thread_json_url, str(path))
    print("Thread's json downloaded successfully!")

def download_all(url, path):
    global thread_number
    r = requests.get(url, verify=False)
    soup = BeautifulSoup(r.content, 'html.parser')
    divMedia = soup.find_all("div", {"class": "fileText"})
    # Download a json of the threads
    try:
        webpage_path = Path.joinpath(path, 'webpage')
        Path(webpage_path).mkdir(parents=True, exist_ok=True)
        thread_json_path = Path.joinpath(webpage_path, 'thread.json')
        download_thread_json(url, thread_json_path)
    except Exception as e:
        print(e)

    try:
        # Download the html of the page
        response = urllib.request.urlopen(url)
        web_content = response.read()
        with open(Path.joinpath(path, 'webpage/index.html'), 'wb') as f:
            f.write(web_content)
    except Exception as e:
        print(e)

    # Download all media files from the thread
    for tag in divMedia:
        hrefTag = tag.find_all("a")
        for media in hrefTag:
            try:
                filename = media.text.strip()
                if not os.path.isfile(f"{path}/{filename}"):
                    print(f"\nDownloading {filename}")
                    wget.download("https:"+media["href"], f"{path}/{filename}")
                else:
                    print("\nThis file already exists, continuing...")
            except Exception as e:
                print(e)
                print("\nFailed to download.")


def main():
    url = input("Insert the thread link here: ")
    path = create_img_folder(url)
    download_all(url,path)


if __name__ == "__main__":
    main()

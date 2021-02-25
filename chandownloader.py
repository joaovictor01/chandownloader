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

def get_json_url(url):
    if '4channel' in url:
        return f"{url.replace('boards.4channel','a.4cdn')}.json"
    else:
        return f"{url.replace('boards.4chan','a.4cdn')}.json"


def get_thread_title(url):
    print(url)
    thread_json_url = get_json_url(url)
    print(thread_json_url)
    r = requests.get(thread_json_url, verify=False)
    thread_json = r.json()
    thread_title = thread_json['posts'][0]['semantic_url']
    return thread_title


# Create an Image Folder for the media of the thread to be stored
def create_img_folder(url, thread_title):
    global thread_number
    board = url.split("/")[3]
    thread_number = str(url.split("thread/")[1])
    path = Path.joinpath(Path.home(), f'4chan/{board}/{thread_title}__{thread_number}')
    Path(path).mkdir(parents=True, exist_ok=True)
    print(f'\nPath of created folder is: {path}')
    return path


def download_thread_json(url, path):
    thread_json_url = get_json_url(url)
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
    thread_title = get_thread_title(url)
    path = create_img_folder(url, thread_title)
    download_all(url, path)


if __name__ == "__main__":
    main()

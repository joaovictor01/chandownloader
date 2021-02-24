import requests
from bs2json import bs2json
from bs4 import BeautifulSoup
import json
import wget
import os
import pathlib
import sys
import urllib.request, urllib.error, urllib.parse

thread_number = ""

# Create an Image Folder for the media of the thread to be stored
def create_img_folder(url):
    global thread_number
    board = url.split("/")[3]
    thread_number = str(url.split("thread/")[1])
    path = pathlib.Path.joinpath(pathlib.Path.home(), f'4chan/{board}/{thread_number}')
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    print(f'\nCaminho da pasta criada é: {path}')
    return path


def download_all(url,path):
    global thread_number
    r = requests.get(url, verify=False)
    soup = BeautifulSoup(r.content, 'html.parser')
    divMedia = soup.find_all("div", {"class": "fileText"})

    # Download a json of the threads
    try:
        pathlib.Path(path+'/webpage').mkdir(parents=True, exist_ok=True)
        html = r.text
        soup2 = BeautifulSoup(html,'lxml')
        converter = bs2json()
        th = soup2.select('.thread')[0]
        json_thread = converter.convert(th)
        with open(path + '/webpage/thread.json', 'w+') as thread_file:
            json.dump(json_thread, thread_file)
    except Exception as e:
        print(e)

    # Download the html of the page
    try:
        response = urllib.request.urlopen(url)
        web_content = response.read()
        with open(path + '/webpage/index.html', 'wb') as f:
            f.write(web_content)
    except Exception as e:
        print(e)

    # Download all media files from the thread
    for tag in divMedia:
        hrefTag = tag.find_all("a")
        for media in hrefTag:
            try:
                filename = media["href"].split("/")[-1].strip()
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

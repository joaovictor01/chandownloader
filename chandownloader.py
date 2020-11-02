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
    thread_number = str(url.split("thread/")[1])
    pathlib.Path(f'./{thread_number}').mkdir(parents=True, exist_ok=True)


def download_imgs(url):
    global thread_number
    r = requests.get(url, verify=False)
    soup = BeautifulSoup(r.content, 'html.parser')
    img_links_vector = soup.find_all("img")

    for img_link in img_links_vector:
        img_link = "https:"+img_link["src"]
        img_title = img_link.split("/")[-1]
        # download the images
        try:
            wget.download(img_link, f"./{thread_number}/{img_title}")
        except Exception as e:
            print("Erro ao fazer download")


def download_all(url):
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
                              f"./{thread_number}/{filename}")
            except Exception as e:
                print(e)
                print("Failed at downloading")


def main():
    url = input("Insert the thread link here: ")
    create_img_folder(url)
    try:
        download_all(url)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()

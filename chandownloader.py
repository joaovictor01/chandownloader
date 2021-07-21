import requests
import json
import wget
import os
import sys
import urllib3.request
import urllib.error
import urllib.parse
import time
import threading
from bs2json import bs2json
from bs4 import BeautifulSoup
from pathlib import Path
from utils import bcolors, setInterval


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

THREAD_MONITORING = False
EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webm"]


class ChanDownloader:
    def __init__(self, url):
        self.url = url
        self.downloading = False
        self.thread_title = self.get_thread_title()
        self.path = self.create_img_folder()

    def set_path(self, path):
        self.path = path

    def set_thread_title(self, thread_title):
        self.thread_title = thread_title

    def get_json_url(self):
        """ Get the url of the current 4chan thread's json"""
        if "4channel" in self.url:
            return f"{self.url.replace('boards.4channel','a.4cdn')}.json"
        else:
            return f"{self.url.replace('boards.4chan','a.4cdn')}.json"

    def get_thread_title(self):
        """ Get the title of the current 4chan thread """
        try:
            thread_json_url = self.get_json_url()
            print(
                bcolors.BOLD
                + bcolors.OKCYAN
                + "Link of json file of the thread is:"
                + f"{thread_json_url}"
                + bcolors.ENDC
            )
            r = requests.get(thread_json_url, verify=False)
            thread_json = r.json()
            thread_title = thread_json["posts"][0]["semantic_url"]
            print(bcolors.BOLD + bcolors.OKCYAN + f"\n{thread_title}" + bcolors.ENDC)
            return thread_title
        except Exception:
            return url.split("/")[1].split(".")[0]

    def create_img_folder(self):
        """ Create an Image Folder for the media of the thread to be stored """
        board = self.url.split("/")[3]
        self.thread_number = str(self.url.split("thread/")[1])
        path = Path.joinpath(Path.home(), f"4chan/{board}/{self.thread_title}__{self.thread_number}")
        Path(path).mkdir(parents=True, exist_ok=True)
        print(
            bcolors.OKGREEN
            + bcolors.BOLD
            + f"\nPath of created folder is: {path}"
            + bcolors.ENDC
        )
        return path

    def download_thread_json(self):
        """ Download the json of the current 4chan thread """
        thread_json_url = get_json_url(self.url)
        print(thread_json_url)
        try:
            wget.download(thread_json_url, str(self.path))
            print(
                bcolors.OKGREEN
                + bcolors.BOLD
                + "\nThread's json downloaded successfully!"
                + bcolors.ENDC
            )
        except Exception as e:
            print(e)

    def remove_extension(self, word):
        """ Remove the extension from the filename and returns it """
        global EXTENSIONS
        for ext in EXTENSIONS:
            if ext in word:
                return word.replace(ext, "")

    def is_archived(self):
        """ Check if the current 4chan thread is archived """
        print("Checking if thread is archived...")
        r = requests.get(self.url, verify=False)
        soup = BeautifulSoup(r.content, "html.parser")
        thread404 = soup.find("div", {"class": "boxbar"})
        thread_closed = soup.find("div", {"class": "closed"})
        if thread404 or thread_closed:
            return True
        return False

    def monitor_thread(self):
        """ Start to monitor the current 4chan thread """
        if self.downloading:
            # if the thread is already being downloaded, ignore the check
            print("Already downloading...")
            return
        elif self.is_archived():
            # if is archived stop monitoring the thread
            print("This thread is archived.")
            THREAD_MONITORING.cancel()
        else:
            print("Downloading thread")
            # download the update json of thread and the new media if it has any
            threading.Thread(target=self.download_all, daemon=True).start()

    def download_all(self):
        """ Download all files from the thread """
        self.downloading = True
        r = requests.get(self.url, verify=False)
        soup = BeautifulSoup(r.content, "html.parser")
        divMedia = soup.find_all("div", {"class": "fileText"})
        # Download a json of the threads
        try:
            webpage_path = Path.joinpath(self.path, "webpage")
            Path(webpage_path).mkdir(parents=True, exist_ok=True)
            thread_json_path = Path.joinpath(webpage_path, "thread.json")
            self.download_thread_json()
        except Exception as e:
            print(e)

        # Download all media files from the thread
        for tag in divMedia:
            hrefTag = tag.find_all("a")
            for media in hrefTag:
                try:
                    generated_filename = media["href"].split("/")[-1].strip()
                    filename = (
                        f"{self.remove_extension(generated_filename)}__{media.text.strip()}"
                    )
                    if not os.path.isfile(f"{self.path}/{filename}"):
                        print(
                            bcolors.OKGREEN
                            + bcolors.BOLD
                            + f"\nDownloading {filename}"
                            + bcolors.ENDC
                        )
                        wget.download(f'https:{media["href"]}', f"{self.path}/{filename}")
                    else:
                        print(
                            bcolors.WARNING
                            + "\nThis file already exists, continuing..."
                            + bcolors.ENDC
                        )
                except Exception as e:
                    print(e)
                    print("\nFailed to download.")

        self.downloading = False


def main():
    url = input(
        bcolors.HEADER + bcolors.BOLD + "Insert the thread link here: " + bcolors.ENDC
    )
    chandownloader = ChanDownloader(url)
    # chandownloader.download_all()
    THREAD_MONITORING = setInterval(30, chandownloader.monitor_thread)


if __name__ == "__main__":
    main()

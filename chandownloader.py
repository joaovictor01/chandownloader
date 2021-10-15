import logging
import requests
import json
import wget
import os
import sys
import urllib3.request
import urllib.error
import urllib.parse
import re
import time
import threading
from bs4 import BeautifulSoup
from pathlib import Path
from utils import bcolors, setInterval

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

THREAD_MONITORING = None
EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webm"]
CLEANR = re.compile('<.*?>') 


def print_bold_green(text):
    print(
            bcolors.OKGREEN
            + bcolors.BOLD
            + text
            + bcolors.ENDC
        )


def clean_html_string(string):
    cleantext = str(re.sub(CLEANR, '', string))
    return cleantext

class ChanDownloader:
    def __init__(self, url):
        # Logger
        self.logger = logging.getLogger(__name__)
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', 
                            '%m-%d-%Y %H:%M:%S')
        self.logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler('chandownloader.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(stdout_handler)

        self.url = url
        self.chan_name = self.get_chan_name()
        self.downloading = False
        self.thread_title = self.get_thread_title()
        self.path = self.create_img_folder()
        

    def get_chan_name(self):
        chan_name = str(self.url.split('https://')[1].split('/')[0].split('.')[0])
        print_bold_green(f'CHAN: {chan_name}')
        return chan_name

    def set_path(self, path):
        self.path = path

    def set_thread_title(self, thread_title):
        self.thread_title = thread_title

    def get_json_url(self):
        """ Get the url of the current 4chan thread's json"""
        if self.chan_name == '4chan':
            print_bold_green('4CHAN')
            if "4channel" in self.url:
                return f"{self.url.replace('boards.4channel','a.4cdn')}.json"
            else:
                return f"{self.url.replace('boards.4chan','a.4cdn')}.json"
        elif self.chan_name == '1500chan':
            print_bold_green('1500CHAN')
            json_url = str(self.url.replace('.html', '.json'))
            self.logger.debug('json url: %s', json_url)
            return json_url

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
            thread_title = ''
            if self.chan_name == '4chan':
                thread_title = thread_json["posts"][0]["semantic_url"]
            elif self.chan_name == '1500chan':
                thread_title = clean_html_string(f"{thread_json['posts'][0]['sub']}_{thread_json['posts'][0]['com']}").replace('/', '')[:100]
            print(bcolors.BOLD + bcolors.OKCYAN + f"\n{thread_title}" + bcolors.ENDC)
            return thread_title
        except Exception as error:
            self.logger.debug('Error gettint the title of the thread: %s', error)
            return self.url.split("/")[1].split(".")[0]

    def create_img_folder(self):
        """ Create an Image Folder for the media of the thread to be stored """
        board = self.url.split("/")[3]
        try:
            self.thread_number = str(self.url.split("thread/")[1])
        except Exception:
            self.thread_number = str(self.url.split("res/")[1]).replace('.html','')
        path = Path.joinpath(Path.home(), f"{self.chan_name}/{board}/{self.thread_title}__{self.thread_number}")
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
        try:
            thread_json_url = self.get_json_url()
            self.logger.info(f'Downloading json of thread: {thread_json_url}')
            if self.chan_name == '4chan':
                wget.download(thread_json_url, str(self.path))
            else:
                r = requests.get(thread_json_url, verify=False)
                with open(str(os.path.join(self.path, 'thread.json')), 'w+') as outfile:
                    json.dump(r.json(), outfile)
            print(
                bcolors.OKGREEN
                + bcolors.BOLD
                + "\nThread's json downloaded successfully!"
                + bcolors.ENDC
            )
        except Exception as e:
            self.logger.debug('Error downloading the json of the thread.')
            self.logger.debug(e)
            raise e

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
        global THREAD_MONITORING
        if self.downloading:
            # if the thread is already being downloaded, ignore the check
            self.logger.info("Already downloading...")
            return
        elif self.is_archived():
            # if is archived stop monitoring the thread
            self.logger.info("This thread is archived.")
            try:
                THREAD_MONITORING.cancel()
            except Exception:
                sys.exit()
        else:
            self.logger.info("Downloading thread")
            # download the update json of thread and the new media if it has any
            threading.Thread(target=self.download_all, daemon=True).start()
    
    def download_all_media(self, soup):
        if self.chan_name == '4chan':
            divMedia = soup.find_all("div", {"class": "fileText"})
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
                            print(bcolors.OKGREEN + bcolors.BOLD + f"\nDownloading {filename}"+ bcolors.ENDC)
                            wget.download(f'https:{media["href"]}', f"{self.path}/{filename}")
                        else:
                            print(bcolors.WARNING + "\nThis file already exists, continuing..." + bcolors.ENDC)
                    except Exception as e:
                        print(e)
                        print("\nFailed to download.")
        elif self.chan_name == '1500chan':
            media_files = soup.find_all('p', {'class':'fileinfo'})
            for media_file in media_files:
                filename = media_file.find('a').text
                media_path = media_file.find('a')['href']
                link = f'https://1500chan.org{media_path}'
                try:
                    if not os.path.isfile(f"{self.path}/{filename}"):
                        print(bcolors.OKGREEN + bcolors.BOLD + f"\nDownloading {filename}"+ bcolors.ENDC)
                        wget.download(link, f"{self.path}/{filename}")
                    else:
                        print(bcolors.WARNING + "\nThis file already exists, continuing..." + bcolors.ENDC)
                except Exception as e:
                    print(e)
                    print("\nFailed to download.")

        self.downloading = False

    def download_all(self):
        """ Download all files from the thread """
        self.chan_name = self.get_chan_name()
        self.downloading = True
        r = requests.get(self.url, verify=False)
        soup = BeautifulSoup(r.content, "html.parser")
        # Download a json of the threads
        try:
            self.download_thread_json()
        except Exception as error:
            self.logger.debug(error)
        self.download_all_media(soup)
        


def main():
    global THREAD_MONITORING
    url = input(
        bcolors.HEADER + bcolors.BOLD + "Insert the thread link here: " + bcolors.ENDC
    )
    chandownloader = ChanDownloader(url)
    # chandownloader.download_all()
    THREAD_MONITORING = setInterval(30, chandownloader.monitor_thread)


if __name__ == "__main__":
    main()

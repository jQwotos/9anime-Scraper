import os
import logging
import re
import subprocess

import requests

from bs4 import BeautifulSoup

MY_CLOUD_PAT = re.compile('<meta property="og:image" content="//(.*?)"')

resolution = '480'
resolutions = ['1080', '720', '480', '360']

def _pick_highest_res(link):
    testIncrement = 1
    for res in resolutions:
        trialLink = _increment_link(link, testIncrement).replace("{{RESOLUTION}}", res)
        if requests.get(trialLink, stream=True).status_code == 200:
            logging.info("Highest quality possible is %s" % (res))
            return link.replace("{{RESOLUTION}}", res)

def _get_direct_link(link):
    data = requests.get(link).content
    details = re.findall(MY_CLOUD_PAT, str(data))[0]
    logging.info("Details are '%s' from '%s'" % (details, link))
    actualLink = details.replace('preview.jpg', 'hls/{{RESOLUTION}}/{{RESOLUTION}}-{{INCREMENT}}.ts')
    actualLink = "https://%s" % (actualLink,)

    return _pick_highest_res(actualLink)

def _increment_link(link, increment):
    return link.replace('{{INCREMENT}}', '%04d' % (increment,))

def download(link, fname):
    '''

    Downloads a file from MyCloud based on link and filename

    '''
    directLink = _get_direct_link(link)
    logging.info("Recieved link of '%s' from '%s'" % (directLink, link,))
    increment = 0
    finished = False

    tempName = "%s.ts" % (fname,)
    with open(tempName, 'wb') as f:
        while True:
            increment += 1
            newLink = _increment_link(directLink, increment)
            while True:
                try:
                    download = requests.get(newLink, stream=True, timeout=10)
                    break
                except:
                    logging.error("Connection timed out while downloading block %i." % (increment))
            if download.status_code == 200:
                f.write(download.content)
                logging.info("Finished writing increment #%i" % (increment))
                finished = True
            else:
                logging.error("FAILED to download increment #%i" % (increment))
                break

    if finished:
        try:
            subprocess.run(['ffmpeg', '-i', tempName, '%s' % (fname,)])
        except:
            print("Please install FFMPEG")
        os.remove(tempName)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    link = input("TESTING MODE, Enter Link:")
    download(link, '1.mp4')

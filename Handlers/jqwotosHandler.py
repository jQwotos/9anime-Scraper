import argparse
import sys
import logging
import os
import glob
import requests
import time

sys.path.append('../')

import argcomplete

import anime9

def download(data, **kwargs):
    if kwargs['directory'] is not None:
        if not os.path.exists(kwargs['directory']):
            logging.debug("The specified directory of '%s' was not found, therefore making the directory." % (kwargs['directory']))
            os.makedirs(kwargs['directory'])
        else:
            logging.debug("The specified directory of '%s' was found." % (kwargs['directory']))
        os.chdir(kwargs['directory'])

    if not os.path.exists(data['title']):
        logging.debug("The show '' was not previously downloaded, therefore making new folder for the show." % (data['title']))
        os.makedirs(str(data['title']))
    os.chdir(data['title'])

    alreadyExists = glob.glob("*.mp4")

    for episode in data['episodes']:
        while True:
            try:
                for f in glob.glob("*.tmp"):
                    logging.info("Episode '%s' was in the middle of a download. Removing and redownloading." % (f))
                    os.remove(f)

                fName = episode['epNumber'] + ".mp4"
                if fName not in alreadyExists:
                    link = anime9.get_mp4(episode['id'])[-1]['file']
                    download = requests.get(link, stream=True, timeout=10)
                    tempF = episode['epNumber'] + ".tmp"

                    with open(tempF, 'wb') as f:

                        length = int(download.headers.get('content-length'))
                        start = time.clock()
                        current = 0

                        for chunk in download.iter_content(chunk_size=1024):

                            current += len(chunk)
                            sys.stdout.write("\r %s Mbps | %r Percent Complete" % (round(current // (time.clock() - start) / 1000000, 2), round((current / length) * 100, 1)))

                            if chunk:
                                f.write(chunk)

                        logging.info("Finished downloading '%s'." % (fName))
                        os.rename(tempF, fName)
                        break
                else:
                    logging.info("The file '%s' was already fully downloaded, skipping." % (fName))
                    break
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                logging.critical("Connection was disconnected during download... Retrying")

parser = argparse.ArgumentParser()

argcomplete.autocomplete(parser)

parser.add_argument('-d', '--directory', type=str, help="Location where the show should be downloaded")
parser.add_argument('-v', '--verbose', action='store_true', help="Change display level to verbose.")
parser.add_argument('link', type=str, help="Link to show")

args = vars(parser.parse_args())

if args['verbose']:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.CRITICAL)

episodes = anime9.getAllEpisodes(args['link'])
download(episodes, **args)

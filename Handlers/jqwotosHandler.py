import argparse
import sys
import logging
import os
import glob
import requests
import time

sys.path.append('../')

try: import argcomplete
except: logging.warning('Could not import the argcomplete module')

import anime9

def makeDir(kwargs):
    # Check if the user specified a directory
    if kwargs['directory'] is not None:
        # If the directory does not exist create the directory
        if not os.path.exists(kwargs['directory']):
            logging.debug("The specified directory of '%s' was not found, therefore making the directory." % (kwargs['directory']))
            os.makedirs(kwargs['directory'])
        else:
            logging.debug("The specified directory of '%s' was found." % (kwargs['directory']))

        # Navigate into the specified directory
        os.chdir(kwargs['directory'])

def download(data, kwargs):
    '''
        Downloads the show
    '''
    makeDir(kwargs)

    # If kwargs['force'] is not specified by the user do not make a new folder
    if kwargs['force'] is False:
        if not os.path.exists(data['title']):
            logging.debug("The show '%s' was not previously downloaded, therefore making new folder for the show." % (data['title']))
            os.makedirs(str(data['title']))
        os.chdir(data['title'])
    else:
        logging.debug("Force tag was specified, script will not make the folder.")

    # FInd all previously downloaded episodes
    alreadyExists = glob.glob("*.mp4")

    for episode in data['episodes']:
        # Used for continous retries if disconnected
        while True:
            try:
                # Remove all tmp files
                for f in glob.glob("*.tmp"):
                    logging.info("Episode '%s' was in the middle of a download. Removing and redownloading." % (f))
                    os.remove(f)

                # The name of the final file
                fName = episode['epNumber'] + ".mp4"

                # If the file is not downloaded yet
                if fName not in alreadyExists:

                    # Get the direct MP4 link
                    link = anime9.get_mp4(episode['id'])[-1]['file']

                    # Create a requests get object
                    download = requests.get(link, stream=True, timeout=10)

                    # Name of temporary file
                    tempF = episode['epNumber'] + ".tmp"

                    logging.info("Downloading episode # %s out of %s episodes of %s." % (episode['epNumber'], data['episodes'][-1]['epNumber'], data['title']))

                    # Make the file and open it for writing mode
                    with open(tempF, 'wb') as f:

                        # Get the length of the file for % done
                        length = int(download.headers.get('content-length'))
                        # Get when the download started
                        start = time.clock()

                        # Set the current bytes downloaded to 0
                        current = 0

                        # For each 1024 byte chunk
                        for chunk in download.iter_content(chunk_size=1024):

                            # Increase the current chunks by the length of the chunk
                            current += len(chunk)

                            # Print the details on the screen
                            sys.stdout.write("\r %s Mbps | %r Percent Complete" % (round(current // (time.clock() - start) / 1000000, 2), round((current / length) * 100, 1)))

                            # Write the chunk to the file if it's not broken
                            if chunk:
                                f.write(chunk)

                        logging.info("Finished downloading '%s'." % (fName))

                        # Rename the file once the download has finished
                        os.rename(tempF, fName)
                        break
                # If the file is already downloaded the continue to next episode
                else:
                    logging.info("The file '%s' was already fully downloaded, skipping." % (fName))
                    break

            # If there is a connection error or timeout restart the process
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                logging.critical("Connection was disconnected during download... Retrying")

def findNDownload(link, kwargs):
    download(anime9.getAllEpisodes(link), kwargs)

def main():
    links = []
    parser = argparse.ArgumentParser()

    argcomplete.autocomplete(parser)

    parser.add_argument('-d', '--directory', type=str, help="Location where the show should be downloaded", default="Downloads")
    parser.add_argument('-v', '--verbose', action='store_true', help="Change display level to verbose.")
    parser.add_argument('-a', '--auto', type=int, help="Automatically check for updates every x hours.")
    parser.add_argument('-f', '--force', action="store_true", help="Do not make a folder with the name of the show, just download it to specified directory.")
    # WIP parser.add_argument('-w', '--write', action="store_true", help="Just output all of the links into a file specified by '-d' instead of downloading the episodes.")
    parser.add_argument('-l', '--list', type=str, help="Download from a list of links in a specified file")
    parser.add_argument('link', type=str, help="Link to show", nargs='?')

    args = vars(parser.parse_args())

    # If the user specified to output in verbose change logging level to debug, otherwise set it to critical
    if args['verbose'] is True:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.CRITICAL)

    # If the user specifies a list then read and add to links
    if args['list'] is not None:
        if not os.path.isfile(args['list']):
            raise Exception("File %s specified by the list argument not found!" % (args['list']))

        with open(args['list'], 'r') as l:
            for line in l:
                links.append(line.replace('\n', ''))

    # Add positional argument link to list
    if args['link'] is not None:
        links.append(args['link'])

    # If the user specified that they want it to run automatically then keep it in a loop
    if args['auto'] is not None:
        while True:
            for link in links:
                findNDownload(link, args)
                logging.info("Finished update, waiting another %i hours until updating." % (args['auto']))
                # Sleep for the specified amount of time
                os.chdir("../..")
            time.sleep(args['auto'] * 3600)
    else:
        for link in links:
            findNDownload(link, args)
            os.chdir("../..")

if __name__ == "__main__":
    main()

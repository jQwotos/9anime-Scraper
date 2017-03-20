'''
Name: Jason Le
Email: le.kent.jason@gmail.com
Github: jQwotos
'''

import os
import logging
import re
import glob

import time
import sys

import requests
from bs4 import BeautifulSoup

import constants

# Returns a list of results
def search(keyword, numResults = 99):
    '''

    Scrapes the search query page of 9anime in order to find shows
    Returns a list of shows in the following format
    [{'link': 'A URL to the show', 'title': 'The name of the show'}]

    '''
    payload = {'keyword': keyword}
    headers = {'Referer': 'https://google.com'}
    page = requests.get(constants.SEARCH_URL, params=payload, headers=headers).content
    soupedPage = BeautifulSoup(page, "html.parser")

    shows = []
    numFound = 0

    listFilm = soupedPage.findAll(attrs={'class': 'list-film'})

    if len(listFilm) > 0:
        listFilm = listFilm[0]
        listFilm = listFilm.findAll(attrs={'class': 'row'})

        if len(listFilm) > 0:
            showsSouped = listFilm[0].findAll(attrs={'class': 'item'})

            if len(showsSouped) > 0:
                for show in showsSouped:
                    numFound += 1
                    if numFound > numResults: break
                    shows.append({
                        'link': show.findAll(attrs={'class': 'name'})[0]['href'],
                        'title': show.findAll(attrs={'class': 'name'})[0].text,
                    })
            else:
                logging.info("Could not find any Shows when searching for %s" % (keyword))
        else:
            logging.info("Unable to find any rows pertaining to search query %s" % (keyword))
    logging.info("Found a total of %i shows when searching for %s at a limit of %i shows." % (len(shows), keyword, numResults))
    return shows

def get_mp4(id):
    '''

    Returns a list of MP4 links by taking in an episode ID
    [{'type': 'file format', 'file': 'link to video file', 'label': 'resolution / quality of file'}]

    '''
    payload = {
        'id': id
    }

    details = requests.get(constants.INFO_API, params=payload).json()
    payload['token'] = details['params']['token']
    logging.info("Acquired token %s when requested from id %s" % (payload['token'], payload['id']))

    data = requests.get(constants.GRABBER_API, params=payload).json()['data']
    logging.info("Recieved %i different links for id %s" % (len(data), payload['id']))

    return data

def getAllEpisodes(link):
    '''

    Returns the details of all of the episodes found on a series
    [{'title': 'name of series'}, 'episodes': [{
        'id': '9anime id for episode',
        'name': 'name of episode, typically episode number',
        'link': 'link to the episode',
        'epNumber': int(episode position number in series)
        }]]

    '''
    data = {
        "episodes": [],
    }
    page = BeautifulSoup(requests.get(link).content, 'html.parser')

    servers = page.findAll("div", {"class": "server row"})

    data["title"] = page.findAll("h1", {"class": "title"})[0].text

    for server in servers:
        episodes = server.findAll("a")

        for episode in episodes:
            data['episodes'].append({
                "id": episode['data-id'],
                "name": episode.text,
                "link": episode['href'],
                "epNumber": episode['data-base'],
            })
        break

    return data

def download(link, **kwargs):
    '''

    Downloads a whole series, to either a designated location
    or the name of the series

    '''
    data = getAllEpisodes(link)
    if 'location' not in kwargs:
        kwargs['location'] = str(data['title'])
    if not os.path.exists(kwargs['location']):
        os.makedirs(kwargs['location'])
    os.chdir(kwargs['location'])
    alreadyExists = glob.glob("*.mp4")

    for f in glob.glob("*.tmp"):
        os.remove(f)

    for episode in data['episodes']:
        directLink = get_mp4(episode['id'])[-1]['file']
        download = requests.get(directLink, stream=True)
        if 'epName' in kwargs:
            fileName = kwargs['epName'].replace('$EPNUM', episode['epNumber'])
        else:
            fileName = episode['epNumber'] + ".mp4"
        tempFile = episode['epNumber'] + ".tmp"
        if fileName not in alreadyExists:
            with open(tempFile, 'wb') as f:


                length = download.headers.get('content-length')
                start = time.clock()
                current = 0


                for chunk in download.iter_content(chunk_size=1024):


                    current += len(chunk)
                    sys.stdout.write("\r %s bps" % (current // (time.clock() - start)))


                    if chunk:
                        f.write(chunk)
                    else:
                        logging.warning("Chunk download error when writing to %s for %s at %s" % (filename, link, directLink))
                os.rename(tempFile, fileName)
        else:
            logging.info("Already downloaded episode %s when trying to download %s" % (fileName, location))

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
                    link = show.findAll(attrs={'class': 'name'})[0]['href']
                    shows.append({
                        'link': link,
                        'title': show.findAll(attrs={'class': 'name'})[0].text,
                        'id': link[-4:],
                    })
            else:
                logging.info("Could not find any Shows when searching for %s" % (keyword))
        else:
            logging.info("Unable to find any rows pertaining to search query %s" % (keyword))
    logging.info("Found a total of %i shows when searching for %s at a limit of %i shows." % (len(shows), keyword, numResults))
    return shows

def get_mp4(id, **kwargs):
    '''

    Returns a list of MP4 links by taking in an episode ID
    [{'type': 'file format', 'file': 'link to video file', 'label': 'resolution / quality of file'}]

    '''

    payload = {
        'id': id
    }

    cookies = {
        'reqkey': constants.reqkey if 'reqkey' not in kwargs else kwargs['reqkey']
    }

    headers = {
          'Accept':'application/json, text/javascript, */*; q=0.01',
          'X-DevTools-Emulate-Network-Conditions-Client-Id':'0abc8a98-1b67-42ab-9ae1-b86b894d8d60',
          'X-Requested-With':'XMLHttpRequest',
          'X-DevTools-Request-Id':'9444.1270',
          'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
          'DNT':'1',
          'Referer':'https://9anime.to/watch/eromanga-sensei.k22w/8x5z2y',
          'Accept-Encoding':'gzip, deflate, sdch, br',
          'Accept-Language':'en-US,en;q=0.8',
      }
    details = requests.get(constants.INFO_API, params=payload, headers=headers, cookies = cookies).json()
    if 'params' not in details:
        raise Exception("Your reqkey cookie has been banned by 9anime, please get another one.")

    payload['server'] = details['grabber'].rsplit('?server=', 1)[-1]
    payload['token'] = details['params']['token']
    payload['options'] = details['params']['options']

    logging.info("Acquired token %s when requested from id %s" % (payload['token'], payload['id']))
    data = requests.get(constants.GRABBER_API, params=payload).json()

    if 'data' not in data:
        raise Exception("Server did not respond with data.")
    else:
        data = data['data']

    logging.info("Recieved %i different links for id %s" % (len(data), payload['id']))

    return data

def getAllEpisodes(link):
    '''
    If you want all servers, use get_all_show_sources instead
    Returns the details of all of the episodes found on a series
    [{'title': 'name of series'},
        'id': 'id of series',
        'episodes': [{
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

    data['id'] = page.findAll("div", {"class": "watchpage"})[0]['data-id']

    for server in servers:
        episodes = server.findAll("a")

        for episode in episodes:
            data['episodes'].append({
                "id": episode['data-id'],
                "name": episode.text,
                "link": episode['href'],
                "epNumber": episode['data-base'],
            })
        # Maybe a future implementation do something with multiple servers...
        break

    return data

def get_all_show_sources(link):
    '''
    Returns the details of all of the episodes found on a series
    [{'title': 'name of series'},
        'id': 'id of series',
        'episodes': [{
        'id': '9anime id for episode',
        'name': 'name of episode, typically episode number',
        'link': 'link to the episode',
        'epNumber': int(episode position number in series)
        }]]

    '''
    data = {
        "sources": [],
    }
    page = BeautifulSoup(requests.get(link).content, 'html.parser')

    servers = page.findAll("div", {"class": "server row"})

    data["title"] = page.findAll("h1", {"class": "title"})[0].text

    data['id'] = page.findAll("div", {"class": "watchpage"})[0]['data-id']

    for server in servers:
        episodes = server.findAll("a")
        data['sources'].append({
            'server': server.find('label', {'class': 'name col-md-3 col-sm-4'}).text,
            'links': [],
        })
        for episode in episodes:
            data['sources'][-1]['links'].append({
                "id": episode['data-id'],
                "name": episode.text,
                "link": episode['href'],
                "epNumber": episode['data-base'],
            })

    return data

def download(link, **kwargs):
    '''

    Downloads a whole series, to either a designated location
    or the name of the series

    '''
    data = getAllEpisodes(link)
    if 'location' in kwargs:
        if not os.path.exists(kwargs['location']):
            os.makedirs(kwargs['location'])
        os.chdir(kwargs['location'])
    if not os.path.exists(str(data['title'])):
        os.makedirs(str(data['title']))
    os.chdir(str(data['title']))

    alreadyExists = glob.glob("*.mp4")

    for f in glob.glob("*.tmp"):
        os.remove(f)

    for episode in data['episodes']:
        if 'epName' in kwargs:
            fileName = kwargs['epName'].replace('$EPNUM', episode['epNumber'])
        else:
            fileName = episode['epNumber'] + ".mp4"

        if fileName not in alreadyExists:
            directLink = get_mp4(episode['id'])[-1]['file']
            download = requests.get(directLink, stream=True)
            tempFile = episode['epNumber'] + ".tmp"
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
            logging.info("Already downloaded episode %s" % (fileName))

def getSeriesInfo(link):
    '''

    Return information related to series in the following format:
    {'title': 'Name of anime', 'year': '(int) Year anime released', 'Scores': 'Anime Score', 'Status': 'Completed/Airing',
    'Date aired': 'season air dates', 'Genre': 'genre of the anime', 'Other names': 'other names of anime'}

    Either enter the whole link or just the series ID (The 3-4 letters alphanumeric ID preceded by ".")

    '''

    data = {}

    period_index = link.rfind(".")
    series_id = link[period_index + 1:link.find("/", period_index) if link.find("/", period_index) > 0 else len(link)]

    headers = {'Referer': 'https://google.com'}
    page = requests.get(constants.SERIES_INFO_API + series_id, headers=headers).content
    soupedPage = BeautifulSoup(page, 'html.parser')

    data["title"] = soupedPage.find("div", attrs={"class": "title"}).get_text()
    data["year"] = int(soupedPage.find("div", attrs={"class": "title"}).find("span").get_text())

    for metadata in soupedPage.find_all("div", attrs={"class": "meta"}):
        if str(metadata).find("label") != -1:
            label = metadata.find("label").get_text().replace(":", "")
            text = re.sub(" +", " ", metadata.find("span").get_text().replace("\n", "").strip())
            data[label] = text

    return data

if __name__ == "__main__":
    print("This module is to be imported, not used directly.")

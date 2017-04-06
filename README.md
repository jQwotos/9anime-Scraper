# 9anime Scraper
Because scraping kissanime has become quite an annoyance since it's bot detection is fairly trigger happy. This 9anime scraper is a replacement for kissanime mass downloader.

# Usage
Currently this can only be used as a module, eventually there will be a cli system that accepts argsparse like KAMD.

Here are some basic functions

- [Download](https://github.com/jQwotos/9anime-Scraper/wiki)
- [Search](https://github.com/jQwotos/9anime-Scraper/wiki/Search)

## Basic Setup and Usage Guide

First we clone this repository and navigate into it
```
git clone https://github.com/jQwotos/9anime-Scraper && cd 9anime-Scraper
```

You may need to install some required modules (no requirements.txt yet)
```
pip3 install bs4 requests
```

Then we can startup the python shell then import the module
```
python3
import anime9
```

From here, you can run some functions such as search
```
anime9.search('sword art online dub')
```

You probably want to download now, so you can do that
```
anime9.download('https://9anime.to/watch/sword-art-online.5y9/m2932p')
```

If your downloading things on a server, i'd recommend you install [screen](https://help.ubuntu.com/community/Screen) as it allows you to leave an ssh session and then resume it later on.

There are some more things in the [wiki](https://github.com/jQwotos/9anime-Scraper/wiki)

# Contributing
Want to contribute to this project? We just follow the [standard github workflow](https://gist.github.com/Chaser324/ce0505fbed06b947d962). Basically just fork, code, push, pr.

Also feel free to start a new [issue](https://github.com/jQwotos/9anime-Scraper/issues) if you find a bug or have a suggestion.

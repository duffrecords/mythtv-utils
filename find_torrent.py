#!/usr/bin/env python

import re
import sys
import getopt
import requests
import json
import logging
from bs4 import BeautifulSoup
import math
import subprocess
from transmission import Transmission
from tmdb import TMDB

def main(argv):
    optional_args = '[-y <year>] [-d] [--allow-chronologies] [--high-quality] [-s <season>] [-e <episode>] [--debug]'
    try:
        opts, args = getopt.getopt(argv, "hdn:y:s:e:",
                ["name=",
                 "year=",
                 "download",
                 "allow-chronologies",
                 "high-quality",
                 "season=",
                 "episode=",
                 "debug"])
    except getopt.GetoptError:
        print "find_torrents.py -n '<name of movie>' " + optional_args
        sys.exit(2)
    year = ''
    download = False
    chronologies = False
    high_quality = False
    season = None
    episode = None
    debug = False
    for opt, arg in opts:
        if opt == '-h':
            print "find_torrents.py -n '<name of movie>' " + optional_args
            sys.exit()
        elif opt in ("-n", "--name"):
            name = arg
        elif opt in ("-d", "--download"):
            download = True
        elif opt in ("-y", "--year"):
            year = arg
        elif opt == '--allow-chronologies':
            chronologies = True
        elif opt == '--high-quality':
            high_quality = True
        elif opt in ("-s", "--season"):
            season = '{:02d}'.format(int(arg))
            season = int(arg)
        elif opt in ("-e", "--episode"):
            episode = '{:02d}'.format(int(arg))
            episode = int(arg)
        elif opt == '--debug':
            debug = True
    if season or episode:
        video_type = 'television'
    else:
        video_type = 'movie'

    logger = logging.getLogger(__name__)
    handler = logging.FileHandler('find_torrent.log')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
            '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.debug("arguments: %s" % ' '.join(argv))

    transmission = Transmission()
    transmission_creds = transmission.user + ':' + transmission.password
    tmdb = TMDB()
    tmdb_url = 'https://api.themoviedb.org/3/search/movie'
    title_variations = []
    # logger.debug("name.split() = %s" % name.split())
    for delimiter in [ ' ', '.', '-', '_' ]:
        variation = delimiter.join(name.split())
        logger.debug(variation)
        title_variations.append(variation)
    
    query = re.sub(r'[\s-]', '+', name)
    if year:
        logger.debug("year: %s" % year)
    if video_type == 'movie':
        if year == '':
            logger.debug('searching for year on tmdb')
            r = requests.get(tmdb_url + '?api_key=' + tmdb.key + '&query=' + name)
            tmdb_results = r.json()
            logger.debug("len(tmdb_results): %s" % len(tmdb_results))
            for result in tmdb_results['results']:
                logger.debug(result)
                if result['title'] == name:
                    logger.debug("result['title']: %s" % result['title'])
                    m = re.match(r'(\d{4})-\d{2}-\d{2}', result['release_date'])
                    year = m.group(1)
                    logger.info("this film appears to have been released in %s" % year)
                    break
        query = "%s+%s" % (query, year)
        if year:
            logger.debug("year: %s" % year)
    elif video_type == 'television':
        if season:
            if episode:
                catalog = "S%sE%s" % ('{:02d}'.format(season), '{:02d}'.format(episode))
            else:
                catalog = "Season+%s" % str(season)
            logger.debug("catalog: %s" % catalog)
            query = "%s+%s" % (query, catalog)
    logger.debug("query: %s" % query)
    great_words = title_variations
    if year != '':
        great_words.append(year)
    good_words = [ 'BrRip', 'BDRip', 'BRRip', 'BluRay', 'Bluray',
                    'x264', 'H.264' ]
    bad_words = [ 'DVDR', 'PAL', 'DvDrip', 'DVDrip', 'DVDscr', '480p' ]
    avoid_words = [ 'YIFY', 'H.265', 'h265', 'x265', 'HEVC' ]
    if '3D' not in name:
        avoid_words.append('3D')
    chronology_words = [ 'chronology',
                        'collection',
                        'sequel',
                        '1, 2',
                        '1&2',
                        '1 & 2',
                        'series',
                        'duology',
                        'trilogy',
                        'triology',
                        'quadrilogy',
                        'tetralogy',
                        'pentalogy',
                        'hexalogy',
                        'heptalogy' ]
    sequel_words = ['part', 'chapter']
    if video_type == 'movie':
        sequel_words.append('episode')
    numbers = [str(x) for x in range(1, 11)]
    numbers = numbers + ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x']
    sequel_phrases = [ w + ' ' + x for w in sequel_words for x in numbers ]
    if video_type == 'movie':
        too_small = 1.0
        ideal_min = 4.0
        ideal_max = 9.0
    elif video_type == 'television':
        too_small = 0.12
        ideal_min = 0.7
        ideal_max = 1.5
    too_big = 17.0
    if high_quality:
        hiq_min = ideal_min + ((too_big - ideal_min) / 2)
        hiq_max = too_big
    else:
        hiq_min = ideal_min
        hiq_max = ideal_max
    torrents = []
    
    # scrape torrent site
    search_results = []
    r = requests.get("https://kickass.cd/search.php?q=%s" % query)
    # r = requests.get("https://kickass2.org/search.php?q=%s" % query)
    search_results.append(r.content)
    if len(search_results) == 0:
        logger.critical('no HTML response from kickass.cd')
        sys.exit(1)
    else:
        logger.info('got HTML response from kickass.cd')
    #html_doc = open('webpage2.html', 'r')

    # parse scraped HTML
    start_list = []
    final_list = []
    for doc in search_results:
        soup = BeautifulSoup(doc, 'lxml')
        div = soup.find(id='mainSearchTable')
        # div = soup.find(class_='mainpart')
        if not div:
            sys.exit("couldn't find mainpart div")
        logger.debug('found mainSearchTable div')
        rows = div.find_all('tr', class_='odd')
        if len(rows) == 0:
            logger.critical('query returned no results')
            sys.exit(1)
        else:
            logger.info("query returned %s results" % len(rows))
        for tr in div.find_all('tr', class_='odd'):
            score = 0
            rejected = False
            link = tr.find('a', {'title': 'Torrent magnet link'})['href']
            title = tr.find('a', class_='cellMainLink').get_text()
            logger.debug("scraped title: %s" % title)
            size = tr.find_all('td')[1].get_text()
            size = re.sub('<[^<]+?>', '', size)
            if isinstance(size, unicode):
                size = size.encode('ascii', 'ignore')
            trs = tr.find_all('td')[3]
            # logger.debug(tr.find_all('td')[3])
            try:
                seeders = tr.find_all('td')[3].get_text()
                seeders = re.sub('<[^<]+?>', '', seeders)
                seeders = int(seeders)
            except:
                logger.debug("couldn't display HTML in seeders column. setting seeders to a default of 1")
                seeders = 1
            size = size.replace('&nbsp;', ' ')
            if 'MiB' in size or 'MB' in size:
                size = re.sub(r'Mi*B', '', size)
                size = float(size.split()[0]) / 1024
            elif 'GiB' in size or 'GB' in size:
                size = re.sub(r'Gi*B', '', size)
                size = float(size.split()[0])
            else:
                rejected = True
                size = 0
                logger.debug('rejected due to size')
            chronology_matches = [ w for w in chronology_words if w in title.lower() and w not in name.lower() ]
            #logger.debug(chronology_matches)
            sequel_matches = [ w for w in sequel_phrases if w in title.lower() and w not in name.lower() ]
            #logger.debug(sequel_matches)
            if ((any(chronology_matches)
                or any(sequel_matches)
                or re.search(r'\d{4}[-\s]\d{4}', title))
                and not chronologies):
                    rejected = True
                    logger.debug('rejected because it looks like a sequel or collection')
            if title not in [ t['title'] for t in torrents ]:
                if seeders == 0:
                    rejected = True
                    logger.debug('rejected because there are no seeders')
                if size < too_small:
                    rejected = True
                    logger.debug("rejected because %.2f GB is too small" % size)
                if size > too_big:
                    rejected = True
                    logger.debug("rejected because %.2f GB is too big" % size)
                if any(w in title for w in avoid_words):
                    rejected = True
                    rejected_words = ' '.join(list(set(title.split()).intersection(avoid_words)))
                    logger.debug("rejected because torrent name contains the following keywords: %s" % rejected_words)
                if not rejected:
                    torrent = {
                            'title': title,
                            'link': link,
                            'size': size,
                            'seeders': seeders,
                            'score': score,
                            'res': ''
                            }
                    start_list.append(torrent)

    logger.info("%s results look relevant" % len(start_list))

    # categorize torrents based on resolution
    logger.debug("separating torrents by resolution")
    hd1080 = []
    hd720 = []
    other = []
    for torrent in start_list:
        if any(w in torrent['title'] for w in ['1080p','1080i']):
            hd1080.append(torrent)
            torrent['res'] = '1080p'
        elif '720p' in torrent['title']:
            hd720.append(torrent)
            torrent['res'] = '720p'
        else:
            other.append(torrent)
            torrent['res'] = ''
    logger.debug("\t1080i/p: %s torrents" % len(hd1080))
    logger.debug("\t720p:    %s torrents" % len(hd720))
    logger.debug("\tother:   %s torrents" % len(other))

    # score torrents based on keywords, size, and number of seeders
    for tlist in [ hd1080, hd720, other ]:
        for torrent in tlist:
            logger.debug(torrent['title'])
            delta = math.log(torrent['seeders'], 16)
            logger.debug("\tnumber of seeders: %+.2f points" % delta)
            torrent['score'] = torrent['score'] + delta
            for w in great_words:
                if w in torrent['title']:
                    if w == year:
                        delta = 2
                    else:
                        delta = 4
                    logger.debug("\tmatched great_words: %+.2f points" % delta)
                    torrent['score'] = torrent['score'] + delta
            for w in good_words:
                if w in torrent['title']:
                    delta = 1
                    logger.debug("\tmatched good_words: %+.2f points" % delta)
                    torrent['score'] = torrent['score'] + delta
            for w in bad_words:
                if w in torrent['title']:
                    delta = -1
                    logger.debug("\tmatched bad_words: %+.2f points" % delta)
                    torrent['score'] = torrent['score'] + delta
            if season:
                delta = 2
                if episode:
                    if catalog in torrent['title']:
                        logger.debug("\tmatched season/episode: %+.2f points" % delta)
                        torrent['score'] = torrent['score'] + delta
                else:
                    if re.search(r"season[\s\.\-_]*0*%d" % season, torrent['title'], re.I):
                        logger.debug("\tmatched season: %+.2f points" % delta)
                        torrent['score'] = torrent['score'] + delta
            if torrent['size'] < ideal_min:
                delta = 1.0 * ((math.log(torrent['size'] / math.log(torrent['size']+1)) + 1) + (math.log(torrent['size'] / math.log(torrent['size']+1)) * 15) - 6) / 2
                logger.debug("\tsmaller than ideal file size: %+.2f points" % delta)
                torrent['score'] = torrent['score'] + delta
            if torrent['size'] > ideal_max:
                delta = -1
                logger.debug("\tlarger than ideal file size: %+.2f points" % delta)
                torrent['score'] = torrent['score'] + delta
            if torrent['size'] > hiq_min or torrent['size'] < hiq_max:
                if high_quality:
                    delta = (torrent['size'] / 2) * math.log(torrent['size'])
                #else:
                #    delta = 1
                    logger.debug("\tideal file size: %+.2f points" % delta)
                    torrent['score'] = torrent['score'] + delta

        # sort torrents by score
        for torrent in sorted(tlist, key=lambda t: t['score'], reverse=True):
            final_list.append(torrent)
        logger.debug("final list contains %s torrents" % len(final_list))

    if video_type == 'television':
        logger.debug('merging 1080 and 720p content scores because this is a television program')
        final_list = sorted(final_list, key=lambda t: t['score'], reverse=True)

    # return the results
    if download:
        if len(final_list) < 1:
            logger.info("final list was empty")
            sys.exit("no results")
        logger.info("downloading %s" % final_list[0]['link'])
        # print final_list[0]['link']
        sp = subprocess.Popen(' '.join([
                        'transmission-remote',
                        '--auth', transmission_creds,
                        '-a', final_list[0]['link']
                        ]), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sp_data = []
        sp_data = sp.communicate()
        # print(sp_data)
        if sp_data[1]:
            if re.search(r"transmission-remote.*Couldn\'t connect to server", sp_data[1]):
                sys.exit("transmission-daemon unreachable")
        elif re.search(r"invalid or corrupt torrent file", sp_data[0]):
            sys.exit("invalid or corrupt torrent file")
        else:
            print("found a %s copy of %s" % (final_list[0]['res'], final_list[0]['title']))
    else:
        logger.info("not downloading")
        if len(final_list) > 0:
            logger.info('---------------- RESULTS ----------------')
            logger.info("score\tseeders\tsize\t  title")
            print("score\tseeders\tsize\t  title")
            for torrent in final_list[:10]:
                result = "%.2f\t%s\t%.1f GiB\t  %s" % (torrent['score'],
                                                torrent['seeders'],
                                                torrent['size'],
                                                torrent['title'])
                print(result)
                logger.info(result)
            logger.info('-----------------------------------------')
        else:
            logger.warning("no results!")
            print "Error: no results"

if __name__ == "__main__":
    main(sys.argv[1:])

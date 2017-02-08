#!/usr/bin/env python

import re
import sys
import getopt
import requests
import json
from bs4 import BeautifulSoup
import math
from subprocess import Popen
from transmission import Transmission
from tmdb import TMDB

def main(argv):
    optional_args = '[-y <year>] [-s] [--allow-chronologies] [--high-quality]'
    try:
        opts, args = getopt.getopt(argv, "hn:y:s",
                ["name=","year=","single","allow-chronologies","high-quality"])
    except getopt.GetoptError:
        print "find_torrents.py -n '<name of movie>' " + optional_args
        sys.exit(2)
    year = ''
    single = False
    chronologies = False
    high_quality = False
    for opt, arg in opts:
        if opt == '-h':
            print "find_torrents.py -n '<name of movie>' " + optional_args
            sys.exit()
        elif opt in ("-n", "--name"):
            name = arg
        elif opt in ("-s", "--single"):
            single = True
        elif opt in ("-y", "--year"):
            year = arg
        elif opt == '--allow-chronologies':
            chronologies = True
        elif opt == '--high-quality':
            high_quality = True

    transmission = Transmission()
    transmission_creds = transmission.user + ':' + transmission.password
    tmdb = TMDB()
    tmdb_url = 'https://api.themoviedb.org/3/search/movie'
    title_variations = []
    for delimiter in [ ' ', '.', '-', '_' ]:
        title_variations.append(delimiter.join(name))
    
    query = re.sub(r'[\s-]', '+', name)
    if year == '':
        r = requests.get(tmdb_url + '?api_key=' + tmdb.key + '&query=' + name)
        tmdb_results = r.json()
        for result in tmdb_results['results']:
            if result['title'] == name:
                m = re.match(r'(\d{4})-\d{2}-\d{2}', result['release_date'])
                year = m.group(1)
                query = query + '+' + year
                break
    great_words = [ year, ] + title_variations
    good_words = [ 'BrRip', 'BDRip', 'BRRip', 'BluRay', 'Bluray',
                    'x264', 'H.264' ]
    bad_words = [ 'DVDR', 'PAL', 'DvDrip', '480p' ]
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
    too_small = 1.0
    too_big = 17.0
    ideal_min = 4.0
    ideal_max = 9.0
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
    search_results.append(r.content)
    #html_doc = open('webpage2.html', 'r')

    # parse scraped HTML
    start_list = []
    final_list = []
    for doc in search_results:
        soup = BeautifulSoup(doc, 'lxml')
        div = soup.find(id='mainSearchTable')
        for tr in div.find_all('tr', class_='odd'):
            score = 0
            rejected = False
            link = tr.find('a', {'title': 'Torrent magnet link'})['href']
            title = tr.find('a', class_='cellMainLink').get_text()
            size = tr.find_all('td')[1].get_text()
            seeders = int(tr.find_all('td')[3].get_text())
            if 'MiB' in size:
                size = float(size.split()[0]) / 1024
            elif 'GiB' in size:
                size = float(size.split()[0])
            else:
                rejected = True
            chronology_matches = [ w in title.lower() for w in chronology_words ]
            score = score - math.log(len(chronology_matches))
            if (any(chronology_matches)
                and re.search(r'\d{4}[-\s]\d{4}', title)
                and not chronologies):
                    rejected = True
            if title not in [ t['title'] for t in torrents ]:
                if (seeders > 0
                    and size > too_small
                    and size < too_big
                    and not rejected
                    and not any(w in title for w in avoid_words)):
                        torrent = {
                                'title': title,
                                'link': link,
                                'size': size,
                                'seeders': seeders,
                                'score': score
                                }
                        start_list.append(torrent)

    # categorize torrents based on resolution
    hd1080 = []
    hd720 = []
    other = []
    for torrent in start_list:
        if any(w in torrent['title'] for w in ['1080p','1080i']):
            hd1080.append(torrent)
        elif '720p' in torrent['title']:
            hd720.append(torrent)
        else:
            other.append(torrent)

    # score torrents based on keywords, size, and number of seeders
    for tlist in [ hd1080, hd720, other ]:
        for torrent in tlist:
            torrent['score'] = torrent['score'] + math.log(torrent['seeders'])
            for w in great_words:
                if w in torrent['title']:
                    torrent['score'] = torrent['score'] + 2
            for w in good_words:
                if w in torrent['title']:
                    torrent['score'] = torrent['score'] + 1
            for w in bad_words:
                if w in torrent['title']:
                    torrent['score'] = torrent['score'] - 1
            if torrent['size'] < ideal_min:
                torrent['score'] = torrent['score'] - 2
            if torrent['size'] > ideal_max:
                torrent['score'] = torrent['score'] - 1
            if high_quality:
                if torrent['size'] > hiq_min or torrent['size'] < hiq_max:
                    torrent['score'] = torrent['score'] + (torrent['size'] / 2) * math.log(torrent['size'])

        # sort torrents by score
        for torrent in sorted(tlist, key=lambda t: t['score'], reverse=True):
            final_list.append(torrent)

    # return the results
    if single:
        print final_list[0]['link']
        process = Popen([
                        'transmission-remote',
                        '--auth', transmission_creds,
                        '-a', final_list[0]['link']
                        ]).communicate()
    else:
        for torrent in final_list[:10]:
            print "%.2f  %s  %.1f GiB\t%s" % (torrent['score'],
                                            torrent['seeders'],
                                            torrent['size'],
                                            torrent['title'])

if __name__ == "__main__":
    main(sys.argv[1:])

#!/usr/bin/env python

import re
import sys
import getopt
import requests
from bs4 import BeautifulSoup

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hn:y:", ["name=","year="])
    except getopt.GetoptError:
        print "find_torrents.py -n '<name of movie>' -y <year>"
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print "find_torrents.py -n '<name of movie>' -y <year>"
            sys.exit()
        elif opt in ("-n", "--name"):
            name = arg
        elif opt in ("-y", "--year"):
            year = arg

    title_variations = []
    for delimiter in [ ' ', '.', '-', '_' ]:
        title_variations.append(delimiter.join(name))
    
    min_res = '1080p'
    great_words = [ min_res, year ] + title_variations
    good_words = [ '720p', 'BrRip', 'BDRip', 'BRRip', 'BluRay', 'Bluray', 'x264', 'H.264' ] + title_variations
    bad_words = [ 'DVDR', 'PAL', 'DvDrip', '480p', 'x265', 'H.265', 'HEVC' ]
    avoid_words = [ 'YIFY' ]
    too_small = 1.0
    ideal_min = 4.0
    ideal_max = 9.0
    too_big = 17.0
    torrents = []
    
    query = re.sub(' ', '+', name)
    r = requests.get("https://kickass.cd/search.php?q=%s" % query)
    html_doc = r.content
    #html_doc = open('webpage2.html', 'r')
    if year:
        r2 = requests.get("https://kickass.cd/search.php?q=%s+%s" % (query, year))
        html_doc_2 = r2.content
    #html_doc_2 = open('webpage2.html', 'r')
    for doc in [ html_doc, html_doc_2 ]:
        soup = BeautifulSoup(doc, 'lxml')
        div = soup.find(id='mainSearchTable')
        for tr in div.find_all('tr', class_='odd'):
            score = 0
            link = tr.find('a', {'title': 'Torrent magnet link'})['href']
            title = tr.find('a', class_='cellMainLink').get_text()
            size = tr.find_all('td')[1].get_text()
            if 'MiB' in size:
                size = float(size.split()[0]) / 1024
            elif 'GiB' in size:
                size = float(size.split()[0])
            else:
                break
            if title not in [ t['title'] for t in torrents ]:
                for w in great_words:
                    if w in title:
                        score = score + 2
                for w in good_words:
                    if w in title:
                        score = score + 1
                for w in bad_words:
                    if w in title:
                        score = score - 1
                for w in avoid_words:
                    if w in title:
                        score = - 2
                if size < too_small or size > too_big:
                    score = score - 2
                else:
                    if ideal_min < size < ideal_max:
                        score = score + 3
                    else:
                        score = score + 2
                torrent = { 'title': title, 'link': link, 'size': size, 'score': score }
                torrents.append(torrent)
    
    torrents = sorted(torrents, key=lambda torrent: torrent['score'], reverse=True)
    
    for t in torrents[:10]:
        print "%s %s\t%s" % (t['score'], t['size'], t['title'])

if __name__ == "__main__":
    main(sys.argv[1:])

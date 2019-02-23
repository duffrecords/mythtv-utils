#!/usr/bin/env python

import argparse
from bs4 import BeautifulSoup
import json
import os
import re
import requests
import urllib.parse

domain = 'https://zooqle.com'
pref_res = os.environ.get('pref_res', '1080p')
pref_audio = os.environ.get('pref_audio', '5.1')
pref_lang = os.environ.get('pref_lang', 'en')
pref_codec = os.environ.get('pref_codec', '1080p')

lang_full = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'ru': 'Russian'
}


def search_zooqle(name):
    query_string = urllib.parse.quote_plus(name)
    r = requests.get(f'{domain}/search?q={query_string}')
    soup = BeautifulSoup(r.content, 'lxml')
    table = soup.find_all('table', class_='table-torrents')
    for tr in table[0].find_all('tr'):
        tds = tr.find_all('td')
        if not re.match(r'[0-9]+\.', tds[0].get_text()):
            continue
        # td = tr.find('td', class_='text-trunc')
        # if not td:
        #     continue
        link_text = tds[1].find('a').get_text()
        try:
            audio_format = tds[1].find('span', {'title': 'Audio format'}).get_text()
        except AttributeError:
            audio_format = ''
        try:
            languages = tds[1].find('span', {'title': 'Detected languages'}).get_text()
        except AttributeError:
            languages = ''
        magnet_link = tds[2].find('a', {'title': 'Magnet link'})['href']
        size = tds[3].get_text()
        age = tds[4].get_text()
        try:
            peers = tds[5].find('div', title=re.compile('.*Seeders.*'))['title']
        except AttributeError:
            peers = ''
        print('{}\t{}\t{}\t{}\t{} {}'.format(size, link_text, peers, age, audio_format, languages))


def get_zooqle_suggestions(name, req_year=None):
    query_string = urllib.parse.quote_plus(name)
    results = []
    perfect_match = []
    r = requests.get(f'{domain}/search?q={query_string}')
    soup = BeautifulSoup(r.content, 'lxml')
    ul = soup.find('ul', class_='suglist')
    if not ul:
        return []
    for li in ul:
        try:
            title = li['title']
        except AttributeError:
            continue
        try:
            url = li.find('a', class_='sug')['href']
        except AttributeError:
            continue
        try:
            year = li.find('div', class_='sugInfo').get_text().split()[0]
        except AttributeError:
            year = None
        results.append({'title': title, 'year': year, 'url': f'{domain}{url}'})
        if title.lower() == name.lower() and req_year and req_year == year:
            perfect_match.append({'title': title, 'year': year, 'url': f'{domain}{url}'})
    if perfect_match:
        return perfect_match
    else:
        return results


def list_available_torrents(url):
    results = []
    res = ''
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'lxml')
    table = soup.find('table', class_='table-torrents')
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if not re.match(r'[0-9]+\.', tds[0].get_text()):
            try:
                res = tr.find('span').get_text().strip()
            except AttributeError:
                res = ''
            continue
        title = tds[1].find('a').get_text()
        link = tds[1].find('a')['href']
        try:
            audio_format = tds[1].find('span', {'title': 'Audio format'}).get_text()
        except AttributeError:
            audio_format = ''
        try:
            languages = tds[1].find('span', {'title': 'Detected languages'}).get_text().split(',')
        except AttributeError:
            languages = []
        size = tds[2].find('div', class_='prog-blue').get_text()
        age = tds[3].get_text()
        try:
            seeders = tds[4].find('div', class_='prog-green').get_text()
        except AttributeError:
            seeders = '0'
        try:
            leechers = tds[4].find('div', class_='prog-yellow').get_text()
        except AttributeError:
            leechers = '0'
        results.append({
            'title': title,
            'url': f'{domain}{link}',
            'res': res,
            'audio_format': audio_format,
            'languages': languages,
            'size': size,
            'age': age,
            'seeders': int(seeders),
            'leechers': int(leechers)
        })
    return results


def get_torrent_details(url):
    details = {}
    r = requests.get(f'{url}#mediainfo')
    soup = BeautifulSoup(r.content, 'lxml')
    dlPanel = soup.find('div', id='dlPanel')
    for a in dlPanel.find_all('a'):
        if a['href'].startswith('magnet'):
            details['magnet_link'] = a['href']
    return details
    mediainfo = soup.find('div', id='mediainfo')
    for tr in mediainfo.find_all('tr'):
        if tr.find('i', class_='zqf-movies'):
            for td in tr.find_all('td'):
                if re.match(r'[0-9]+ x [0-9]+', td.get_text()):
                    details['res'] = td.get_text()
        elif tr.find('i', class_='zqf-mi-audio'):
            audio_format = ''
            for td in tr.find_all('td'):
                if re.match(r'[0-9]+\.[0-9]+', td.get_text()):
                    audio_format = td.get_text()
                    try:
                        details['audio_format'].append(audio_format)
                    except KeyError:
                        details['audio_format'] = [audio_format]
        elif tr.find('i', class_='zqf-mi-subtitles'):
            languages = ''
            for td in tr.find_all('td'):
                if td.get_text().split()[0].strip(':') in [pref_lang, lang_full[pref_lang]]:
                    languages = td.get_text()
                    try:
                        details['languages'].append(languages)
                    except KeyError:
                        details['languages'] = [languages]
    return details


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True, help='name of movie')
    parser.add_argument('--year', default=None, help='year of release')
    args = parser.parse_args()

    # results = search_zooqle(args.name)
    results = get_zooqle_suggestions(args.name, req_year=args.year)
    print('--- matching title(s) ---')
    print(json.dumps(results, indent=2))
    results = list_available_torrents(results[0]['url'])
    print('--- top results ---')
    print(json.dumps(results[:5], indent=2))
    results[0].update(get_torrent_details(results[0]['url']))
    print('--- top result ---')
    print(json.dumps(results[0], indent=2))

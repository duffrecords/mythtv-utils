from app.config import config, intent, session
from app.logger import logger
from app.zooqle import get_zooqle_suggestions, text_to_integer
import math
import re

session.attributes = {}


def get_slot(name):
    try:
        slot = intent.slots[name].value
    except (KeyError, TypeError):
        logger.debug(f"failed to read value of slot '{name}'")
        slot = ''
    return slot


def get_suggestion(title, req_year=None):
    if not session.attributes['zooqle']['suggestions']:
        logger.debug(f'searching zooqle for {title}')
        session.attributes['zooqle']['suggestions'] = get_zooqle_suggestions(title, req_year=req_year)
    try:
        return session.attributes['zooqle']['suggestions'][0]
    except IndexError:
        return None


def format_catalog(season=None, episode=None):
    if season:
        if episode:
            return "S%sE%s" % ('{:02d}'.format(season), '{:02d}'.format(episode))
        else:
            return "Season+%s" % str(season)
    else:
        return ''


def score_by_size(torrent, prefer_high_quality=False):
    size = text_to_integer(torrent['size'])
    category = torrent['category']
    if prefer_high_quality:
        [ideal_min, ideal_max] = config.ideal_video_size[f"hd {category}"]
    else:
        [ideal_min, ideal_max] = config.ideal_video_size[category]
    delta = 0
    if size < ideal_min:
        delta = 1.0 * ((math.log(size / math.log(size+1)) + 1) + (math.log(size / math.log(size+1)) * 15) - 6) / 2
        logger.debug("\tsmaller than ideal file size: %+.2f points" % delta)
    elif size > ideal_max:
        delta = -1
        logger.debug("\tlarger than ideal file size: %+.2f points" % delta)
    elif ideal_min < size < ideal_max:
        if prefer_high_quality:
            delta = (size / 2) * math.log(size)
            logger.debug("\tideal file size: %+.2f points" % delta)
    return delta


def sort_torrents(title, torrents, category='movie', req_year=None, season=None, episode=None):
    title_variations = []
    for delimiter in [' ', '.', '-', '_']:
        variation = delimiter.join(title.split())
        logger.debug(variation)
        title_variations.append(variation)
    great_words = title_variations
    good_words = ['BrRip', 'BDRip', 'BRRip', 'BluRay', 'Bluray', 'x264', 'H.264']
    bad_words = ['DVDR', 'PAL', 'DvDrip', 'DVDrip', 'DVDscr', '480p']
    avoid_words = ['YIFY']
    if config.disable_hevc:
        avoid_words = avoid_words + ['H.265', 'h265', 'x265', 'HEVC']
    if '3D' not in title:
        avoid_words.append('3D')
    catalog = format_catalog(season=season, episode=episode)

    # categorize torrents based on resolution
    logger.debug("separating torrents by resolution")
    hd1080 = []
    hd720 = []
    other = []
    results = []
    for torrent in torrents:
        # if torrent['year'] != '':
        #     great_words.append(torrent['year'])
        if any(word in torrent['title'] for word in avoid_words):
            continue
        size = text_to_integer(torrent.get('size', 0))
        if torrent.get('category', ''):
            if size < config.strict_video_size[torrent['category']][0]:
                continue
            if size > config.strict_video_size[torrent['category']][1]:
                continue
        else:
            if size < config.strict_video_size['tv show'][0]:
                continue
            if size > config.strict_video_size['movie'][1]:
                continue
        if int(torrent.get('seeders', 0)) == 0:
            continue
        if any(torrent.get('res', '').startswith(res) for res in ['1080p', '1080i']):
            hd1080.append(torrent)
        elif ' x ' in torrent.get('res', '') and int(torrent.get('res', '').split()[-1]) > 720:
            hd1080.append(torrent)
        elif torrent.get('res', '') == '720p':
            hd720.append(torrent)
        elif ' x ' in torrent.get('res', '') and int(torrent['res'].split()[-1]) > 480:
            hd720.append(torrent)
        else:
            other.append(torrent)

    for tlist in [hd1080, hd720, other]:
        for torrent in tlist:
            logger.debug(torrent['title'])
            torrent['score'] = 0
            delta = math.log(torrent['seeders'], 16)
            logger.debug("\tnumber of seeders: %+.2f points" % delta)
            torrent['score'] += delta
            for w in great_words:
                if w in torrent['title']:
                    if w == req_year:
                        delta = 2
                    else:
                        delta = 4
                    logger.debug("\tmatched great_words: %+.2f points" % delta)
                    torrent['score'] += delta
            for w in good_words:
                if w in torrent['title']:
                    delta = 1
                    logger.debug("\tmatched good_words: %+.2f points" % delta)
                    torrent['score'] += delta
            for w in bad_words:
                if w in torrent['title']:
                    delta = -1
                    logger.debug("\tmatched bad_words: %+.2f points" % delta)
                    torrent['score'] += delta
            torrent['score'] += delta

            if season:
                delta = 2
                if episode:
                    if catalog in torrent['title']:
                        logger.debug("\tmatched season/episode: %+.2f points" % delta)
                        torrent['score'] += delta
                else:
                    if re.search(r"season[\s\.\-_]*0*%d" % season, torrent['title'], re.I):
                        logger.debug("\tmatched season: %+.2f points" % delta)
                        torrent['score'] += delta

        # sort torrents by score
        for torrent in sorted(tlist, key=lambda t: t['score'], reverse=True):
            results.append(torrent)
        logger.debug("final list contains %s torrents" % len(results))

    if category == 'tv show':
        logger.debug('merging 1080 and 720p content scores because this is a television program')
        results = sorted(results, key=lambda t: t['score'], reverse=True)

    return results

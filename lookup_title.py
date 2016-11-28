#!/usr/bin/env python

from database import Database
import sys
import re
from math import ceil

if len(sys.argv) < 2:
    print "Usage: %s movie"
    sys.exit()
else:
    title = ' '.join(sys.argv[1:])
    params = (title,)
    query = "select * from videometadata where title = %s"

blue = '\033[;34m'
white = '\033[;37m'
reset = '\033[0m'

db = Database()
metadata = db.rows_to_dicts(query, params)[0]
keys = metadata.keys()

for key in ['collectionref',
            'homepage',
            'showlevel',
            'hash',
            'childid',
            'browse',
            'watched',
            'processed',
            'playcommand',
            'category',
            'trailer',
            'host',
            'screenshot',
            'banner']:
    keys.remove(key)

for key in keys:
    tabs = '\t' * (3 - int(ceil(len(key) / 6.0)))
    print "%s%s%s:%s%s%s%s" % (blue, key, reset, tabs, white, metadata[key], reset)

#!/usr/bin/env python

from database import Database
from formatting import Formatting
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

fmt = Formatting()

db = Database()
metadata = db.rows_to_dicts(query, params)[0]
for key in ['genre', 'cast']:
    query = ("select video" + key + "." + key + " from video" + key +
            " inner join videometadata" + key +
            " on video" + key + ".intid = videometadata" + key + ".id" + key +
            " where videometadata" + key + ".idvideo = %s")
    params = (metadata['intid'],)
    metadata[key] = ', '.join([i[0].decode('latin-1', 'replace') for i in db.run_query(query, params)])
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
    print "%s%s%s:%s%s%s%s" % (fmt.header, key, fmt.reset, tabs, fmt.text, metadata[key], fmt.reset)

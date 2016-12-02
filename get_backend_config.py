#!/usr/bin/env python

import sys
from database import Database

db = Database()

if len(sys.argv) < 2:
    print "Usage: " + sys.argv[0] + " parameter"
    sys.exit()

if sys.argv[1] == 'VideosDir':
    query = ("select dirname from storagegroup "
            "where groupname='Videos'")
elif sys.argv[1] == 'CoverartDir':
    query = ("select dirname from storagegroup "
            "where groupname='Coverart'")

print(db.run_query(query, '')[0][0])

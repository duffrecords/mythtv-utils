#!/usr/bin/env python

import json
import os
import re
import sys
import shlex
import subprocess
import MySQLdb
from collections import Counter

db = MySQLdb.connect(host="localhost",
                     user="mythtv",
                     passwd="QMYSQL3",
                     db="mythconverg")
cur = db.cursor()
cur.execute("select dirname from storagegroup where groupname='Videos';")
video_dir = cur.fetchall()[0][0]
cur.execute("select filename from videometadata where contenttype='MOVIE';")
resolutions = []
for row in cur:
    #filename = re.sub(' ', '\ ', row[0])
    filename = row[0]
    full_path = os.path.join(video_dir, filename)
    cmd = '/bin/ffprobe -v quiet -print_format json -show_format -show_streams '
    args = shlex.split(cmd)
    args.append(full_path)
    #print(args)
    output,error = subprocess.Popen(args,stdout = subprocess.PIPE, stderr= subprocess.PIPE).communicate()
    #print(output)
    #output = re.sub(r'\n', '', output)
    #output = re.sub(r'"', "'", output)
    #print(output)
    output_json = json.loads(output)
    #output_json = json.loads(re.sub(r'"', "'", output_json))
    #print(output_json)
    streams = output_json['streams']
    for stream in streams:
        #print(stream)
        if stream['codec_type'] == 'video':
            width = int(stream['width'])
            height = int(stream['height'])
            #print "%s x %s" % (stream['width'], stream['height'])
            #resolution = "%sx%s" % (stream['width'], stream['height'])
            if height >= 1080:
                resolutions.append(1080)
            elif height >= 720:
                resolutions.append(720)
            elif height >= 480:
                resolutions.append(480)
            elif height >= 360:
                resolutions.append(360)
            elif height >= 240:
                resolutions.append(240)
            else:
                resolutions.append(100)
db.close()
count = zip(Counter(resolutions).keys(), Counter(resolutions).values())
count = sorted(count)
for resolution in count:
    print "%s: %s" % (resolution[0], '*' * (resolution[1] / 4))

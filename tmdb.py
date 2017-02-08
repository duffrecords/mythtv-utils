#!/usr/bin/env python

import os
from ConfigParser import SafeConfigParser

class TMDB(object):

    def __init__(self):
        configdir = os.path.dirname(os.path.realpath(__file__))
        config = SafeConfigParser()
        config.read(os.path.join(configdir, 'tmdb.conf'))
        self.key = config.get('Main', 'Key')

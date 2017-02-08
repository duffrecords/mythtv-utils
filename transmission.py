#!/usr/bin/env python

import os
from ConfigParser import SafeConfigParser

class Transmission(object):

    def __init__(self):
        configdir = os.path.dirname(os.path.realpath(__file__))
        config = SafeConfigParser()
        config.read(os.path.join(configdir, 'transmission.conf'))
        self.user = config.get('Main', 'Username')
        self.password = config.get('Main', 'Password')

#!/usr/bin/env python

import os
from ConfigParser import SafeConfigParser

class Formatting(object):

    def __init__(self):
        configdir = '.'
        config = SafeConfigParser()
        config.read(os.path.join(configdir, 'mythtv.conf'))
        header_color = config.get('Main', 'HeaderColor')
        text_color = config.get('Main', 'TextColor')
        bold_text_color = config.get('Main', 'BoldTextColor')
        ruler_color = config.get('Main', 'RulerColor')
        color_codes = {
                    'reset':        '\033[;0m',
                    'black':        '\033[0;30m',
                    'red':          '\033[0;31m',
                    'green':        '\033[0;32m',
                    'brown':        '\033[0;33m',
                    'blue':         '\033[0;34m',
                    'magenta':      '\033[0;35m',
                    'cyan':         '\033[0;36m',
                    'lightgray':    '\033[0;37m',
                    'darkgray':     '\033[1;30m',
                    'lightred':     '\033[1;31m',
                    'lightgreen':   '\033[1;32m',
                    'lightyellow':  '\033[1;33m',
                    'lightblue':    '\033[1;34m',
                    'lightmagenta': '\033[1;35m',
                    'lightcyan':    '\033[1;36m',
                    'white':        '\033[1;37m',
                    'default':      '\033[;39m',
                    'none':         ''
                    }
        self.header = color_codes[header_color]
        self.text = color_codes[text_color]
        self.boldtext = color_codes[bold_text_color]
        self.ruler = color_codes[ruler_color]
        self.reset = color_codes['default']
        self.none = color_codes['none']

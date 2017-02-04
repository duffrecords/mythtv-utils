#!/usr/bin/env python

import os
import MySQLdb
import itertools
from ConfigParser import SafeConfigParser
from collections import OrderedDict

class Database(object):

    def __init__(self):
        #configdir = '.'
        configdir = os.path.dirname(os.path.realpath(__file__))
        config = SafeConfigParser()
        config.read(os.path.join(configdir, 'mythtv.conf'))
        self.host = config.get('Main', 'Host')
        self.user = config.get('Main', 'User')
        self.password = config.get('Main', 'Password')
        self.db = config.get('Main', 'Database')
        self.connection = MySQLdb.connect(host=self.host,
                                          user=self.user,
                                          passwd=self.password,
                                          db=self.db)
        self.cursor = self.connection.cursor()

    def run_query(self, query, params):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def rows_to_dicts(self, query, params):
        self.cursor.execute(query, params)
        desc = self.cursor.description
        column_names = [col[0] for col in desc]
        return [OrderedDict(itertools.izip(column_names, row))
                for row in self.cursor]

    def close(self):
        self.connection.close()

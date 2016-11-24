#!/usr/bin/env python

import os
import MySQLdb
from ConfigParser import SafeConfigParser

class Database(object):

    def __init__(self):
        configdir = '.'
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

    def run_query(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def close(self):
        self.connection.close()

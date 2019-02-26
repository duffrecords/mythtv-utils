#!/usr/bin/env python

from app.config import config
# from configparser import SafeConfigParser
# import os
import transmissionrpc

# if 'AWS_EXECUTION_ENV' in os.environ:
#     transmission_host = os.environ['transmission_host']
#     transmission_user = os.environ['transmission_user']
#     transmission_password = os.environ['transmission_password']
# else:
#     configdir = os.path.dirname(os.path.realpath(__file__))
#     config = SafeConfigParser()
#     if os.environ.get('PROJECT_DIR', ''):
#         config_file = os.path.join(os.environ['PROJECT_DIR'], 'config.ini')
#     else:
#         config_file = 'config.ini'
#     config.read(os.path.join(configdir, config_file))
#     transmission_host = config.get('transmission', 'transmission_host')
#     transmission_user = config.get('transmission', 'transmission_user')
#     transmission_password = config.get('transmission', 'transmission_password')

transmission_client = transmissionrpc.Client(
    config.transmission_host,
    port=9091,
    user=config.transmission_user,
    password=config.transmission_password
)

# transmission_client.add_torrent(magnet_link)
# torrent1 = transmission_client.get_torrent(1)
# torrent1.progress
# torrent1.status

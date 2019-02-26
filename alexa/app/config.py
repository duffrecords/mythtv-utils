from app.logger import logger
import logging
import os
from werkzeug.local import Local

config = Local()
intent = Local()
session = Local()

if 'AWS_EXECUTION_ENV' in os.environ:
    if os.environ['log_level'] == 'debug':
        logger.setLevel(logging.DEBUG)
    elif os.environ['log_level'] == 'info':
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)
    config.ideal_video_size = {
        'movie': [float(i) * 1000000000 for i in os.environ['ideal_movie_size'].split(',')],
        'hd movie': [float(i) * 1000000000 for i in os.environ['ideal_hd_movie_size'].split(',')],
        'tv show': [float(i) * 1000000000 for i in os.environ['ideal_tv_show_size'].split(',')],
        'hd tv show': [float(i) * 1000000000 for i in os.environ['ideal_hd_tv_show_size'].split(',')]
    }
    config.strict_video_size = {
        'movie': [float(i) * 1000000000 for i in os.environ['strict_movie_size'].split(',')],
        'tv show': [float(i) * 1000000000 for i in os.environ['strict_tv_show_size'].split(',')]
    }
    config.disable_hevc = os.environ['disable_hevc']
    config.transmission_host = os.environ['transmission_host']
    config.transmission_user = os.environ['transmission_user']
    config.transmission_password = os.environ['transmission_password']
else:
    from configparser import ConfigParser
    configparser = ConfigParser()
    if os.environ.get('PROJECT_DIR', ''):
        config_file = os.path.join(os.environ['PROJECT_DIR'], 'config.ini')
    else:
        config_file = 'config.ini'
    configparser.read(config_file)
    os.environ['AWS_REGION'] = configparser.get('aws', 'aws_region')
    os.environ['log_level'] = configparser.get('main', 'log_level')
    logger.setLevel(logging.DEBUG)
    config.ideal_video_size = {
        'movie': [float(i) * 1000000000 for i in configparser.get('main', 'ideal_movie_size').split(',')],
        'hd movie': [float(i) * 1000000000 for i in configparser.get('main', 'ideal_hd_movie_size').split(',')],
        'tv show': [float(i) * 1000000000 for i in configparser.get('main', 'ideal_tv_show_size').split(',')],
        'hd tv show': [float(i) * 1000000000 for i in configparser.get('main', 'ideal_hd_tv_show_size').split(',')]
    }
    config.strict_video_size = {
        'movie': [float(i) * 1000000000 for i in configparser.get('main', 'strict_movie_size').split(',')],
        'tv show': [float(i) * 1000000000 for i in configparser.get('main', 'strict_tv_show_size').split(',')]
    }
    config.disable_hevc = bool(configparser.get('main', 'disable_hevc'))
    config.transmission_host = configparser.get('transmission', 'transmission_host')
    config.transmission_user = configparser.get('transmission', 'transmission_user')
    config.transmission_password = configparser.get('transmission', 'transmission_password')

if os.environ.get('HANDLE_ALL_EXCEPTIONS', 'false') == 'true':
    config.handle_all_exceptions = True
else:
    config.handle_all_exceptions = False
if os.environ.get('LOG_ALL_EVENTS', 'false') == 'true':
    config.log_all_events = True
else:
    config.log_all_events = False

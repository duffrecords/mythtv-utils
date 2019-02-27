#!/usr/bin/env python

from app.config import session
from configparser import ConfigParser
import datetime
import json
import os
import re
import subprocess
import uuid
import xml.etree.ElementTree as ET

session.attributes = {}


configparser = ConfigParser()
config_file = 'config.ini'
configparser.read(config_file)


def alphanumeric_hash(length=32):
    output = ''
    while len(output) <= length:
        output = output + str(uuid.uuid4()).replace('-', '')
    return output[:length]


test_events_dir = 'tests/integration/fixtures'
arn_string = configparser.get('alexa', 'arn_string')
default_timeout = 8
default_ids = {
    'userId': 'amzn1.ask.account.testUser12345',
    'deviceId': 'amzn1.ask.device.' + alphanumeric_hash(128).upper(),
    'sessionId': 'amzn1.echo-api.session.' + str(uuid.uuid4()),
    'applicationId': 'amzn1.ask.skill.' + str(uuid.uuid4()),
    'apiAccessToken': configparser.get('alexa', 'api_access_token')
}
gadget_ids = [
    'amzn1.ask.gadget.' + str(uuid.uuid4()),
    'amzn1.ask.gadget.' + str(uuid.uuid4()),
    'amzn1.ask.gadget.' + str(uuid.uuid4()),
    'amzn1.ask.gadget.' + str(uuid.uuid4()),
    'amzn1.ask.gadget.' + str(uuid.uuid4())
]


def now():
    return datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z'


def strip_xml(text):
    tree = ET.fromstring(text)
    return ET.tostring(tree, encoding='UTF-8', method='text').decode()


def say(text):
    text = re.sub(r'<sub alias="(.*)">.*<\/sub>', r'\1', text)
    plain_text = strip_xml(text)
    command = 'say -v Samantha -r 200 "{}"'.format(plain_text)
    subprocess.Popen(command, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)


def sanitize(event):
    """Fills in IDs and timestamps with default, generic data"""
    request_id = 'amzn1.echo-api.request.' + str(uuid.uuid4())
    if isinstance(event, dict):
        for k, v in event.items():
            event[k] = default_ids.get(k, v)
            if k == 'requestId':
                event[k] = request_id
            elif k == 'timestamp':
                event[k] = now()
            elif isinstance(v, dict):
                event[k] = sanitize(event[k])
    return event


def generate_event(intent_name, template='IntentRequest', slots={}, dialog_state='STARTED', button=None):
    """Generates a JSON event to be used as a request"""
    with open(os.path.join(test_events_dir, f'{template}.json'), 'r') as f:
        event = f.read()
    event = json.loads(event)
    event = sanitize(event)
    if intent_name not in ['LaunchRequest', 'GameEngine.InputHandlerEvent']:
        event['request']['intent']['name'] = intent_name
    if dialog_state:
        event['request']['dialogState'] = dialog_state
    if slots:
        event['request']['intent']['slots'] = {}
        for k, v in slots.items():
            event['request']['intent']['slots'][k] = {
                "confirmationStatus": "NONE",
                "name": k,
                "resolutions": None,
                "value": v
            }
    if intent_name == 'GameEngine.InputHandlerEvent':
        if button:
            event['request']['events'][0]['name'] = f'event_btn{button}'
            event['request']['events'][0]['inputEvents'][0]['gadgetId'] = gadget_ids[int(button)]
            event['request']['events'][0]['inputEvents'][0]['timestamp'] = now()
        else:
            event['request']['events'][0]['name'] = 'timeout'
    if session.attributes:
        event['session']['attributes'] = session.attributes
    return json.dumps(event)

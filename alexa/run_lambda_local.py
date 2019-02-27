#!/usr/bin/env python

from app.config import session
from app.core import lambda_handler
import argparse
from configparser import ConfigParser
from lambda_local.context import Context
from tests.local_lambda import alphanumeric_hash, generate_event, say, strip_xml
import uuid
import xml.dom.minidom

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--speak', action='store_true', help='speak the response using TTS')
parser.add_argument('--ssml', action='store_true', help='print full SSML output')
parser.add_argument('--verbose', action='store_true', help='enable verbose output from lambda_local module')
args = parser.parse_args()

if not args.verbose:
    print('disabling verbose logging')
    import logging
    import sys
    logging.basicConfig(stream=sys.stdout,
                        level=logging.CRITICAL,
                        format='[%(name)s - %(levelname)s - %(asctime)s] %(message)s')
    from lambda_local.main import call

session.attributes = {}

configparser = ConfigParser()
config_file = 'config.ini'
configparser.read(config_file)


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
dialog_state = ''
elicit_slot = ''

utterance = None
while True:
    if elicit_slot:
        print(f'\nelicit slot: [ {elicit_slot} ]')
    if utterance is None:
        utterance = 'launch'
    else:
        utterance = input('\nASK > ').lower()
    if utterance in ['quit', 'stop', 'exit']:
        break
    elif utterance in ['yes', 'yeah', 'ok']:
        event = generate_event('YesIntent')
    elif utterance in ['no']:
        event = generate_event('NoIntent')
    elif utterance in ['play who am i', 'launch']:
        dialog_state = ''
        event = generate_event('LaunchRequest', template='LaunchRequest', dialog_state='')
    elif utterance in ['download movie']:
        event = generate_event('DownloadIntent')
    else:
        if elicit_slot == 'title':
            dialog_state = 'IN_PROGRESS'
            elicit_slot = ''
            event = generate_event('DownloadIntent', slots={'title': utterance}, dialog_state='IN_PROGRESS')
        else:
            event = {}
    context = Context(8, arn_string=arn_string, version_name='$LATEST')
    if event:
        response_json = call(lambda_handler, event, default_timeout)
        # print(response[0])
        speech = ''
        reprompt = ''
        response = response_json[0].get('response', {})
        if response:
            if response.get('outputSpeech', {}):
                if response['outputSpeech']['type'] == 'PlainText':
                    speech = response['outputSpeech']['text']
                elif response['outputSpeech']['type'] == 'SSML':
                    speech = response['outputSpeech']['ssml']
                if response.get('reprompt', {}):
                    if response['reprompt']['outputSpeech']['type'] == 'PlainText':
                        reprompt = response['reprompt']['outputSpeech']['text']
                    elif response['reprompt']['outputSpeech']['type'] == 'SSML':
                        reprompt = response['reprompt']['outputSpeech']['ssml']
                if args.speak:
                    say(speech)
                if '<speak>' in speech:
                    if args.ssml:
                        dom = xml.dom.minidom.parseString(speech)
                        speech = dom.toprettyxml().replace('<?xml version="1.0" ?>\n', '')
                    else:
                        speech = '    ' + strip_xml(speech).replace('\n', ' ').replace('\t', '')
                print(f'\noutputSpeech:\n{speech}')
                if reprompt:
                    if '<speak>' in reprompt:
                        if args.ssml:
                            dom = xml.dom.minidom.parseString(reprompt)
                            reprompt = dom.toprettyxml().replace('<?xml version="1.0" ?>\n', '')
                        else:
                            reprompt = '    ' + strip_xml(reprompt).replace('\n', ' ').replace('\t', '')
                    print(f'\nreprompt:\n{reprompt}')
            directives = response.get('directives', [])
            for directive in directives:
                if directive.get('type', '') == 'Dialog.ElicitSlot':
                    elicit_slot = directive['slotToElicit']
            if directives:
                print('\ndirectives: {}'.format([d['type'] for d in directives]))
            if response.get('shouldEndSession', ''):
                print('')
                break

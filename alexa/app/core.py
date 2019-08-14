from app.config import config, intent, session
from app.intents.built_in import (
    StopIntent, CancelIntent, HelpIntent, PreviousIntent
)
from app.intents.torrents import (
    DownloadIntentHandler, MovieTitleHandler, YesIntentHandler, NoIntentHandler
)
from app.logger import logger
from app.ssml import join_ssml
from app.templating import render_template
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractResponseInterceptor, AbstractRequestInterceptor)
from ask_sdk_core.utils import is_request_type
from ask_sdk.standard import StandardSkillBuilder
import ask_sdk_dynamodb
import json
import os


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        session.attributes = {
            'state': '',
            'zooqle': {
                'suggestions': [],
                'results': [],
                'selected title': None,
                'selected torrent': None
            }
        }
        welcome = render_template('welcome')
        reprompt = render_template('welcome_re')
        # welcome = join_ssml([welcome, reprompt])
        handler_input.response_builder.speak(welcome).ask(reprompt)
        return handler_input.response_builder.response


class RequestLogger(AbstractRequestInterceptor):
    def process(self, handler_input):
        if os.environ['log_level'] == 'debug':
            try:
                if handler_input.request_envelope.request.object_type == 'IntentRequest':
                    intent_name = handler_input.request_envelope.request.intent.name
                else:
                    intent_name = handler_input.request_envelope.request.object_type
            except AttributeError:
                intent_name = ''
            logger.debug('intent: {}'.format(intent_name))
            if os.environ.get('LOG_ALL_EVENTS', 'false') == 'true':
                if 'AWS_EXECUTION_ENV' in os.environ:
                    logger.debug(f"Incoming request\n{handler_input.request_envelope}")
                else:
                    request = handler_input.request_envelope.to_dict()
                    request['request']['timestamp'] = str(request['request']['timestamp'])
                    logger.debug(f"Incoming request\n{json.dumps(request, indent=2)}")
        session.attributes = handler_input.attributes_manager.session_attributes
        session.user_id = handler_input.request_envelope.session.user.user_id
        try:
            intent.slots = handler_input.request_envelope.request.intent.slots
        except AttributeError:
            intent.slots = {}


class ResponseLogger(AbstractResponseInterceptor):
    def process(self, handler_input, response):
        if os.environ['log_level'] == 'debug' and os.environ.get('LOG_ALL_EVENTS', 'false') == 'true':
            if 'AWS_EXECUTION_ENV' in os.environ:
                logger.debug(f"Response: {response}")
            else:
                logger.debug(f"Response: {json.dumps(response.to_dict(), indent=2)}")
        handler_input.attributes_manager.session_attributes = session.attributes


class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(f"Encountered following exception: {exception}", exc_info=True)
        logger.error('exception type: {}'.format(type(exception)))
        logger.error('exception attributes: {}'.format(dir(exception)))
        # filename, lineno, funname, line = traceback.extract_tb(exception.__traceback__)[-1]
        # exception_type = re.sub('([a-z])([A-Z])', r'\1 \2', sys.last_type.__qualname__)
        if os.environ.get['handle_all_exceptions']:
            speech = 'The following exception occurred: {}'.format(exception.splitlines()[0])
        else:
            speech = 'An exception occurred.'
        # speech = f'{exception_type} on line {lineno} of {filename}'
        # speech = "I don't understand that. Please say it again. "
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response


def get_device_id(handler_input):
    return ask_sdk_dynamodb.partition_keygen.device_id_partition_keygen(
        handler_input.request_envelope
    )


def get_user_id(handler_input):
    return ask_sdk_dynamodb.partition_keygen.user_id_partition_keygen(
        handler_input.request_envelope
    )


class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        logger.debug(
            f"Reason for ending session: {handler_input.request_envelope.request.reason}")
        # persist_user_attributes(handler_input)
        return handler_input.response_builder.response


sb = StandardSkillBuilder(
    # table_name='whoami_user', auto_create_table=False,
    # partition_keygen=ask_sdk_dynamodb.partition_keygen.user_id_partition_keygen
)

# Add all request handlers to the skill.
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(StopIntent())
sb.add_request_handler(CancelIntent())
sb.add_request_handler(HelpIntent())
sb.add_request_handler(PreviousIntent())
sb.add_request_handler(YesIntentHandler())
sb.add_request_handler(NoIntentHandler())
# sb.add_request_handler(StartOverIntent())
# sb.add_request_handler(PauseIntent())
sb.add_request_handler(DownloadIntentHandler())
sb.add_request_handler(MovieTitleHandler())

# Add exception handler and request/response loggers to the skill.
sb.add_exception_handler(CatchAllExceptionHandler())
# sb.add_request_handler(ExceptionEncounteredRequestHandler())
sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())

# Expose the lambda handler to register in AWS Lambda.
lambda_handler = sb.lambda_handler()

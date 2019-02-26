from app.logger import logger
from app.templating import render_template
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_intent_name


class StopIntent(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.StopIntent")(handler_input)

    def handle(self, handler_input):
        """
        (STATEMENT) Handles the 'stop' built-in intention.
        """
        logger.debug('StopIntent')
        speech = render_template('stop_bye')
        handler_input.response_builder.speak(speech).set_should_end_session(True)
        return handler_input.response_builder.response


class CancelIntent(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.CancelIntent")(handler_input)

    def handle(self, handler_input):
        """
        (STATEMENT) Handles the 'cancel' built-in intention.
        """
        logger.debug('CancelIntent')
        speech = render_template('cancel_bye')
        handler_input.response_builder.speak(speech).set_should_end_session(True)
        return handler_input.response_builder.response


class HelpIntent(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        """
        (QUESTION) Handles the 'help' built-in intention.
        You can provide context-specific help here by rendering templates conditional on the help referrer.
        """
        logger.debug('HelpIntent')
        speech = render_template('help_text')
        handler_input.response_builder.speak(speech)
        return handler_input.response_builder.response


class PreviousIntent(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.PreviousIntent")(handler_input)

    def handle(self, handler_input):
        """
        (?) Handles the 'go back!'  built-in intention.
        """
        logger.debug('PreviousIntent')
        pass

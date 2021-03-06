from app.config import session
from app.dialog import generate_response, describe_torrent_result
from app.helpers import get_slot, get_suggestion, sort_torrents
from app.logger import logger
from app.templating import render_template
from app.transmission import transmission_client
from app.zooqle import list_available_torrents, get_torrent_details
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model.dialog import ElicitSlotDirective


class YesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("YesIntent")(handler_input)

    def handle(self, handler_input):
        if session.attributes['state'] == 'confirm torrent title':
            session.attributes['zooqle']['selected title'] = session.attributes['zooqle']['suggestions'][0]
            return DownloadIntentHandler().handle(handler_input)
        elif session.attributes['state'] == 'confirm torrent download':
            session.attributes['zooqle']['selected torrent'] = session.attributes['zooqle']['results'][0]
            return DownloadIntentHandler().handle(handler_input)
        else:
            speech = "I'm not sure what you mean."
            session.attributes['state'] = ''
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response


class NoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("NoIntent")(handler_input)

    def handle(self, handler_input):
        if session.attributes['state'] == 'confirm torrent title':
            session.attributes['zooqle']['selected title'] = None
            try:
                session.attributes['zooqle']['suggestions'].pop(0)
                return DownloadIntentHandler().handle(handler_input)
            except IndexError:
                speech = "Sorry, I couldn't find what you're looking for."
        elif session.attributes['state'] == 'confirm torrent download':
            session.attributes['zooqle']['selected torrent'] = None
            try:
                session.attributes['zooqle']['results'].pop(0)
                return DownloadIntentHandler().handle(handler_input)
            except IndexError:
                speech = "Sorry, I couldn't find what you're looking for."
        else:
            speech = "I'm not sure what you mean."
            session.attributes['state'] = ''
            handler_input.response_builder.speak(speech).set_should_end_session(True)
            return handler_input.response_builder.response
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response


class DownloadIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("DownloadIntent")(handler_input)

    def handle(self, handler_input):
        logger.info('user requested a download')
        title = get_slot('title')
        if not title and session.attributes['zooqle']['selected title']:
            title = session.attributes['zooqle']['selected title']['title']
        req_year = get_slot('year')
        season = get_slot('season')
        episode = get_slot('episode')
        logger.debug(f'title: {title}')
        logger.debug(f'year: {req_year}')
        logger.debug(f'season: {season}')
        logger.debug(f'episode: {episode}')
        if not title:
            logger.info('prompting user for the title of the movie/TV show')
            session.attributes['state'] = ''
            speech = "What would you like me to download?"
            reprompt = "What's the name of the movie or TV show you'd like me to download?"
            directives = [ElicitSlotDirective(slot_to_elicit='title')]
            response = generate_response(handler_input, speech=speech, reprompt=reprompt, directives=directives)
            return response
        if not session.attributes['zooqle']['selected title']:
            logger.info('asking user if this is the correct title')
            suggestion = get_suggestion(title, req_year=req_year)
            if not suggestion:
                speech = f"I couldn't find anything matching {title}."
                session.attributes['state'] = ''
                session.attributes['zooqle']['selected title'] = None
                session.attributes['zooqle']['selected torrent'] = None
            else:
                session.attributes['state'] = 'confirm torrent title'
                speech = render_template(
                    'first_suggestion',
                    category=suggestion['category'],
                    title=suggestion['title'],
                    year=suggestion['year']
                )
            handler_input.response_builder.speak(speech).ask(speech)
            return handler_input.response_builder.response
        selected_title = session.attributes['zooqle']['selected title']
        for suggestion in session.attributes['zooqle']['suggestions']:
            if suggestion['url'] == selected_title['url']:
                title_url = suggestion['url']
                category = suggestion['category']
        if not session.attributes['zooqle']['selected torrent']:
            if not session.attributes['zooqle']['results']:
                available_torrents = list_available_torrents(title_url, season=season, episode=episode)
                session.attributes['zooqle']['results'] = sort_torrents(title, available_torrents, req_year=req_year)[:5]
            torrent = session.attributes['zooqle']['results'][0]
            speech = describe_torrent_result(torrent)
            session.attributes['state'] = 'confirm torrent download'
            handler_input.response_builder.speak(speech).ask(speech)
            return handler_input.response_builder.response
        torrent = session.attributes['zooqle']['results'][0]
        details = get_torrent_details(torrent['url'])
        logger.debug(f'details: {details}')
        try:
            transmission_client.add_torrent(details['magnet_link'])
            speech = "I've added the torrent to the download queue."
            reprompt = "Is there anything else I can help you with?"
        except LookupError:
            speech = "I couldn't find the magnet link for that torrent."
            reprompt = "Would you like to try something else?"
        session.attributes['state'] = ''
        session.attributes['zooqle']['selected title'] = None
        session.attributes['zooqle']['selected torrent'] = None
        handler_input.response_builder.speak('  '.join([speech, reprompt])).ask(reprompt)
        return handler_input.response_builder.response


class MovieTitleHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("MovieTitleIntent")(handler_input)

    def handle(self, handler_input):
        title = get_slot('title')
        logger.info(f'movie title: {title}')
        return DownloadIntentHandler().handle(handler_input)

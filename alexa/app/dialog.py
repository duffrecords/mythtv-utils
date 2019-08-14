def generate_response(handler_input, speech='', reprompt='', directives=[]):
    handler_input.response_builder.speak(speech)
    if reprompt:
        handler_input.response_builder.ask(reprompt)
    for directive in directives:
        handler_input.response_builder.add_directive(directive)
    return handler_input.response_builder.response


def describe_torrent_result(torrent):
    res = torrent['res'].replace(' x ', ' by ').replace('Std', 'standard def')
    if torrent['audio_format'] == '2.0':
        audio_format = 'stereo'
    elif torrent['audio_format'] in ['7.1', '5.1']:
        audio_format = torrent['audio_format'] + ' surround'
    else:
        audio_format = torrent['audio_format']
    size = torrent['size'].replace(' MB', ' megabyte').replace(' GB', ' gigabyte')
    speech = (
        f"The best result I found is {res} resolution, {audio_format}, in a {size} file."
        "Would you like me to download it?"
    )
    return speech

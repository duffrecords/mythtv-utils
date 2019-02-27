import re

speak_tag = re.compile(r'<\/?speak>')
amp = re.compile(r'&(?![a-z]+;)')


def interjection(text):
    if not text:
        return text
    return f'<speak><say-as interpret-as="interjection">{text}</say-as></speak>'


def join_ssml(strings=[]):
    if not strings:
        return ''
    stripped = ' '.join([speak_tag.sub('', s) for s in strings])
    escaped = amp.sub('&amp;', stripped)
    return f'<speak>{escaped}</speak>'

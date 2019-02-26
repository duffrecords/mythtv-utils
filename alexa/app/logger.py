import logging
import os


class CustomFilter(logging.Filter):
    def filter(self, record):
        if record.name == "botocore.parsers" and "SecretAccessKey" in record.getMessage():
            return


AWS_FORMAT = "[%(levelname)s]\t%(asctime)s.%(msecs)dZ\t%(aws_request_id)s\t%(message)s\n"
FORMAT = "[%(levelname)s]\t%(aws_request_id)-8s\t%(message)s\n"
logger = logging.getLogger(__name__)
if 'AWS_EXECUTION_ENV' in os.environ:
    filter = CustomFilter()
    for h in logger.handlers:
        h.setFormatter(logging.Formatter(FORMAT))
        h.addfilter(filter)
    if os.environ['log_level'] == 'debug':
        logger.setLevel(logging.DEBUG)
    elif os.environ['log_level'] == 'info':
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)
else:
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_dir = os.path.abspath(os.path.dirname(__file__))
    fh = logging.FileHandler(os.path.join(log_dir, __name__ + '.log'))
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

# Python Imports
import sys
import logging
from tqdm_loggable.tqdm_logging import tqdm_logging

# Project Imports
from src import vars


class CustomFormatter(logging.Formatter):
    # Set different formats for every logging level
    time_name_stamp = "[%(asctime)s.%(msecs)03d] [" + vars.G_APP_NAME + "]"
    FORMATS = {
        logging.ERROR: time_name_stamp + " ERROR in %(module)s.py %(funcName)s() %(lineno)d - %(msg)s",
        logging.WARNING: time_name_stamp + " WARNING - %(msg)s",
        logging.CRITICAL: time_name_stamp + " CRITICAL in %(module)s.py %(funcName)s() %(lineno)d - %(msg)s",
        logging.INFO: time_name_stamp + " %(msg)s",
        logging.DEBUG: time_name_stamp + " %(funcName)s() %(msg)s",
        'DEFAULT': time_name_stamp + " %(msg)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS['DEFAULT'])
        formatter = logging.Formatter(log_fmt, '%d-%m-%Y %H:%M:%S')
        return formatter.format(record)


def innit_logger():
    global G_LOGGER

    """ Init Logging """
    G_LOGGER = logging.getLogger(vars.G_APP_NAME)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())
    G_LOGGER.addHandler(handler)

    tqdm_logging.set_level(logging.INFO)

    # Set loglevel from config
    G_LOGGER.setLevel(vars.G_LOG_LEVEL)
    handler.setLevel(vars.G_LOG_LEVEL)

    G_LOGGER.info('Started')

    return G_LOGGER


G_LOGGER = innit_logger()

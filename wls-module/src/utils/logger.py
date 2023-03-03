import sys
import logging

G_APP_NAME = 'WLS'


# Custom logging formatter
class CustomFormatter(logging.Formatter):
    # Set different formats for every logging level
    time_name_stamp = "[%(asctime)s.%(msecs)03d] [" + G_APP_NAME + "]"
    FORMATS = {
        logging.ERROR: time_name_stamp + " ERROR in %(module)s.py %(funcName)s() %(lineno)d - %(msg)s",
        logging.WARNING: time_name_stamp + " WARNING - %(msg)s",
        logging.CRITICAL: time_name_stamp + " CRITICAL in %(module)s.py %(funcName)s() %(lineno)d - %(msg)s",
        logging.INFO:  time_name_stamp + " %(msg)s",
        logging.DEBUG: time_name_stamp + " %(funcName)s() %(msg)s",
        'DEFAULT': time_name_stamp + " %(msg)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS['DEFAULT'])
        formatter = logging.Formatter(log_fmt, '%d-%m-%Y %H:%M:%S')
        return formatter.format(record)


def innit_logging():
    """ Init Logging """
    handler = logging.StreamHandler(sys.stdout)
    G_LOGGER = logging.getLogger(G_APP_NAME)
    handler.setFormatter(CustomFormatter())
    G_LOGGER.addHandler(handler)
    G_LOGGER.info('Started')

    return G_LOGGER, handler


def configure_logging(G_LOGGER, handler, wls_config, config_file):
    G_LOGGER.setLevel(wls_config['debug_level'])
    handler.setLevel(wls_config['debug_level'])
    G_LOGGER.debug(wls_config)
    G_LOGGER.info('Configuration loaded from %s' % config_file)





import logging
import os


def get_logger(name, logging_level=None, date_fmt=None):
    logging_level = logging_level or os.environ.get('LOG_LEVEL', 'info')
    #
    date_fmt = date_fmt or "%d/%m/%Y %H:%M:%s"

    levels = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
    }
    logging_level = levels.get(logging_level.lower(), logging.DEBUG)

    logger = logging.getLogger(name=name)
    logger.setLevel(logging_level)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging_level)

    # create formatter
    logging_format = "{date} %(name)s - %(levelname)s - %(message)s".format(date=" %(asctime)s -" if date_fmt else "")
    formatter = logging.Formatter(logging_format, datefmt=date_fmt)

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    # Child loggers propagate messages up to the handlers associated with their ancestor loggers, disable propagation to
    # avoid double print in cloudwatch
    logger.propagate = False

    return logger

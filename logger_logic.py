import logging


def get_file_handler(file_name, log_format, level='INFO'):
    fl_handler = logging.FileHandler(filename=file_name, encoding='utf-8')
    fl_handler.setLevel(level)
    fl_handler.setFormatter(logging.Formatter(log_format))
    return fl_handler


def get_stream_handler(log_format, level='WARNING'):
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(logging.Formatter(log_format))
    return stream_handler


def get_logger(name, def_level='INFO'):
    logger = logging.getLogger(name)
    logger.setLevel(def_level)
    logger.addHandler(get_file_handler())
    logger.addHandler(get_stream_handler())
    return logger

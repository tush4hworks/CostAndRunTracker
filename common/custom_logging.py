import logging
import sys
from logging.handlers import RotatingFileHandler

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class CustomLogger:

    @staticmethod
    def getLogger(name):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        file_handler = RotatingFileHandler(filename="logs/runs.log", maxBytes=1000000, backupCount=5)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

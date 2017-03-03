import logging
import logging.handlers
from util import config


class Logging:
    def __init__(self):
        self.level = config['Logging/level']
        self.name = config['Logging/file_name']

        logging.basicConfig(
            level=self.level,
            filename=self.name,
            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
            datefmt='%m-%d %H:%M',
        )

        # logging.handlers.RotatingFileHandler(self.name, maxBytes=5, backupCount=5)

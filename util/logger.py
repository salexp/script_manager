import logging
from util.config import Config


class Logging:
    def __init__(self):
        config = Config()
        logging.basicConfig(
            level=config['Logging/level'],
            filename=config['Logging/file_name'],
            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
            datefmt='%m-%d %H:%M',
        )

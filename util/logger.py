import sys
from datetime import datetime

import logging
import logging.handlers
from util import config


class _Logger(logging.Logger):
    result = None

    def __init__(self):
        self.level = config['Logging/level']
        self.name = config['Logging/file_name']
        logging.Logger.__init__(self, name=self.name, level=self.level)

        self.logger = logging.getLogger()
        self.logger.setLevel(self.level)
        self.logger.propagate = False

        hndlr = logging.handlers.RotatingFileHandler(self.name, maxBytes=262144, backupCount=5)
        fmrtr = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                                  datefmt='%m-%d %H:%M')
        hndlr.setFormatter(fmrtr)
        self.logger.addHandler(hndlr)

        _Logger.result = self.logger

        self.logger.info("#############################################")
        self.logger.info("Log start: {}".format(datetime.now().ctime()))


def _logger():
    if _Logger.result is None:
        _Logger()
    return _Logger.result


sys.modules['util.logger'] = _logger()

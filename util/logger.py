import os
import sys
from datetime import datetime

import logging
import logging.handlers
from util import args


class _Logger(logging.Logger):
    def __init__(self):
        base_name = os.path.basename(sys.argv[0]).replace('.py', '.log')
        self.name = base_name if not args.log_file else args.log_file
        self.level = "DEBUG" if args.debug_mode else "INFO"

        logging.Logger.__init__(self, name=self.name, level=self.level)

        name = None if args.debug_mode else 'root'
        self._logger = logging.getLogger(name)
        self._logger.setLevel(self.level)
        self._logger.propagate = False

        if not os.path.isdir('logs'):
            os.makedirs('logs')

        hndlr = logging.handlers.RotatingFileHandler('logs/' + self.name, maxBytes=262144, backupCount=5)

        fmrtr = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                                  datefmt='%m-%d %H:%M')
        hndlr.setFormatter(fmrtr)
        self._logger.addHandler(hndlr)

        if args.debug_mode:
            ch = logging.StreamHandler()
            ch.setLevel("DEBUG")
            ch.setFormatter(fmrtr)
            self._logger.addHandler(ch)

        self._logger.debug("#############################################")
        self._logger.debug("Log start: {}".format(datetime.now().ctime()))

    @property
    def logger(self):
        return self._logger


sys.modules['util.logger'] = _Logger().logger

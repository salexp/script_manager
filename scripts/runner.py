from datetime import datetime
from importlib import import_module
from util import args
from util import logger


class Script:
    def __init__(self, name):
        logger.debug("STARTING SCRIPT ({}): {}".format(datetime.now().ctime(), name))
        self.module = name if not args.test_mode else 'test'
        self.name = name

        try:
            test_module = import_module('scripts.{}.{}'.format(name, self.module))
        except ImportError:
            logger.error("Module not found: scripts/{}/{}.py".format(name, self.module))
            raise

        test_module.run()
        logger.debug("COMPLETED SCRIPT ({}): {}".format(datetime.now().ctime(), name))

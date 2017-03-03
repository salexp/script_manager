from importlib import import_module
from util import args
from util import logger


class Script:
    def __init__(self, name):
        logger.info("STARTING SCRIPT: {}".format(name))
        self.module = 'main' if not args.test_mode else 'test'
        self.name = name

        test_module = import_module('scripts.{}.{}'.format(name, self.module))
        test_module.run()
        logger.info("COMPLETED SCRIPT: {}".format(name))

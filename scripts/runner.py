from importlib import import_module
from util.args import Args


class Script:
    def __init__(self, name):
        self.module = 'main' if not Args().test_mode else 'test'
        self.name = name

        test_module = import_module('scripts.{}.{}'.format(name, self.module))
        test_module.run()

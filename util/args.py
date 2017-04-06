import os
import sys

import argparse


class _Args(argparse.ArgumentParser):
    def __init__(self):
        argparse.ArgumentParser.__init__(self)
        self.add_argument('scripts', nargs='+',
                          help='Script to run. Can be used multiple times to run multiple scripts.')
        self.add_argument('-d', action='store_true', dest='debug_mode',
                          help='Run scripts in debug mode.')
        self.add_argument('-t', action='store_true', dest='test_mode',
                          help='Run script tests.')
        self.add_argument('-c', action='store', dest='config_file',
                          help='Specifies configuration file used. Uses default.ini if not specified.')
        self.add_argument('-l', action='store', dest='log_file',
                          help='Specifies log file used. Uses {} if not specified.'.format(
                              os.path.basename(sys.argv[0]).replace('.py', '.log')))
        self.add_argument('-s', action='store', dest='script_option',
                          help='Script specific options and flags to utilize.')

        self._parsed = self.parse_args(sys.argv[1:])

    def __getattr__(self, item):
        print "Add property for completeness: {}".format(item)
        return getattr(self._parsed, item)

    @property
    def scripts(self):
        return self._parsed.scripts

    @property
    def debug_mode(self):
        return self._parsed.debug_mode

    @property
    def test_mode(self):
        return self._parsed.test_mode

    @property
    def config_file(self):
        return self._parsed.config_file

    @property
    def log_file(self):
        return self._parsed.log_file

    @property
    def script_option(self):
        return self._parsed.script_option


sys.modules['util.args'] = _Args()

import os
import sys

import argparse


class _Args(argparse.ArgumentParser):
    result = None

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

        _Args.result = self.parse_args(sys.argv[1:])


def _args():
    if _Args.result is None:
        _Args()
    return _Args.result


sys.modules['util.args'] = _args()


# Empty variables of args to support auto-completion
scripts = config_file = test_mode = None

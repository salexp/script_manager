import argparse
import sys


class _Args(argparse.ArgumentParser):
    result = None

    def __init__(self):
        argparse.ArgumentParser.__init__(self)
        self.add_argument('scripts', nargs='+',
                          help='Script to run. Can be used multiple times to run multiple scripts.')
        self.add_argument('-c', action='store', dest='config_file',
                          help='Specifies configuration file used. Uses default.ini if not specified.')
        self.add_argument('-t', action='store_true', dest='test_mode',
                          help='Run script tests.')

        _Args.result = self.parse_args(sys.argv[1:])


def _args():
    if _Args.result is None:
        _Args()
    return _Args.result


sys.modules['util.args'] = _args()


# Empty variables of args to support auto-completion
scripts = config_file = test_mode = None

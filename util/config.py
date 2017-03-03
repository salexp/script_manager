"""
$Id: configparser.py,v1.1, 2016-5-10 16:02Z, Stuart Petty$
"""
import logging
import sys
from ConfigParser import ConfigParser

from util import args

# Default configuration file to use if not specified
DEFAULT_CFG = "default.ini"


class _Config(ConfigParser):
    result = None

    def __init__(self):
        print 1
        ConfigParser.__init__(self)
        config_file = DEFAULT_CFG if args.config_file is None else args.config_file

        self.read(config_file)
        self.name = config_file

        _dict = {}
        for section in self.sections():
            _dict[section] = {}
            options = self.options(section)
            for option in options:
                key = '{}/{}'.format(section, option)
                try:
                    val = self.get(section, option)
                    while "{" in val:
                        for i in range(val.count("{")):
                            host = val[val.index("{")+1:val.index("}")]
                            val = val[:val.index("{")] + _dict['{}/{}'.format(section, host)] + val[val.index("}")+1:]

                    # Handle empty strings
                    if val == "":
                        val = "''"

                    # Store value
                    _dict[key] = eval(val)
                    _dict[section][key] = eval(val)

                    if _dict[key] == -1:
                        logging.error("skip: {}".format(option))
                except:
                    logging.error("exception on {}!".format(option))
                    _dict[key] = None

        _Config.result = _dict


def __getitem__(self, item):
    output = None
    found = item in self._dict.keys()
    if found:
        # Return found config tag
        output = self._dict[item]
    else:
        logging.warning("Unable to find config tag: {}".format(item))

    if output == {}:
        output = None

    return output


def __setitem__(self, key, value):
    logging.error("Unable to overwrite config values. Please edit config file directly.")


def _config():
    if _Config.result is None:
        _Config()
    return _Config.result


sys.modules['util.config'] = _config()

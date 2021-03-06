"""
$Id: configparser.py,v1.1, 2016-5-10 16:02Z, Stuart Petty$
"""
import sys

from ConfigParser import ConfigParser

from util import args
from util import logger

# Default configuration file to use if not specified
DEFAULT_CFG = "default.ini"


class _Config(ConfigParser):
    def __init__(self):
        self.logger = logger
        ConfigParser.__init__(self)
        config_file = DEFAULT_CFG if args.config_file is None else args.config_file

        self.read(config_file)
        self.name = config_file

        self._dict = {}
        for section in self.sections():
            self._dict[section] = {}
            options = self.options(section)
            for option in options:
                key = '{}/{}'.format(section, option)
                try:
                    val = self.get(section, option)
                    while "{" in val:
                        for i in range(val.count("{")):
                            host = val[val.index("{")+1:val.index("}")]
                            val = val[:val.index("{")] + self._dict['{}/{}'.format(section, host)] + val[val.index("}")+1:]

                    # Handle empty strings
                    if val == "":
                        val = "''"

                    # Store value
                    self._dict[key] = eval(val)
                    self._dict[section][key] = eval(val)

                    if self._dict[key] == -1:
                        self.logger.error("skip: {}".format(option))
                except:
                    self.logger.error("exception on {}!".format(option))
                    self._dict[key] = None

    def __getitem__(self, item):
        output = None
        found = item in self._dict.keys()
        if found:
            # Return found config tag
            output = self._dict[item]
        else:
            self.logger.warning("Unable to find config tag: {}".format(item))

        if output == {}:
            output = None

        return output

    def __setitem__(self, key, value):
        self.logger.error("Unable to overwrite config values. Please edit config file directly.")


sys.modules['util.config'] = _Config()

import logging
from datetime import datetime

from scripts import runner
from util import args
from util import config
from util.logger import Logging


if __name__ == "__main__":
    start = datetime.now()

    Logging()

    for script in args.scripts:
        try:
            runner.Script(script)
        except:
            logging.exception("Error running script: {}".format(script))

    print str(datetime.now() - start)

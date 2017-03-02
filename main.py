from datetime import datetime
import logging

from scripts import runner
from util.args import args
from util.config import Config
from util.logger import Logging


if __name__ == "__main__":
    start = datetime.now()

    args = args()
    Logging()
    config = Config()

    for script in args.scripts:
        try:
            runner.Script(script)
        except:
            logging.warning("Error running script: {}".format(script))

    print str(datetime.now() - start)

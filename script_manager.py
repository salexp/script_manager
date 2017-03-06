from scripts import runner
from util import args
from util import config
from util import logger


if __name__ == "__main__":
    for script in args.scripts:
        try:
            runner.Script(script)
        except:
            logger.exception("Error running script: {}".format(script))

from scripts import runner
from util import args
from util import logger
from util import config


if __name__ == "__main__":
    for script in args.scripts:
        try:
            runner.Script(script)
        except Exception as e:
            logger.exception("Error running script: {}: {}".format(script, e))

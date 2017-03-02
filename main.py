from datetime import datetime

from scripts import runner
from util.args import Args
from util.config import Config
from util.logger import Logging


def main(script):
    runner.Script(script)


if __name__ == "__main__":
    start = datetime.now()

    args = Args()
    Logging()
    config = Config()

    for script in args.scripts:
        try:
            main(script)
        except:
            pass

    print str(datetime.now() - start)

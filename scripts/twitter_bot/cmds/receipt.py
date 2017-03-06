from util import config
from util import logger


def run(cmd):
    config['foo'] = 'bar'
    logger.info(config['foo'])
    True

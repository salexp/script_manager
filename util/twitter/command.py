from util import config
from util import logger


authorized_users = config['Twitter/authorized_users']


class Command:
    def __init__(self, msg):
        self.message = msg
        self.requestor = msg.sender_screen_name
        self.text = msg.text

        key, other = self.text.partition(' ')[::2]

        self.help = '?' in key
        self.valid = '$' == key[0] and len(key) > 1

        self.key = key.replace('?', '')
        self.other = other


def parse_dm(msg):
    if msg.sender_screen_name in authorized_users:
        cmd = Command(msg)

        return cmd

    else:
        logger.info("Ignored message from: {}".format(msg.sender_screen_name))

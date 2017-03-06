from importlib import import_module
from util import config
from util import logger

authorized_users = config['Twitter/authorized_users']
commands = {
    '$r': 'receipt'
}


class Command:
    def __init__(self, msg):
        self.message = msg
        self.requester = msg.sender_screen_name
        self.text = msg.text

        key, other = self.text.partition(' ')[::2]
        value, other = other.partition(' ')[::2]

        self.help = '?' in key

        self.key = key.replace('?', '')
        self.value = value
        self.other = other

        self.known_cmd = self.key in commands
        self.valid_str = '$' == key[0] and len(key) > 1
        self.valid = self.known_cmd and self.valid_str

        if self.known_cmd:
            self.command = commands.get(self.key)
            self.module = import_module('scripts.twitter_bot.cmds.{}'.format(self.command))
        else:
            self.command = None
            self.module = None

    def clear(self):
        # self.message.destroy()
        print "DELETED"

    def run(self):
        logger.info("Beginning Twitter command: {}, {}: {}".format(self.key, self.command, self.value))
        self.module.run(self)
        logger.info("Completed Twitter command: {}, {}: {}".format(self.key, self.command, self.value))


def parse_dm(msg):
    if msg.sender_screen_name in authorized_users:
        cmd = Command(msg)

        return cmd
    else:
        logger.info("Ignored message from: {}".format(msg.sender_screen_name))

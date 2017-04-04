from importlib import import_module
from scripts.config import CmdConfig
from util import config
from util import logger

authorized_users = config['Twitter/authorized_users']
commands = {
    '$': 'skip',
    '$r': 'receipt',
}


class Command:
    def __init__(self, msg, session, force_text=None):
        self.message = msg
        self.session = session

        self.created = msg.created_at
        self.requester = msg.sender_screen_name
        self.text = msg.text if force_text is None else force_text

        key, other = self.text.partition(' ')[::2]
        value, other = other.partition(' ')[::2]

        full_key = key.ljust(3)

        self.key = full_key[0:2].rstrip()
        self.option = full_key[2].rstrip() if full_key[2] != ' ' else None
        self.value = value
        self.other = other

        self.help = '?' == self.option

        self.known_cmd = self.key in commands
        self.valid_str = '$' == key[0] and len(key) > 1
        self.valid = self.known_cmd and self.valid_str

        if self.valid:
            self.command = commands.get(self.key)
            self.module = import_module('scripts.twitter_bot.cmds.{}'.format(self.command))
            self.config = CmdConfig(command=self, file_name="{}.xml".format(self.command))
        else:
            self.command = None
            self.module = None
            self.config = None

    def clear(self):
        self.message.destroy()
        logger.info("Deleted message from: {}".format(self.requester))

    def run(self):
        logger.info("Beginning Twitter command: {} ({}), {}: {}".format(self.key, self.option, self.command, self.value))
        self.module.run(self)
        logger.info("Completed Twitter command: {} ({}), {}: {}".format(self.key, self.option, self.command, self.value))


def make_cmd_from_dm(message, session):
    if message.sender_screen_name in authorized_users:
        cmd = Command(message, session)
    else:
        logger.info("Process as skip from: {}".format(message.sender_screen_name))
        cmd = Command(message, force_text="$")
    return cmd

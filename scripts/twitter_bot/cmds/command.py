from datetime import datetime
from importlib import import_module
from scripts.config import CmdConfig
from util import config
from util import logger

authorized_users = config['Twitter/authorized_users']
commands = {
    '$': 'skip',
    '$r': 'receipt',
    '$v': 'pto',
}
server_options = {
    'payday': '$rr {} Auto-payday'.format(config['Finance/payday'])
}


class Command:
    def __init__(self, created, requestor, text, session, msg=None, force_text=None):
        self.message = msg
        self.session = session

        self.created = created
        self.requester = requestor
        self.text = text if force_text is None else force_text

        key, other = self.text.partition(' ')[::2]
        value, other = other.partition(' ')[::2]
        value = None if value == '' else value

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
        if self.message is not None:
            self.message.destroy()
            logger.info("Deleted message from: {}".format(self.requester))

    def run(self):
        logger.info("Beginning Twitter command: {} ({}), {}: {}".format(self.key, self.option, self.command, self.value))
        self.module.run(self)
        logger.info("Completed Twitter command: {} ({}), {}: {}".format(self.key, self.option, self.command, self.value))


def make_cmd_from_dm(message, session):
    created = message.created_at
    requestor = message.sender_screen_name
    text = message.text

    if message.sender_screen_name in authorized_users:
        cmd = Command(created=created, requestor=requestor, text=text, session=session, msg=message)
    else:
        logger.info("Process as skip from: {}".format(message.sender_screen_name))
        cmd = Command(created=created, requestor=requestor, text=text, session=session, msg=message, force_text="$")
    return cmd


def make_cmd_from_server(server_option, session):
    created = datetime.now()
    requestor = 'Server'

    if server_option in server_options:
        text = server_options[server_option]
        cmd = Command(created=created, requestor=requestor, text=text, session=session)
    else:
        logger.info("Process option as skip: {}".format(server_option))
        cmd = Command(created=created, requestor=requestor, text='', session=session, force_text="$")
    return cmd

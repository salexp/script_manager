import json
import requests
from requests import session
from group import GMeGroup
from message import GMeMessage
from do_not_upload import BOT_ID, GROUP_ID


class GMeBot(object):
    def __init__(self, bot_id, group_id):
        self.bot_id = bot_id
        self.group_id = group_id

        self.uri = "https://api.groupme.com/v3/bots/post"
        self.session = session()

        self._commands = {
            '!help': self.say_help
        }

        self.last_heard = None

    @property
    def commands(self):
        return self._commands

    def __post(self, data):
        self.session.post(self.uri, data=data)

    def listen(self, data):
        if data.get('sender_type') != 'bot':
            msg = GMeMessage(data=data, listening=self)
            self.last_heard = msg
            if msg.command in self.commands.keys():
                self.commands.get(msg.command)()

    def say(self, text):
        data = {'bot_id': self.bot_id, 'text': text}
        self.__post(data)

    def say_help(self):
        self.say("Commands:\n!help")


class ThugBot(GMeBot):
    def __init__(self, bot_id, group_id):
        GMeBot.__init__(self, bot_id, group_id)

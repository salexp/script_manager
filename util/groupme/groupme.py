import json
import requests
from requests import session
from group import GMeGroup
from message import GMeMessage
from do_not_upload import BOT_ID, GROUP_ID


class GMeBot:
    def __init__(self, bot_id, group_id):
        self.bot_id = bot_id
        self.group_id = group_id

        self.uri = "https://api.groupme.com/v3/bots/post"
        self.session = session()

        self.commands = {
            '!help': self.say_help
        }

        self.last_heard = None

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


class GroupMe:
    def __init__(self, auth_id):
        self.auth_id = auth_id

        self.uri = "https://api.groupme.com/v3/"
        self.session = session()

        groups = self.session.get(self._url('groups'))
        self.active = groups.status_code == 200

        self.groups = []
        self.users = {}

        if self.active:
            res = json.loads(groups.content)
            self.groups = [GMeGroup(groupme=self, dict_=_) for _ in res['response']]

    def __post(self, uri, data):
        r = self.session.post(uri, json=data)

    def _url(self, *args):
        url = self.uri + "/".join(args) + '?token=' + self.auth_id
        return url

    def find_group(self, id=None, name=None):
        found = None

        if id is None and name is None:
            raise
        elif id is not None:
            f = [g for g in self.groups if int(g.id) == int(id)]
            if len(f) == 1:
                found = f[0]
        elif name is not None:
            f = [g for g in self.groups if str(g.name) == str(name)]
            if len(f) == 1:
                found = f[0]

        return found

    def say(self, group_id, text):
        data = {'message': {"text": text, "source_guid": "PY"}}
        self.__post(self._url('groups', group_id, 'messages'), data)

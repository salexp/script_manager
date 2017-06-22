from collections import OrderedDict
from requests import session
from message import GMeMessage


class GMeBot(object):
    def __init__(self, bot_id, group_id):
        self.bot_id = bot_id
        self.group_id = group_id

        self.uri = "https://api.groupme.com/v3/bots/post"
        self.session = session()

        self._commands = OrderedDict([('!help', self.say_help)])

        self.last_heard = None

    @property
    def commands(self):
        return self._commands

    def __post(self, data):
        self.session.post(self.uri, data=data)

    def add_command(self, text, func):
        self._commands[text] = func

    def listen(self, data):
        if data.get('sender_type') != 'bot':
            msg = GMeMessage(data=data, listening=self)
            self.last_heard = msg
            if msg.command in self.commands.keys():
                self.commands.get(msg.command)()

    def say(self, text):
        data = {'bot_id': self.bot_id, 'text': text}
        self.__post(data)
        return text

    def say_help(self):
        text = "Commands:{}".format("\n".join(self.commands.keys()))
        return self.say(text)


class ThugBot(GMeBot):
    def __init__(self, bot_id, group_id):
        GMeBot.__init__(self, bot_id, group_id)

        self.add_command('picks', self.say_picks)

    def say_picks(self):
        text = "{}\n{}".format(self.last_heard.sender, ", ".join(['1.1', '2.1', '2.6', '4.1', '5.1']))
        return self.say(text)

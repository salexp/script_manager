from collections import OrderedDict
from requests import session
from message import GMeMessage
from util.sql.database import Database


class GMeBot(object):
    def __init__(self, bot_id, group_id):
        self.bot_id = bot_id
        self.group_id = group_id

        self.uri = "https://api.groupme.com/v3/bots/post"
        self.session = session()
        self.db = None

        self._commands = OrderedDict([('!help', self.say_help)])

        self.last_heard = None

    @property
    def commands(self):
        return self._commands

    def __post(self, data):
        self.session.post(self.uri, data=data)

    def add_command(self, text, func):
        self._commands[text] = func

    def listen(self, data, store=False):
        if data.get('group_id') == self.group_id:
            if self.db and store:
                query = """INSERT INTO GroupMe (GROUP_ID, CREATED_AT, USER_ID, SENDER_ID, SENDER_NAME, SENDER_TYPE,
                MESSAGE_TEXT) VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                params = (data['group_id'], data['created_at'], data['user_id'], data['sender_id'], data['name'],
                          data['sender_type'], data['text'])

                self.db.query_set(query=query, params=params)
                self.db.commit()

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
        text = "Commands:\n{}".format("\n".join(self.commands.keys()))
        return self.say(text)


class ThugBot(GMeBot):
    def __init__(self, bot_id, group_id):
        GMeBot.__init__(self, bot_id, group_id)
        self.db = Database('Fantasy', user='local', password='',
                           host='127.0.0.1', port='3306')

    def say(self, text):
        pass


class TestBot(ThugBot):
    def __init__(self, bot_id, group_id):
        ThugBot.__init__(self, bot_id, group_id)

        self.add_command('!picks', self.say_picks)

    def say(self, text):
        GMeBot.say(self, text)

    def say_picks(self):
        text = "{}\n{}".format(self.last_heard.sender, ", ".join(['1.1', '2.1', '2.6', '4.1', '5.1']))
        return self.say(text)

from collections import OrderedDict
from requests import session
from util.groupme.message import GMeMessage

from util import logger


class GMeBot(object):
    def __init__(self, bot_id, group_id):
        self.bot_id = bot_id
        self.group_id = group_id

        self.uri = "https://api.groupme.com/v3/bots/post"
        self.session = session()
        self.db = None
        self.fantasy = None

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
            logger.info("DB: %s, Store: %s" % (self.db is not None, store))
            if self.db and store:
                query = """INSERT INTO GroupMe (GROUP_ID, CREATED_AT, USER_ID, SENDER_ID, SENDER_NAME, SENDER_TYPE,
                MESSAGE_TEXT) VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                params = (data['group_id'], data['created_at'], data['user_id'], data['sender_id'], data['name'],
                          data['sender_type'], data['text'])

                logger.info("Query: %s" % query)
                logger.info("Params: %s" % ','.join(params))

                self.db.query_set(query=query, params=params)
                self.db.commit()

            if data.get('sender_type') != 'bot':
                msg = GMeMessage(data=data, listening=self)
                self.last_heard = msg
                if msg.command in self.commands.keys():
                    self.commands.get(msg.command)(msg.data['text'])

    def say(self, text):
        data = {'bot_id': self.bot_id, 'text': text}
        self.__post(data)
        return text

    def say_help(self, text):
        text = "Commands:\n{}".format("\n".join(self.commands.keys()))
        return self.say(text)

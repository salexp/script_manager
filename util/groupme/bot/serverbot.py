from datetime import datetime
from util.groupme.bot.bot import GMeBot
from util.sql.database import Database


class ServerBot(GMeBot):
    def __init__(self, bot_id, group_id):
        GMeBot.__init__(self, bot_id, group_id)
        self.db = Database('Finance', user='local', password='', host='127.0.0.1', port='3306')

        self.add_command('!time', self.say_time)

    def say_time(self):
        text = datetime.now()
        self.say(text)

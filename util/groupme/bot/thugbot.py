from fantasy.league import League
from util.groupme.bot.bot import GMeBot
from util.sql.database import Database


class ThugBot(GMeBot):
    def __init__(self, bot_id, group_id, fantasy=None):
        GMeBot.__init__(self, bot_id, group_id)
        self.db = Database('Fantasy', user='local', password='',
                           host='127.0.0.1', port='3306')

        if fantasy is None:
            self.fantasy = League(espn_id=190153, database_connection=self.db)
        else:
            self.fantasy = fantasy

    def say(self, text):
        if "COMPUTER RANKINGS" in text:
            GMeBot.say(self, text)
        else:
            pass


class TestBot(ThugBot):
    def __init__(self, bot_id, group_id):
        ThugBot.__init__(self, bot_id, group_id)

        self.add_command('!picks', self.say_picks)

    def say(self, text):
        GMeBot.say(self, text)

    def say_picks(self):
        owner = self.fantasy.find_owner(self.last_heard.sender, 'USER_GROUPME_ID')
        text = "{}'s Picks:\n{}".format(owner.initials, ", ".join(['1.1', '2.1', '2.6', '4.1', '5.1']))
        return self.say(text)

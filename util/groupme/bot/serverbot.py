from datetime import datetime
from util.groupme.bot.bot import GMeBot
from util.groupme.command.command import Command
from util.sql.database import Database


class ServerBot(GMeBot):
    def __init__(self, bot_id, group_id):
        GMeBot.__init__(self, bot_id, group_id)
        self.db = Database('Finance', user='local', password='', host='127.0.0.1', port='3306')

        self.add_command('!receipt', self.add_receipt)
        self.add_command('!time', self.say_time)

    def add_receipt(self, text):
        cmd = Command(datetime.now(), None, text=text)
        query = """INSERT INTO Receipts (RECEIPT_GROUP, RECEIPT_AMOUNT, RECEIPT_ITEM) VALUES (%s, %s, %s);"""
        self.db.query_set(query=query, params=('1', cmd.value, cmd.other))
        self.db.commit()

    def say_time(self, text):
        text = datetime.now()
        self.say(text)


if __name__ == '__main__':
    ServerBot(bot_id=123, group_id=123).add_receipt('!receipt 7.37 lunch')
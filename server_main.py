from flask import Flask, Response
from flask import json, render_template, request
from util.groupme.groupme import GMeBot
from util.groupme.do_not_upload import BOT_ID, GROUP_ID

app = Flask(__name__)
bot = GMeBot(BOT_ID, GROUP_ID)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/bot/thugbot/callback', methods=['POST'])
def thugbot_listen():
    if request.content_type == 'application/json':
        bot.listen(request.json)
        return "Heard"
    else:
        return "Ignored"


if __name__ == '__main__':
    app.run()

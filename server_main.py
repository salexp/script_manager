import argparse
from flask import Flask, Response
from flask import render_template, request
from util.groupme.bot import GMeBot
from util.groupme.do_not_upload import BOT_ID, GROUP_ID

app = Flask(__name__)
bot = GMeBot(BOT_ID, GROUP_ID)


@app.route('/')
def index():
    return Response("<div><p>Hi!</p></div>")


@app.route('/bot/thugbot/callback', methods=['POST'])
def thugbot_listen():
    if request.content_type == 'application/json':
        bot.listen(request.json)
        return "Heard"
    else:
        return "Ignored"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', action='store', dest='ip_address', nargs='?')
    parser.add_argument('-p', action='store', dest='port', nargs='?')
    args = parser.parse_args()
    app.run(host=args.ip_address, port=args.port)

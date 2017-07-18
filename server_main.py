import argparse
from flask import Flask, Response
from flask import render_template, request
from util.groupme.bot.thugbot import TestBot, ThugBot
from util.groupme.do_not_upload import BOT_ID_TEST, GROUP_ID_TEST
from util.groupme.do_not_upload import BOT_ID_THUG, GROUP_ID_THUG

from util import logger

app = Flask(__name__)
testbot = TestBot(BOT_ID_TEST, GROUP_ID_TEST)
thugbot = ThugBot(BOT_ID_THUG, GROUP_ID_THUG)


@app.route('/')
def index():
    return Response("<div><p>Hi!</p></div>")


@app.route('/bot/testbot/callback', methods=['POST'])
def testbot_listen():
    if request.content_type == 'application/json':
        testbot.listen(request.json, store=False)
        return "Heard"
    else:
        return "Ignored"


@app.route('/bot/thugbot/callback', methods=['POST'])
def thugbot_listen():
    if request.content_type == 'application/json':
        thugbot.listen(request.json, store=True)
        return "Heard"
    else:
        return "Ignored"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', action='store', dest='ip_address', nargs='?')
    parser.add_argument('-p', action='store', dest='port', nargs='?')
    args = parser.parse_args()
    try:
        app.run(host=args.ip_address, port=args.port)
    except Exception as e:
        logger.exception(e)
        raise e

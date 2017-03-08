from scripts.twitter_bot.cmds import command
from util import config
from util import logger
from util.twitter import session, do_not_upload

# Twitter authentication tokens
C_KEY = do_not_upload.C_KEY
C_SECRET = do_not_upload.C_SECRET
A_TOKEN = do_not_upload.A_TOKEN
A_TOKEN_SECRET = do_not_upload.A_TOKEN_SECRET


def run():
    with session.APISession(c_key=C_KEY, c_secret=C_SECRET, a_token=A_TOKEN, a_token_secret=A_TOKEN_SECRET)as twtr:
        for msg in twtr.direct_messages():
            cmd = command.parse_dm(msg)
            if cmd.valid:
                cmd.run()
            elif not cmd.known_cmd:
                logger.info("Command not found: {}".format(cmd.key))
            elif cmd.key == "$":
                logger.info("Skipped command from: {}".format(cmd.requester))
            else:
                logger.info("Command invalid: {}".format(cmd.text))

            cmd.clear()

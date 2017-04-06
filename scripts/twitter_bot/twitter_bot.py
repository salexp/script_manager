from datetime import datetime
from scripts.twitter_bot.cmds import command
from util.finance import payday
from util import args
from util import config
from util import logger
from util.twitter import session, do_not_upload

# Twitter authentication tokens
C_KEY = do_not_upload.C_KEY
C_SECRET = do_not_upload.C_SECRET
A_TOKEN = do_not_upload.A_TOKEN
A_TOKEN_SECRET = do_not_upload.A_TOKEN_SECRET

today = datetime.now().date()


def run():
    with session.APISession(c_key=C_KEY, c_secret=C_SECRET, a_token=A_TOKEN, a_token_secret=A_TOKEN_SECRET)as twtr:
        cmd = None
        if args.script_options is None:
            # Check for new DM commands and run
            messages = twtr.direct_messages()
            messages.reverse()
            for msg in messages:
                cmd = command.make_cmd_from_dm(msg, twtr)
        elif args.script_options == 'payday' and today in payday:
            # Reset transaction log on payday
            cmd = command.make_cmd_from_server(args.script_options, twtr)

        if cmd is not None:
            if cmd.valid:
                cmd.run()
            elif not cmd.known_cmd:
                logger.info("Command not found: {}".format(cmd.key))
            elif cmd.key == "$":
                logger.info("Skipped command from: {}".format(cmd.requester))
            else:
                logger.info("Command invalid: {}".format(cmd.text))

            cmd.clear()

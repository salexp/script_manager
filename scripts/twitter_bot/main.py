from util import config
from util import logger
from util.twitter import command, session, do_not_upload

# Twitter authentication tokens
C_KEY = do_not_upload.C_KEY
C_SECRET = do_not_upload.C_SECRET
A_TOKEN = do_not_upload.A_TOKEN
A_TOKEN_SECRET = do_not_upload.A_TOKEN_SECRET

commands = {
    '$r': 'receipt'
}


def run():
    # Establish connection
    twtr = session.APISession(c_key=C_KEY, c_secret=C_SECRET, a_token=A_TOKEN, a_token_secret=A_TOKEN_SECRET)

    for msg in twtr.direct_messages():
        cmd = command.parse_dm(msg)
        if cmd.valid and cmd.key in commands:
            True
        elif cmd.key not in commands:
            logger.info("Command not found: {}".format(cmd.key))
        else:
            logger.info("Command invalid: {}".format(cmd.text))



    user = config['Database/user']
    password = config['Database/password']
    db_name = config['Twitter/database']
    db_table = config['Twitter/table']

    # with database.Database(user=user, password=password, name=db_name) as db:
    #     db.show_all(table=db_table)

    if twtr.active:
        print "Hello World!"
    else:
        print "Goodbye World!"

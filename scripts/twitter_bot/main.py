import do_not_upload
from util import config
from util.sql import database
from util.twitter import session

# Twitter authentication tokens
C_KEY = do_not_upload.C_KEY
C_SECRET = do_not_upload.C_SECRET
A_TOKEN = do_not_upload.A_TOKEN
A_TOKEN_SECRET = do_not_upload.A_TOKEN_SECRET


def run():
    # Establish connection
    twtr = session.APISession(c_key=C_KEY, c_secret=do_not_upload.C_SECRET, a_token=A_TOKEN, a_token_secret=A_TOKEN_SECRET)

    user = config['Database/user']
    password = config['Database/password']
    db_name = config['Twitter/database']
    db_table = config['Twitter/table']

    with database.Database(user=user, password=password, name=db_name) as db:
        db.show_all(table=db_table)

    if twtr.active:
        print "Hello World!"
    else:
        print "Goodbye World!"

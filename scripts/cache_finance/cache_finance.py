from util.quandl import do_not_upload
from util.quandl.quandl import QuandlWiki

# Quandl authentication tokens
API_KEY = do_not_upload.QUANDL_API


def run():
    qw = QuandlWiki(api_key=API_KEY, database_settings={'name': 'Finance', 'user': 'local'})

    qw.update_database()

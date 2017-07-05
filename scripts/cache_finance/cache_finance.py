import datetime
from util.quandl import do_not_upload
from util.quandl.quandl import QuandlWiki

from util import args

# Quandl authentication tokens
API_KEY = do_not_upload.QUANDL_API


def run():
    qw = QuandlWiki(api_key=API_KEY, database_settings={'name': 'Finance', 'user': 'local'})

    if args.script_option.lower() == 'today':
        start_date = datetime.datetime.now().date()-datetime.timedelta(days=2)
    elif args.script_option is not None:
        start_date = datetime.datetime.strptime(args.script_option, "%Y-%m-%d").date()
    else:
        start_date = None

    qw.update_database(start_date=start_date)

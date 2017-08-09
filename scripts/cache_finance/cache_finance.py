import datetime
from util.alphavantage.do_not_upload import API_KEY as VAPI_KEY
from util.alphavantage.alphavantage import AlphaVantage
from util.finance.stock import Stock
from util.quandl.do_not_upload import QUANDL_API
from util.quandl.quandl import QuandlWiki
from util.sql.database import Database
from util.twitter.do_not_upload import C_KEY, C_SECRET, A_TOKEN, A_TOKEN_SECRET
from util.twitter.session import APISession
from util.twitter.tweet import tweets_from_list

from util import args


def run():
    db_settings = {'name': 'Finance', 'user': 'local'}
    qw = QuandlWiki(api_key=QUANDL_API, database_settings=db_settings)

    if args.script_option is not None and args.script_option.lower() == 'twitter':
        twr = APISession(C_KEY, C_SECRET, A_TOKEN, A_TOKEN_SECRET)
        for search in qw.twitter_searches:
            results = twr.search_all(search['SEARCH_TERM'], max_count=20)
            twts = tweets_from_list(results)

    elif args.script_option is not None and args.script_option.lower() == 'intraday':
        av = AlphaVantage(api_key=VAPI_KEY, database_settings=db_settings)
        start_date = datetime.datetime.now().date()
        av.update_database(tickers=qw.stock_ticker_list, start_date=start_date)

    elif args.script_option is not None and args.script_option.lower() == 'fundamentals':
        db = Database(**db_settings)
        for t in qw.stock_ticker_list:
            stock = Stock(ticker=t, database_connection=db)
            stock.download_fundamentals()
            stock.update_fundamentals_database()

    elif args.script_option is not None and '-' in args.script_option:
        start_date = datetime.datetime.strptime(args.script_option, "%Y-%m-%d").date()
        qw.update_database(start_date=start_date)

    elif args.script_option is not None and '!' in args.script_option:
        ticker = args.script_option.replace('!', '')
        av = AlphaVantage(api_key=VAPI_KEY, database_settings=db_settings)
        av.update_database(tickers=[ticker])

    if args.script_option is None:
        start_date = datetime.datetime.now().date()-datetime.timedelta(days=2)
        qw.update_database(start_date=start_date)

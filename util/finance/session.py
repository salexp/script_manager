from util.alphavantage.do_not_upload import API_KEY as VAPI_KEY
from util.alphavantage.alphavantage import AlphaVantage
from util.quandl.do_not_upload import QUANDL_API
from util.quandl.quandl import QuandlWiki
from util.sql.database import Database


class Finance:
    def __init__(self, database_settings=None, database_connection=None):
        if database_connection:
            self.db = database_connection
        elif database_settings:
            self.db = Database(**database_settings)
        else:
            raise Exception("Missing database connection")

        self.av = AlphaVantage
        self.qw = QuandlWiki

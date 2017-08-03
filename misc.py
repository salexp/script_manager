from util.finance.stock import Stock
from util.finance.multistock import MultiStock
from util.quandl.do_not_upload import QUANDL_API
from util.quandl.quandl import QuandlWiki
from util.sql.database import Database


def main():
    db_settings = {'name': 'Finance', 'user': 'local'}
    qw = QuandlWiki(api_key=QUANDL_API, database_settings=db_settings)

    db = Database(**db_settings)

    stock = MultiStock(name='multi', tickers=['GRMN', 'AAPL'], database_connection=db)
    True
    # stock = Stock(ticker='GRMN', database_connection=db)
    stock.set_data(start='2017-07-24', end='2017-07-28', intraday=True)
    chart = stock.candlestick()
    chart.show()


if __name__ == '__main__':
    main()

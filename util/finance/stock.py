import csv
import os
import urllib2
from collections import OrderedDict
from util.plotter.candlestick import Candlestick
from util.sql.database import Database


class Stock:
    def __init__(self, ticker, database_settings=None, database_connection=None):
        self.ticker = ticker

        if database_connection:
            self.db = database_connection
        elif database_settings:
            self.db = Database(**database_settings)
        else:
            raise Exception("Missing database connection")

        self._data_def = None
        self._data_set = None
        self._has_fundamentals = None

        self.fundamentals_filename = '{}_quarterly_financial_data.csv'.format(self.ticker)
        self.fundamentals_file = os.path.join('resources/fundamentals', self.fundamentals_filename)

    @property
    def data_def(self):
        return self._data_def

    @property
    def candlestick(self):
        return Candlestick(ticker=self.ticker, data=self.data_set, intraday=self.data_def['intraday'])

    @property
    def data_set(self):
        if self._data_set is None:
            query = """SELECT `TICKER`,`Datetime`,`Open`,`High`,`Low`,`Close`,`Volume` FROM Finance.Historic
                        WHERE `TICKER`='{}' AND `Intraday`='{:d}'""".format(self.ticker, int(self.data_def['intraday']))

            if self.data_def['start'] is not None:
                query += """ AND `Datetime`>='{}'""".format(self.data_def['start'])

            if self.data_def['end'] is not None:
                query += """ AND `Datetime`<='{}'""".format(self.data_def['end'])

            query += ";"

            self._data_set = self.db.query_return_dict(query=query)
        return self._data_set

    @property
    def has_fundamentals(self):
        if self._has_fundamentals is None:
            self._has_fundamentals = os.path.isfile(self.fundamentals_file)
        return self._has_fundamentals

    def download_fundamentals(self):
        url = 'http://www.stockpup.com/data/{}'.format(self.fundamentals_filename)
        try:
            fi = urllib2.urlopen(url)
            if fi.code == 200:
                with open(self.fundamentals_file, 'wb') as fo:
                    fo.write(fi.read())
                self._has_fundamentals = True
        except urllib2.HTTPError:
            pass

    def set_data(self, start=None, end=None, intraday=False):
        self._data_def = {'start': start, 'end': end, 'intraday': intraday}

    def update_fundamentals_database(self):
        if self.has_fundamentals:
            with open(self.fundamentals_file, 'rb') as csvfile:
                reader = csv.DictReader(csvfile)
                columns = [f for f in reader.fieldnames]

                for row in reader:
                    data = OrderedDict((DB_MAP[k], row[k]) for k in columns)

                    data = filter_exceptions(self.ticker, data)

                    query = """INSERT INTO Fundamentals (`TICKER`,{}) VALUES ({}) ON DUPLICATE KEY 
                    UPDATE FUNDAMENTALS_ID=FUNDAMENTALS_ID;""".format(
                        ','.join(['`{}`'.format(k) for k in data.keys()]),
                        ','.join(['%s']+['%s' for _ in data.itervalues()]))

                    self.db.query_set(query=query, params=
                        tuple([self.ticker]+[_ if _ not in ('None', 'none', 'NONE', None) else None for _ in data.itervalues()]))
                    self.db.commit()

DB_MAP = {
    'Quarter end': 'QUARTER_END',
    'Shares': 'SHARES',
    'Shares split adjusted': 'SHARES_SPLIT_ADJUSTED',
    'Split factor': 'SPLIT_FACTOR',
    'Assets': 'ASSETS',
    'Current Assets': 'CURRENT_ASSETS',
    'Liabilities': 'LIABILITIES',
    'Current Liabilities': 'CURRENT_LIABILITIES',
    'Shareholders equity': 'SHAREHOLDERS_EQUITY',
    'Non-controlling interest': 'NON-CONTROLLING_INTEREST',
    'Preferred equity': 'PREFERRED_EQUITY',
    'Goodwill & intangibles': 'GOODWILL_INTANGIBLES',
    'Long-term debt': 'LONG-TERM_DEBT',
    'Revenue': 'REVENUE',
    'Earnings': 'EARNINGS',
    'Earnings available for common stockholders': 'EARNINGS_AVAILABLE_FOR_COMMON_STOCKHOLDERS',
    'EPS basic': 'EPS_BASIC',
    'EPS diluted': 'EPS_DILUTED',
    'Dividend per share': 'DIVIDEND_PER_SHARE',
    'Cash from operating activities': 'CASH_FROM_OPERATING_ACTIVITIES',
    'Cash from investing activities': 'CASH_FROM_INVESTING_ACTIVITIES',
    'Cash from financing activities': 'CASH_FROM_FINANCING_ACTIVITIES',
    'Cash change during period': 'CASH_CHANGE_DURING_PERIOD',
    'Cash at end of period': 'CASH_AT_END_OF_PERIOD',
    'Capital expenditures': 'CAPITAL_EXPENDITURES',
    'Price': 'PRICE',
    'Price high': 'PRICE_HIGH',
    'Price low': 'PRICE_LOW',
    'ROE': 'ROE',
    'ROA': 'ROA',
    'Book value of equity per share': 'BOOK_VALUE_OF_EQUITY_PER_SHARE',
    'P/B ratio': 'P_B_RATIO',
    'P/E ratio': 'P_E_RATIO',
    'Cumulative dividends per share': 'CUMULATIVE_DIVIDENDS_PER_SHARE',
    'Dividend payout ratio': 'DIVIDEND_PAYOUT_RATIO',
    'Long-term debt to equity ratio': 'LONG-TERM_DEBT_TO_EQUITY_RATIO',
    'Equity to assets ratio': 'EQUITY_TO_ASSETS_RATIO',
    'Net margin': 'NET_MARGIN',
    'Asset turnover': 'ASSET_TURNOVER',
    'Free cash flow per share': 'FREE_CASH_FLOW_PER_SHARE',
    'Current ratio': 'CURRENT_RATIO',
}


def filter_exceptions(ticker, data):
    if ticker == 'AMAT':
        if ('P_E_RATIO', '432345564227567616') in data.items():
            data['P_E_RATIO'] = None

    return data

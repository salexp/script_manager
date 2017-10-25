import csv
import mysql.connector
import os
import urllib2
from collections import OrderedDict
from util.plotter.candlestick import Candlestick
from util.sql.database import Database

from util import logger


class Stock:
    SMA_TIMES = [5, 10, 20, 50, 100, 200]

    def __init__(self, ticker, database_settings=None, database_connection=None):
        self.ticker = ticker

        if database_connection:
            self.db = database_connection
        elif database_settings:
            self.db = Database(**database_settings)
        else:
            raise Exception("Missing database connection")

        self._data_def = None
        self._data_points = None
        self._data_set = None
        self._has_fundamentals = None
        self._sma_times = None

        self.fundamentals_filename = '{}_quarterly_financial_data.csv'.format(self.ticker)
        self.fundamentals_file = os.path.join('resources/fundamentals', self.fundamentals_filename)

    @property
    def close(self):
        return self.data_set[-1]['Close']

    @property
    def data_def(self):
        if self._data_def is None:
            e = AttributeError("Please use set_data() to define data range.")
            raise e
        return self._data_def

    @property
    def data_points(self):
        if self._data_points is None:
            self._data_points = [s['Datetime'] for s in self.data_set]
        return self._data_points

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

            data_set = self.db.query_return_dict(query=query)
            self._data_set = sorted(data_set, key=lambda k: k['Datetime'])
        return self._data_set

    @property
    def has_fundamentals(self):
        if self._has_fundamentals is None:
            self._has_fundamentals = os.path.isfile(self.fundamentals_file)
        return self._has_fundamentals

    @property
    def high(self):
        return max(d['High'] for d in self.data_set)

    @property
    def low(self):
        return min(d['Low'] for d in self.data_set)

    @property
    def open(self):
        return self.data_set[0]['Open']

    @property
    def sma_times(self):
        if self._sma_times is None:
            self._sma_times = [t for t in Stock.SMA_TIMES if t <= 0.5*len(self.data_points)][-3:]
        return self._sma_times

    @property
    def volume(self):
        return sum(d['Volume'] for d in self.data_set)

    def candlestick(self, sma=False):
        return Candlestick(ticker=self.ticker, data=self.data_set,
                           intraday=self.data_def['intraday'], sma_list=self.sma_times if sma else None)

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

    def update_fundamentals_database(self, single_quarter=False):
        count = 0
        if self.has_fundamentals:
            with open(self.fundamentals_file, 'rb') as csvfile:
                reader = csv.DictReader(csvfile)
                columns = [f for f in reader.fieldnames]

                if single_quarter:
                    reader = [[r for r in reader][0]]

                for row in reader:
                    data = OrderedDict((DB_MAP[k], row[k]) for k in columns)

                    data = filter_exceptions(self.ticker, data)

                    query = """INSERT INTO Fundamentals (`TICKER`,{}) VALUES ({}) ON DUPLICATE KEY 
                    UPDATE FUNDAMENTALS_ID=FUNDAMENTALS_ID;""".format(
                        ','.join(['`{}`'.format(k) for k in data.keys()]),
                        ','.join(['%s']+['%s' for _ in data.itervalues()]))

                    try:
                        self.db.query_set(query=query, params=
                            tuple([self.ticker]+[_ if _ not in ('None', 'none', 'NONE', None) else None for _ in data.itervalues()]))
                        self.db.commit()
                        count += 1
                    except mysql.connector.DataError as e:
                        logger.info('%s : %s' % (self.ticker, data['QUARTER_END']))
                        logger.info(e.msg)

        return count


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
        if ('QUARTER_END', '2009-07-26') in data.items():
            data['P_E_RATIO'] = None
    elif ticker == 'CSC':
        if ('QUARTER_END', '2017-03-31') in data.items():
            data['BOOK_VALUE_OF_EQUITY_PER_SHARE'] = None
            data['FREE_CASH_FLOW_PER_SHARE'] = None
    elif ticker == 'EMC':
        if ('QUARTER_END', '2003-06-30') in data.items():
            data['P_E_RATIO'] = None
    elif ticker == 'ESRX':
        if ('QUARTER_END', '2008-09-30') in data.items():
            data['CURRENT_RATIO'] = None
    elif ticker == 'ETN':
        if ('QUARTER_END', '1995-06-30') in data.items():
            data['CURRENT_RATIO'] = None
    elif ticker == 'NTAP':
        if ('QUARTER_END', '2002-04-26') in data.items():
            data['P_E_RATIO'] = None
    elif ticker == 'NUE':
        if ('QUARTER_END', '2000-07-01') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '2000-04-01') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1999-10-02') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1999-07-03') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1998-12-31') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1998-10-03') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1998-07-04') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1998-04-04') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1997-10-04') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1997-07-05') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1997-04-05') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1996-12-31') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1996-09-28') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1996-06-29') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1996-03-30') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1995-12-31') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1995-09-30') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1995-07-01') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1995-04-01') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1994-12-31') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1994-10-01') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1994-07-02') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
        if ('QUARTER_END', '1994-04-02') in data.items():
            data['FREE_CASH_FLOW_PER_SHARE'] = None
    elif ticker == 'NWL':
        if ('QUARTER_END', '2005-09-30') in data.items():
            data['P_E_RATIO'] = None
    elif ticker == 'RDC':
        if ('QUARTER_END', '2015-09-30') in data.items():
            data['P_E_RATIO'] = None
    elif ticker == 'THC':
        if ('QUARTER_END', '2001-11-30') in data.items():
            data['CURRENT_RATIO'] = None
        if ('QUARTER_END', '2000-11-30') in data.items():
            data['CURRENT_RATIO'] = None
        if ('QUARTER_END', '2000-08-31') in data.items():
            data['CURRENT_RATIO'] = None
    elif ticker == 'TMO':
        if ('QUARTER_END', '2002-03-30') in data.items():
            data['P_E_RATIO'] = None
    elif ticker == 'VRSN':
        if ('QUARTER_END', '2000-03-31') in data.items():
            data['P_E_RATIO'] = None
    elif ticker == 'WYNN':
        if ('QUARTER_END', '2013-12-31') in data.items():
            data['P_B_RATIO'] = None
    elif ticker == 'ANR':
        if ('QUARTER_END', '2007-12-31') in data.items():
            data['P_E_RATIO'] = None
    elif ticker == 'ASH':
        if ('QUARTER_END', '2013-09-30') in data.items():
            data['P_E_RATIO'] = None
    elif ticker == 'CIEN':
        if ('QUARTER_END', '2007-01-31') in data.items():
            data['P_E_RATIO'] = None
    elif ticker == 'SAPE':
        if ('QUARTER_END', '2004-06-30') in data.items():
            data['P_E_RATIO'] = None
    elif ticker == 'UIS':
        if ('QUARTER_END', '1997-09-30') in data.items():
            data['P_E_RATIO'] = None
    elif ticker == 'WEN':
        if ('QUARTER_END', '2013-06-30') in data.items():
            data['P_E_RATIO'] = None
    elif ticker == 'GRA':
        if ('QUARTER_END', '2000-03-31') in data.items():
            data['CURRENT_RATIO'] = None

    return data

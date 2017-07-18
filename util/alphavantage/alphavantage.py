import json
from requests import session
from util.sql.database import Database

from util import logger


class AlphaVantage:
    def __init__(self, api_key, database_settings):
        self.api_key = api_key

        self.db = Database(**database_settings)

        self.uri = "https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={}&interval=1min&outputsize=full&apikey="

        self.session = session()

    def _get(self, uri, **kwargs):
        r = self.session.get(uri, **kwargs)
        return r

    def _url(self, symbol):
        url = self.uri.format(symbol) + self.api_key
        return url

    def download_intraday(self, ticker):
        url = self._url(ticker)
        r = self._get(url)

        if r.status_code == 200:
            data = json.loads(r.content)
            return data

    def update_database(self, tickers):
        for tick in tickers:
            data = self.download_intraday(tick)
            if 'Error Message' not in data.keys():
                data_set = data['Time Series (1min)']

                all_data_set = []
                for k, v in data_set.items():
                    set = [tick, k, v['1. open'], v['2. high'], v['3. low'], v['4. close'], v['5. volume']]
                    all_data_set.append(set)

                query = """INSERT INTO Historic (`TICKER`,`Datetime`,`Open`,`High`,`Low`,`Close`,`Volume`,`Intraday`) VALUES 
                (%s, %s, %s, %s, %s, %s, %s, 1) ON DUPLICATE KEY UPDATE HISTORIC_ID=HISTORIC_ID;"""

                if all_data_set:
                    self.db.query_set_many(query=query, params=all_data_set)
                    self.db.commit()

        logger.info("Cached intraday for %s tickers." % len(tickers))

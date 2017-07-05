import csv
import json
import os
import time
import zipfile
from requests import session
from util.sql.database import Database

from util import logger


class Quandl:
    def __init__(self, api_key, data_set, database_settings):
        self.api_key = api_key
        self.data_set = data_set

        self.db = Database(**database_settings)

        self.uri = "https://www.quandl.com/api/v3/datasets/{}/".format(data_set)
        self.meta_uri = "https://www.quandl.com/api/v3/databases/{}/".format(data_set)
        self.session = session()

    def _get(self, uri, **kwargs):
        r = self.session.get(uri, **kwargs)
        return r

    def _post(self, uri, data, **kwargs):
        r = self.session.post(uri, json=data, **kwargs)
        return r

    def _url(self, *args):
        url = '{}{}'.format(self.uri, "/".join(args))
        arg_key = '&' if '?' in url else '?'
        url_key = "{}{}api_key={}".format(url, arg_key, self.api_key)
        return url_key

    def _meta_url(self, *args):
        url = self.meta_uri + "/".join(args) + '?api_key=' + self.api_key
        return url

    def download_codes(self, outfile='codes.zip', extract=True):
        r = self.session.get(self._meta_url('codes.json'), stream=True)
        with open(os.path.join('resources', outfile), 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        if extract:
            zip_ref = zipfile.ZipFile(outfile, 'r')
            zip_ref.extractall('resources')
            zip_ref.close()


class QuandlWiki(Quandl):
    def __init__(self, api_key, database_settings):
        Quandl.__init__(self, api_key=api_key, data_set='WIKI', database_settings=database_settings)

        self._last_updated = None
        self._stock_ticket_list = None

    @property
    def last_updated(self):
        if self._last_updated is None:
            query = """SELECT MAX(Date) AS Date FROM Finance.Historic;"""
            result = self.db.query_return(query=query)
            self._last_updated = result[0][0]
        return self._last_updated

    @property
    def stock_ticker_list(self):
        if self._stock_ticket_list is None:
            infile = os.path.join('resources', 'WIKI-datasets-codes.csv')
            if not os.path.isfile(infile):
                self.download_codes()

            with open(infile, 'rb') as f:
                cf = csv.reader(f)
                items = [_ for _ in cf]

            self._stock_ticket_list = [_[0].replace('WIKI/', '') for _ in items]

        return self._stock_ticket_list

    def download_company_data(self, ticker, start_date=None):
        if start_date is None:
            url = self._url(ticker, 'data.json')
        else:
            url = self._url(ticker, 'data.json?start_date={}'.format(start_date))
        r = self._get(url)

        if r.status_code == 429:
            logger.info(r.content)
            time.sleep(1.0)
            r = self._get(url)

        if r.status_code == 200:
            data = json.loads(r.content)
            return data

    def update_database(self, start_date=None):
        tickers = self.stock_ticker_list

        for tick in tickers:
            data = self.download_company_data(ticker=tick, start_date=start_date)

            data_set = data['dataset_data']['data']
            all_data_set = tuple([[tick] + [str(_[0])] + _[1:] for _ in data_set])

            query = """INSERT INTO Historic (`TICKER`,{}) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE HISTORIC_ID=HISTORIC_ID;""".format(
                ','.join(['`{}`'.format(_) for _ in data['dataset_data']['column_names']])
            )

            if all_data_set:
                self.db.query_set_many(query=query, params=all_data_set)
                self.db.commit()

            logger.info("Done: %s, %s" % (tick, len(all_data_set)))

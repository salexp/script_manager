from util.finance.stock import Stock


class MultiStock(Stock):
    def __init__(self, name, tickers, database_settings=None, database_connection=None):
        self.name = name
        self.tickers = tickers

        Stock.__init__(self, ticker=name, database_settings=database_settings, database_connection=database_connection)

        stocks = {}
        for ticker in tickers:
            stocks[ticker] = Stock(ticker=ticker, database_connection=database_connection, database_settings=database_settings)

        self.stocks = stocks

        self._data_set = None

    @property
    def data_set(self):
        if self._data_set is None:
            all_data_sets = [s.data_set for _, s in self.stocks.items()]
            all_data_set_dicts = []
            for i, ds in enumerate(all_data_sets):
                all_data_set_dicts.append({})
                for d in ds:
                    all_data_set_dicts[i][d['Datetime']] = d

            all_datetimes = [d['Datetime'] for sets in all_data_sets for d in sets]
            trim_datetimes = sorted(set([d for d in all_datetimes if all_datetimes.count(d)==len(all_data_sets)]))

            self._data_set = []
            for tdt in trim_datetimes:
                self._data_set.append({})
                date_data_set = [ds[tdt] for ds in all_data_set_dicts]
                self._data_set[-1]['Datetime'] = tdt
                for key in ['Open', 'Close', 'High', 'Low', 'Volume']:
                    self._data_set[-1][key] = sum(_[key] for _ in date_data_set)

        return self._data_set

    def set_data(self, *args, **kwargs):
        Stock.set_data(self, *args, **kwargs)
        for _, stock in self.stocks.items():
            stock.set_data(*args, **kwargs)

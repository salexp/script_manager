import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY, date2num, num2date
from matplotlib.finance import candlestick_ohlc
from util.sql.database import Database


class Candlestick:
    def __init__(self, ticker, database_settings, intraday=True, start=None, end=None):
        db = Database(**database_settings)

        query = """SELECT `TICKER`,`Datetime`,`Open`,`High`,`Low`,`Close`,`Volume` FROM Finance.Historic
            WHERE `TICKER`='{}' AND `Intraday`='{:d}'""".format(ticker, int(intraday))

        if start is not None:
            query += """ AND `Datetime`>='{}'""".format(start)

        if end is not None:
            query += """ AND `Datetime`<='{}'""".format(end)

        query += ";"

        data = db.query_return_dict(query=query)
        quotes = [(date2num(d['Datetime']),
                   d['Open'],
                   d['High'],
                   d['Low'],
                   d['Close'],
                   d['Volume'])for d in data]

        weekday_quotes = [tuple([i] + list(quote[1:])) for i, quote in enumerate(quotes)]

        fig, ax = plt.subplots()
        fig.subplots_adjust(bottom=0.2)
        ax.xaxis.set_major_locator(WeekdayLocator(MONDAY))
        ax.xaxis.set_minor_locator(DayLocator())
        ax.xaxis.set_major_formatter(DateFormatter('%b %d'))

        candlestick_ohlc(ax=ax, quotes=weekday_quotes, width=0.00075)

        ax.set_xticks(range(0, len(weekday_quotes), 5))

        ax.xaxis_date()
        ax.autoscale_view()

        plt.show()


if __name__ == '__main__':
    db_settings = {'name': 'Finance', 'user': 'local'}
    graph = Candlestick('GRMN', db_settings)

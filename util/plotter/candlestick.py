import datetime
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY, date2num, num2date
from matplotlib.finance import candlestick_ohlc
from matplotlib.ticker import FormatStrFormatter
from util.sql.database import Database
from util.utilities import *


class Candlestick:
    def __init__(self, ticker, data, intraday=False):
        quotes = [(date2num(d['Datetime']),
                   d['Open'],
                   d['High'],
                   d['Low'],
                   d['Close'],
                   d['Volume'])for d in data]

        weekday_quotes = [tuple([i] + list(quote[1:])) for i, quote in enumerate(quotes)]

        fig, ax = plt.subplots()
        fig.subplots_adjust(bottom=0.2)

        ax.set_title(ticker)
        ax.yaxis.set_major_formatter(FormatStrFormatter('$%.2f'))
        ax.yaxis.grid(True)

        ax.xaxis_date()
        ax.set_xticks(range(0, len(weekday_quotes), len(weekday_quotes) / 10 if len(weekday_quotes) >= 10 else 1))
        fig.autofmt_xdate()

        if intraday:
            bar_width = 0.0005
            ax.set_xticklabels([num2date(quotes[index][0]).strftime('%d-%b %H:%M') for index in ax.get_xticks()])
        else:
            bar_width = 0.6
            ax.set_xticklabels([num2date(quotes[index][0]).strftime('%d-%b-%y') for index in ax.get_xticks()])

        ls, rs = candlestick_ohlc(ax=ax, quotes=weekday_quotes, width=bar_width, colorup='#77d879', colordown='#db3f3f')

        if not intraday:
            for r in rs:
                r.set_antialiased(False)
                r.set_edgecolor('black')
                r.set_linewidth(bar_width)

        for l in ls:
            l.set_color('black')
            l.set_zorder(0)

        ax.autoscale_view()

        self.ax = ax
        self.fig = fig

    def show(self):
        plt.show()

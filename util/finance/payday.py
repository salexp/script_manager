import datetime
import sys
from util import logger

try:
    import dateutil.parser as dp
    import dateutil.relativedelta as drel
    import dateutil.rrule as dr
except ImportError:
    logger.error("Install dateutil: >pip install pyton-dateutil")


class Paydays:
    def __init__(self):
        self.today = datetime.datetime.now().date()
        year = self.today.year

        if year < 2021 or 2027 < year:
            day = 1
        else:
            day = 7
        d = datetime.date(year, 1, day)
        start_date = self._next_weekday(3, d)
        start = dp.parse(str(start_date))

        rr = dr.rrule(dr.WEEKLY, dtstart=start, count=54)
        self.paydays = [_.date() for _ in rr[::2]]

    def __getitem__(self, item):
        return self.paydays[item]

    def _next_weekday(self, weekday, day=None):
        import datetime
        if day is None:
            day = self.today
        days_ahead = weekday - day.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return day + datetime.timedelta(days=days_ahead)

    @property
    def days_next(self):
        td = self.next - self.today
        return td.days

    @property
    def next(self):
        next_ = self._next_weekday(3)
        if next_ not in self.paydays:
            next_ = self._next_weekday(3, next_)

        return next_


sys.modules['util.finance.payday'] = Paydays()

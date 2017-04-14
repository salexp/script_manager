import datetime
import sys
from util import config
from util import logger

try:
    import dateutil.parser as dp
    import dateutil.relativedelta as drel
    import dateutil.rrule as dr
except ImportError:
    logger.error("Install dateutil: >pip install python-dateutil")


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

        pto_start = config['Finance/pto_start']
        pto_startdate = datetime.datetime.strptime(config['Finance/pto_startdate'],
                                                   '%m/%d/%Y').date()
        self.pto_rate = config['Finance/pto_rate']

        rrpd = dr.rrule(dr.WEEKLY, dtstart=pto_startdate, count=54)
        self.ptodays = {_.date(): pto_start+i*self.pto_rate for i, _ in enumerate(rrpd)}

        self._next = None
        self._previous = None

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

    def _prev_weekday(self, weekday, day=None):
        import datetime
        if day is None:
            day = self.today
        days_ahead = weekday - day.weekday()
        if days_ahead >= 0:
            days_ahead -= 7
        return day + datetime.timedelta(days=days_ahead)

    @property
    def days_next(self):
        td = self.next - self.today
        return td.days

    @property
    def next(self):
        if self._next is None:
            next_ = self._next_weekday(3)
            if next_ not in self.paydays:
                next_ = self._next_weekday(3, next_)

            self._next = next_

        return self._next

    def next_by_date(self, start_date):
        next_ = self._next_weekday(3, day=start_date)
        if next_ not in self.paydays:
            next_ = self._next_weekday(3, next_)

        return next_

    def next_pto_by_date(self, start_date):
        next_ = self._next_weekday(5, day=start_date)
        if next_ not in self.ptodays:
            next_ = self._next_weekday(5, next_)

        return next_

    @property
    def previous(self):
        if self._previous is None:
            prev = self._prev_weekday(3)
            if prev not in self.paydays:
                prev = self._prev_weekday(3, prev)

            self._previous = prev

        return self._previous

    def previous_by_date(self, start_date):
        prev = self._prev_weekday(3, day=start_date)
        if prev not in self.paydays:
            prev = self._prev_weekday(3, prev)

        return prev

    def previous_pto_by_date(self, start_date):
        prev = self._prev_weekday(5, day=start_date)
        if prev not in self.ptodays:
            prev = self._prev_weekday(5, prev)

        return prev


sys.modules['util.finance.payday'] = Paydays()

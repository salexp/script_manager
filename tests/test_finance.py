from datetime import date, datetime
from util.finance import payday


def test_paydays():
    assert payday.today == datetime.now().date()
    assert payday.next == payday.next_by_date(datetime.now().date())
    assert payday.previous == payday.previous_by_date(datetime.now().date())

    test_date = date(2017, 10, 29)
    assert payday.next_by_date(test_date) == date(year=2017, month=11, day=9)
    assert payday.previous_by_date(test_date) == date(year=2017, month=10, day=26)

    test_date = date(2018, 12, 25)
    assert payday.next_by_date(test_date) == date(year=2019, month=1, day=3)
    assert payday.previous_by_date(test_date) == date(year=2018, month=12, day=20)

    test_date = date(2018, 12, 30)
    assert payday.next_pto_by_date(test_date) == date(year=2019, month=1, day=5)
    assert payday.previous_pto_by_date(test_date) == date(year=2018, month=12, day=29)

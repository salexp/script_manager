import time
from datetime import date, datetime
from tweepy import TweepError
from util import logger
from util.finance import payday


def run(cmd):
    value = cmd.value
    if value is not None:
        month, dayyear = value.partition('/')[::2]
        day, year = dayyear.partition('/')[::2]
        if year in ('', None):
            year = payday.today.year
    else:
        month, day, year = payday.today.month, payday.today.day, payday.today.year
        
    value_mdy = '/'.join(str(_) for _ in [month, day, year])
    tweet_text = None

    if cmd.option is None:
        # Get predicted PTO hours for a date
        check_date = date(year=int(year), month=int(month), day=int(day))

        pto_hours = get_hours(cfg=cmd.config, check_date=check_date)

        tweet_text = "{:.3f} hours available on {}".format(pto_hours, check_date)
    elif cmd.option == 'a':
        # Add scheduled PTO
        amount, description = cmd.other.partition(' ')[::2]

        tweet_text = add_pto(command=cmd, value=amount, date=value_mdy, description=description)
    elif cmd.option == 'd':
        # Delete scheduled PTO
        pass
    elif cmd.option == 'l':
        # List all scheduled PTO
        pass
    else:
        logger.info("Unknown option for pto: {}".format(cmd.option))

    if tweet_text is not None:
        try:
            tweet = cmd.session.update_status(tweet_text)
        except TweepError:
            cmd.session.clear_timeline()
            tweet = cmd.session.update_status(tweet_text)


def add_pto(command, value, date, description):
    command.config.add_element('PTO', value,
                               {'description': description, 'date': date})
    command.config.save()

    pto_date = datetime.strptime(date, '%m/%d/%Y').date()
    tweet_text = "Scheduled {} hours of PTO on {}.\nAvailable: {:.3f}".format(value, date, get_hours(command.config, pto_date))

    return tweet_text


def get_hours(cfg, check_date):
    pto_date = payday.previous_pto_by_date(check_date)
    base_amount = payday.ptodays[pto_date]

    scheduled = []
    for entry in cfg.root.findall('PTO'):
        entry_date = datetime.strptime(entry.attrib['date'], '%m/%d/%Y').date()
        if entry_date <= check_date:
            scheduled.append(entry.pyval)

    pto_hours = base_amount - sum(scheduled)
    return pto_hours


def get_sum(cfg):
    sum_ = 0
    sum_ += sum([_.pyval for _ in cfg.root.findall('PTO')])
    return sum_
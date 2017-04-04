from util import config
from util import logger
from util.finance import payday
from util.sql import database


def run(cmd):
    value = float(cmd.value.replace('$', ''))

    if cmd.option is not None:
        if cmd.option == 'r':
            # Reset transactions
            cmd.config.reset()
            cmd.config.add_element('Reset', value,
                                   {'description': cmd.other, 'datetime': cmd.created})
            cmd.config.save()
        else:
            logger.info("Unknown option for receipt: {}".format(cmd.option))
    else:
        cmd.config.add_element('Transaction', value,
                               {'description': cmd.other, 'datetime': cmd.created})
        cmd.config.save()

    sum_ = cmd.config.root.find('Reset').pyval
    sum_ += sum([0-_.pyval for _ in cmd.config.root.findall('Transaction')])

    tweet_text = "${} available for next {} days, ${:.2f}/day".format(
        sum_,
        payday.days_next,
        sum_/payday.days_next)

    tweet = cmd.session.update_status(tweet_text)

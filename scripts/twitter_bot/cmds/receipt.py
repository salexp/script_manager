from util import config
from util import logger
from util.finance import payday
from util.sql import database


def run(cmd):
    value = float(cmd.value.replace('$', ''))
    tweet_text = None

    if cmd.option is None:
        # Add reciept to current list of transactions
        tweet_text = add_receipt(command=cmd, value=value)
    elif cmd.option == 'e':
        # Edit last transaction
        transactions = cmd.config.root.findall('Transaction')
        if transactions:
            latest = transactions[-1]
            add_receipt(command=cmd, value=0-latest.pyval, description="Edit previous")
            tweet_text = add_receipt(command=cmd, value=value)
    elif cmd.option == 'r':
        # Reset transactions
        previous_sum = get_sum(cfg=cmd.config)

        cmd.config.reset()
        cmd.config.add_element('Reset', value,
                               {'description': cmd.other, 'datetime': cmd.created})
        cmd.config.save()

        tweet_text = "${} available for next {} days, ${:.2f}/day. Spent ${} last period".format(
            value,
            payday.days_next+1,
            value/(payday.days_next+1),
            previous_sum
        )
    else:
        logger.info("Unknown option for receipt: {}".format(cmd.option))

    if tweet_text is not None:
        tweet = cmd.session.update_status(tweet_text)


def add_receipt(command, value, description=None):
    if description is None:
        description = command.other

    command.config.add_element('Transaction', value,
                               {'description': description, 'datetime': command.created})
    command.config.save()

    sum_ = get_sum(cfg=command.config)
    tweet_text = "${} available for next {} days, ${:.2f}/day".format(
        sum_,
        payday.days_next,
        sum_/payday.days_next if payday.days_next > 0 else 0
    )

    return tweet_text


def get_sum(cfg):
    sum_ = cfg.root.find('Reset').pyval
    sum_ += sum([0 - _.pyval for _ in cfg.root.findall('Transaction')])
    return sum_

"""
Thug Island Fantasy League Stats and Computer Rankings - Stuart Petty (stu.petty92@gmail.com)
Created for 2016 season
"""
import argparse
import time
from datetime import datetime
from fantasy.league import League
from util.groupme.bot.thugbot import TestBot, ThugBot
from util.groupme.do_not_upload import *


DEBUG = False

CURRENT_WEEK = 3

FULL_HISTORY = False
DOWNLOAD_GAMES = False
GROUP_ME = False

FUTURE_PLAYOFFS = False


def main():
    thug_island = League(
        espn_id=190153,
        database_settings={'name': 'Fantasy', 'user': 'local'},
        resources_folder='fantasy/resources',
        update_resources=DOWNLOAD_GAMES,
        full_update=FULL_HISTORY,
        current_week=CURRENT_WEEK
    )

    del thug_island.owners["Cody Blain"]

    thug_island.recursive_rankings(playoffs=FUTURE_PLAYOFFS)

    thug_island.to_string(
        outfile="ff_data.txt",
        title=True,
        games=True,
        mtchups=True,
        owners=False,
        plyffs=False,
        power=True,
        seasons=False,
        rcds=False
    )

    thug_island.to_string(
        outfile="ff_data_records.txt",
        title=False,
        games=True,
        mtchups=False,
        owners=True,
        plyffs=False,
        power=False,
        seasons=True,
        rcds=50
    )

    if DEBUG:
        with open("ff_data.txt", "r") as f:
            with open("fantasy/resources/ff_data_base.txt", "r") as fb:
                broken = f.read() == fb.read()
                assert not broken

    if GROUP_ME:
        thug_bot = ThugBot(bot_id=BOT_ID_THUG, group_id=GROUP_ID_THUG, fantasy=thug_island)
        bot_says = "COMPUTER RANKINGS:\n" + thug_island.power_rankings_simple
        yes = raw_input("Confirm posting to GroupMe (Y): ")
        if yes.lower() in ('y', 'yes'):
            thug_bot.say(bot_says)

    True


def check_transactions(group_me=True, wait_time=300.0):
    thug_island = League(
        espn_id=190153,
        database_settings={'name': 'Fantasy', 'user': 'local'},
        resources_folder='fantasy/resources',
        update_resources=DOWNLOAD_GAMES,
        full_update=FULL_HISTORY,
        current_week=CURRENT_WEEK
    )

    thug_bot = ThugBot(bot_id=BOT_ID_TEST, group_id=GROUP_ID_TEST, fantasy=thug_island)

    while True:
        for transaction in thug_island.get_new_transactions():
            if 'trade' in transaction.get('type', 'none').lower() and group_me:
                bot_says = "TRADE ALERT:\n" + transaction.get('text')
                thug_bot.say(bot_says)
            elif group_me:
                bot_says = "TRANSACTION:\n" + transaction.get('text')
                # thug_bot.say(bot_says)

        time.sleep(float(wait_time))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-t', '--check-trades', action='store', dest='trades', default=None,
                        help='Check and post recent trades..')

    args, leftovers = parser.parse_known_args()

    if args.trades is not None:
        check_transactions(wait_time=args.trades)
    else:
        main()

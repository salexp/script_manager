"""
Thug Island Fantasy League Stats and Computer Rankings - Stuart Petty (stu.petty92@gmail.com)
Created for 2016 season
"""
import argparse
import logging
import os
import time
from fantasy.league import League
from util.groupme.bot.serverbot import ServerBot
from util.groupme.bot.thugbot import TestBot, ThugBot
from util.groupme.do_not_upload import *


DEBUG = False

CURRENT_WEEK = 4

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
    server_bot = ServerBot(BOT_ID_SERVER, GROUP_ID_SERVER)

    try:
        logger.info("Starting transaction monitoring...")
        while True:
            for transaction in thug_island.get_new_transactions():
                if 'trade' in transaction.get('type', 'none').lower() and group_me:
                    bot_says = "TRADE ALERT:\n" + transaction.get('text')
                    logger.info("Trade: %s" % transaction.get('text').split()[0])
                    thug_bot.say(bot_says)
                    server_bot.say(bot_says)
                elif group_me:
                    bot_says = "TRANSACTION:\n" + transaction.get('text')
                    logger.info("Transaction: %s" % transaction.get('text').split()[0])
                    server_bot.say(bot_says)

            time.sleep(float(wait_time))
    except Exception as ex:
        logger.exception(ex)
        exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-t', '--check-trades', action='store', dest='trades', default=None,
                        help='Check and post recent trades..')

    args, leftovers = parser.parse_known_args()

    # Setup log file
    logging.basicConfig()
    logger = logging.getLogger('gbench_convert')
    logger.setLevel(logging.INFO)
    logger.propagate = False

    try:
        hndlr = logging.FileHandler('logs/thug_island_data.log')
    except IOError:
        os.makedirs('logs')
        hndlr = logging.FileHandler('logs/thug_island_data.log')
    fmrtr = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%m-%d %H:%M:%S')
    hndlr.setFormatter(fmrtr)
    logger.addHandler(hndlr)

    if args.trades is not None:
        check_transactions(wait_time=args.trades)
    else:
        main()

"""
Thug Island Fantasy League Stats and Computer Rankings - Stuart Petty (stu.petty92@gmail.com)
Created for 2016 season
"""
import xlrd
from xlutils.copy import copy
from fantasy.league import League
from util.groupme.bot.thugbot import ThugBot
from util.groupme.do_not_upload import *


DEBUG = False

CURRENT_WEEK = 2

FULL_HISTORY = False
DOWNLOAD_GAMES = False
GROUP_ME = True

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

    output = thug_island.to_string(games=True,
                                   mtchups=True,
                                   owners=False,
                                   plyffs=False,
                                   power=True,
                                   seasons=False,
                                   rcds=False)

    with open("ff_data.txt", "w") as f:
        print >> f, output

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

if __name__ == "__main__":
    main()

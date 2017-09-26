"""
Thug Island Fantasy League Stats and Computer Rankings - Stuart Petty (stu.petty92@gmail.com)
Created for 2016 season
"""
from fantasy.league import League
from util.groupme.bot.thugbot import ThugBot
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

if __name__ == "__main__":
    main()

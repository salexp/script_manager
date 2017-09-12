"""
Thug Island Fantasy League Stats and Computer Rankings - Stuart Petty (stu.petty92@gmail.com)
Created for 2016 season
"""
import xlrd
from xlutils.copy import copy
from fantasy.league import League


CURRENT_YEAR = 2017
CURRENT_WEEK = 1

DOWNLOAD_HISTORY = False
FULL_HISTORY = False
DOWNLOAD_GAMES = False

FUTURE_PLAYOFFS = False


def main():
    thug_island = League(espn_id=190153, database_settings={'name': 'Fantasy', 'user': 'local'})
    thug_island.current_year = CURRENT_YEAR
    thug_island.current_week = CURRENT_WEEK

    history_file = 'fantasy/resources/thug_island_history.xls'

    if DOWNLOAD_HISTORY:
        rb = xlrd.open_workbook(history_file)
        work_book = copy(rb)
        years = [2017]
        thug_island.download_history(years=years, book=work_book, full_history=FULL_HISTORY)
        work_book.save(history_file)

    work_book = xlrd.open_workbook(history_file)
    years = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017]
    thug_island.add_history(years, work_book, push_database=None)

    del thug_island.owners["Cody Blain"]

    year_file = 'fantasy/resources/thug_island_2017.xls'

    if DOWNLOAD_GAMES:
        rb = xlrd.open_workbook(year_file)
        work_book = copy(rb)
        year = 2017
        thug_island.download_games(year=year, book=work_book)
        work_book.save(year_file)

    work_book = xlrd.open_workbook('fantasy/resources/thug_island_2015.xls')
    thug_island.add_games(2015, work_book)
    work_book = xlrd.open_workbook('fantasy/resources/thug_island_2016.xls')
    thug_island.add_games(2016, work_book)
    work_book = xlrd.open_workbook('fantasy/resources/thug_island_2017.xls')
    thug_island.add_games(2017, work_book)

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

    # with open("ff_data.txt", "rb") as f1:
    #     with open("fantasy/resources/ff_data_base.txt", "rb") as f2:
    #         assert f1.read() == f2.read()

    True

if __name__ == "__main__":
    main()

"""
Thug Island Fantasy League Stats and Computer Rankings - Stuart Petty (stu.petty92@gmail.com)
Created for 2016 season
"""
import xlrd
from xlutils.copy import copy
from fantasy.league import League


DOWNLOAD_HISTORY = True


def main():
    thug_island = League(espn_id=190153, database_settings={'name': 'Fantasy', 'user': 'local'})

    history_file = 'fantasy/resources/thug_island_history.xls'

    if DOWNLOAD_HISTORY:
        rb = xlrd.open_workbook(history_file)
        work_book = copy(rb)
        years = [2017]
        thug_island.download_history(years=years, book=work_book)
        work_book.save(history_file)

    work_book = xlrd.open_workbook(history_file)
    years = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017]
    thug_island.add_history(years, work_book, push_database=[2017])

    del thug_island.owners["Cody Blain"]

    work_book = xlrd.open_workbook('fantasy/resources/thug_island_2015.xls')
    thug_island.add_games(2015, work_book)
    work_book = xlrd.open_workbook('fantasy/resources/thug_island_2016.xls')
    thug_island.add_games(2016, work_book)

    thug_island.recursive_rankings()

    output = thug_island.to_string(games=True,
                                   mtchups=True,
                                   owners=True,
                                   plyffs=False,
                                   power=True,
                                   seasons=True,
                                   rcds=20)

    with open("ff_data.txt", "w") as f:
        print >> f, output

    with open("ff_data.txt", "rb") as f1:
        with open("fantasy/resources/ff_data_base.txt", "rb") as f2:
            assert f1.read() == f2.read()

    True

if __name__ == "__main__":
    main()

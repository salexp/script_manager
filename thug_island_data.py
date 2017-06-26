"""
Thug Island Fantasy League Stats and Computer Rankings - Stuart Petty (stu.petty92@gmail.com)
Created for 2016 season
"""
import xlrd
from fantasy.fantasy_data import league


def main():
    thug_island = league.League("Thug Island", id="190153",
                                database_settings={'name': 'Fantasy', 'user': 'local'}
                                )

    work_book = xlrd.open_workbook('fantasy/resources/thug_island_history.xls')
    years = ['2010', '2011', '2012', '2013', '2014', '2015', '2016']
    for yi, year in enumerate(years):
        if len(years) < 7:
            yi = int(year[-1])
        work_sheet = work_book.sheet_by_index(yi)
        thug_island.add_schedule(year, work_sheet)

    del thug_island.owners["Cody Blain"]

    work_book = xlrd.open_workbook('fantasy/resources/thug_island_2015.xls')
    thug_island.add_games("2015", work_book)
    work_book = xlrd.open_workbook('fantasy/resources/thug_island_2016.xls')
    thug_island.add_games("2016", work_book)

    thug_island.recursive_rankings()

    # output = thug_island.to_string(games=True,
    #                                mtchups=True,
    #                                owners=True,
    #                                plyffs=False,
    #                                power=True,
    #                                seasons=True,
    #                                rcds=20)
    thug_island.update_database()

    # print output
    # with open("ff_data.txt", "w") as f:
    #     print >> f, output
    True

if __name__ == "__main__":
    main()

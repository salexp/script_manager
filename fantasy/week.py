from fantasy.game import Game
from fantasy.records import Records
from util.fantasy.utilities import *


class Week:
    def __init__(self, schedule, wek, sh, i):
        self.complete = False
        self.league = schedule.league
        self.owners = []
        self.schedule = schedule
        self.number = wek
        self.year = schedule.year

        self.records = Records(self)
        self.games = []

        idx = 0
        while sh.cell_value(i, 0) != "" and i <= sh.nrows - 1:
            # If 'at'
            if sh.cell_value(i, 2) != "":
                idx += 1
                row = [sh.cell_value(i, c) for c in range(sh.ncols)]
                game = Game(self, row, index=idx, detailed=False)
                self.games.append(game)
                self.owners += [game.away_owner, game.home_owner]
                if game.played:
                    self.complete = True
                    schedule.current_week = wek
            i += 1
            if i == sh.nrows:
                break

        self.records.update()

    def add_details(self, sh):
        for c in range(sh.ncols):
            if sh.cell_value(1, c) in self.league.owners:
                game = self.find_game(sh.cell_value(1, c))

                table = []
                for ir in range(0, sh.nrows):
                    table.append([sh.cell_value(ir, ic) for ic in range(c, c + 5)])

                game.build_from_matchup(table)

    def find_game(self, owner_name):
        for game in self.games:
            if owner_name in [game.away_owner_name, game.home_owner_name]:
                return game

    def is_postseason(self):
        return is_postseason(self.year, self.number)

    def is_regular_season(self):
        return is_regular_season(self.year, self.number)

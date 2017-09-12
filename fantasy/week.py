from fantasy.game import ExcelGame, game_from_sheet
from nfl_data import roster
from util.fantasy.utilities import *


class Week:
    def __init__(self, schedule, wek, sh, i):
        self.complete = False
        self.league = schedule.league
        self.owners = []
        self.schedule = schedule
        self.number = wek
        self.year = schedule.year

        self.records = WeekRecords(self)
        self.games = []

        self._highest_score = None
        self._losing_owners = None
        self._winning_owners = None

        idx = 0
        while sh.cell_value(i, 0)  not in ("", " ") and i <= sh.nrows - 1:
            # If 'at'
            if sh.cell_value(i, 2) not in ("", " "):
                idx += 1
                row = [sh.cell_value(i, c) for c in range(sh.ncols)]
                game = game_from_sheet(self, row, index=idx, detailed=False)
                self.games.append(game)
                self.owners += [game.away_owner, game.home_owner]
                if game.played:
                    self.complete = True
                    schedule.current_week = wek
            i += 1
            if i == sh.nrows:
                break

        self.records.update()

    @property
    def highest_score(self):
        if self._highest_score is None:
            if self.complete and self.winning_owners:
                winning_matchups = [o.games[self.year][self.number] for o in self.winning_owners]
                sorted_matchups = sorted(winning_matchups, key=lambda m: m.pf, reverse=True)
                self._highest_score = sorted_matchups[0]
        return self._highest_score

    @property
    def losing_owners(self):
        if self._losing_owners is None:
            if self.complete:
                self._losing_owners = [o for o in self.owners if o.games[self.year][self.number].lost]
        return self._losing_owners

    @property
    def winning_owners(self):
        if self._winning_owners is None:
            self._winning_owners = [o for o in self.owners if o.games[self.year][self.number].won]
        return self._winning_owners

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


class WeekRecords:
    def __init__(self, week):
        self.alltime_roster = None
        self.finish = {"Games": []}
        self.league = week.league
        self.week = week
        self.year = week.year

    def make_roster(self):
        rstr = roster.GameRoster()
        for game in self.week.games:
            for mtch in [game.away_matchup, game.home_matchup]:
                for plyr in mtch.roster.starters:
                    rstr.add_player(plyr, force="Bench")

        rstr.make_optimal()
        opt = rstr.optimal
        opt.update_points()
        self.alltime_roster = opt

    def update(self):
        if self.week.complete and self.week.is_regular_season():
            rcd = self.finish
            matchups = [g.home_matchup for g in self.week.games]
            matchups += [g.away_matchup for g in self.week.games]
            matchups = sorted(matchups, key=lambda p: p.pf, reverse=True)
            rcd["Games"] = matchups
            for i, mtch in enumerate(matchups):
                rcd[mtch.owner.name] = i + 1
                mtch.owner.records.points_finish["All"].append(i + 1)
                if not mtch.owner.records.points_finish.get(self.year):
                    mtch.owner.records.points_finish[self.year] = []
                mtch.owner.records.points_finish[self.year].append(i + 1)

from fantasy.fantasy_data import owner
from fantasy.nfl_data import player
from fantasy.nfl_data import roster
from util.fantasy.utilities import *


class Schedule:
    def __init__(self, league, sh, year):
        self.complete = False
        self.league = league
        self.owners = []
        self.year = year

        self.week_list = []
        self.weeks = {}

        wek = 0
        found_division = False
        for r in range(sh.nrows):
            if "WEEK" in sh.cell_value(r, 0) or "ROUND" in sh.cell_value(r, 0):
                wek += 1
                week = Week(self, str(wek), sh, r)
                self.add_week(week)
                self.complete = week.complete
                if not len(self.owners):
                    self.owners = week.owners
                if self.complete:
                    self.league.years[year].current_week = week.number
                    self.league.years[year].current_year = year
            elif "Byes" in sh.cell_value(r, 0):
                found_division = True
                for owner in self.owners:
                    if owner not in week.owners:
                        owner.add_division_championship(year)

        if not found_division and self.complete:
            for wi, week in enumerate(self.week_list):
                if self.weeks[week].is_postseason():
                    break

            standings = []
            for owner in self.owners:
                rcd = owner.seasons[year].wl_records[wi]
                w = int(rcd.split('-')[0])
                l = int(rcd.split('-')[1])
                t = 0 if len(rcd.split('-')) < 3 else int(rcd.split('-')[2])
                standings.append([owner.name, w, l, t, owner.division])

            standings = sorted(standings, key=lambda p: (p[1], p[3]), reverse=True)

            found = {"East": False, "West": False}
            for i, f in enumerate(standings):
                if not found.get(f[4]):
                    found[f[4]] = f[0]
                    self.league.owners[f[0]].add_division_championship(year)

    def add_week(self, w):
        self.week_list.append(w.number)
        self.weeks[w.number] = w


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

    def update_database(self):
        for game in self.games:
            game.update_database()

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


class Records:
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
                for plyr in mtch.roster.starters + mtch.roster.bench:
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


class Game:
    def __init__(self, week, data, index, detailed=False):
        self.away_matchup = None
        self.away_owner = None
        self.away_owner_name = None
        self.away_record = None
        self.away_roster = []
        self.away_score = None
        self.away_team = None
        self.away_win = None
        self.detailed = detailed
        self.expended = None
        self.home_matchup = None
        self.home_owner = None
        self.home_owner_name = None
        self.home_record = None
        self.home_roster = []
        self.home_score = None
        self.home_team = None
        self.home_win = None
        self.index = index
        self.league = week.league
        self.played = False
        self.preview = None
        self.raw_details = None
        self.raw_summary = None
        self.schedule = week.schedule
        self.score = None
        self.week = week
        self.winner = None
        self.year = week.year
        self.is_regular_season = is_regular_season(self.year, self.week.number)
        self.is_postseason = is_postseason(self.year, self.week.number)
        self.is_consolation = is_consolation(self.year, self.week.number, self.index)
        self.is_playoffs = is_playoffs(self.year, self.week.number, self.index)
        self.is_championship = is_championship(self.year, self.week.number, self.index)

        if detailed:
            self.build_from_matchup(data)
        else:
            self.build_from_summary(data)

    def update_database(self):
        db = self.league.db
        True

    def build_from_summary(self, row):
        self.raw_summary = row
        [self.away_team, self.away_record] = row[0].replace(" (", "(").replace(")", "").split("(")
        self.away_owner_name = row[1]
        [self.home_team, self.home_record] = row[3].replace(" (", "(").replace(")", "").split("(")
        self.home_owner_name = row[4]
        score = row[5]
        if score not in ["", "Preview"]:
            self.played = True
            self.score = score

        away = self.league.owners[self.away_owner_name]
        home = self.league.owners[self.home_owner_name]
        self.away_owner = self.league.owners[self.away_owner_name]
        self.home_owner = self.league.owners[self.home_owner_name]

        if self.played:
            self.away_score = float(score.split("-")[0])
            self.home_score = float(score.split("-")[1])
            self.winner = "Away" if self.away_score > self.home_score else "Home" \
                if self.away_score < self.home_score else "Tie"
            self.away_win = self.winner == "Away"
            self.home_win = self.winner == "Home"

        self.away_matchup = away.add_matchup(self, "Away")
        self.home_matchup = home.add_matchup(self, "Home")

    def build_from_matchup(self, data):
        self.detailed = True
        self.raw_details = data
        team_a = data[1][0]
        team_b = data[5][0]
        away = True if team_a == self.away_owner_name else False
        box_a_start = 10
        box_b_end = len(data) - 1
        for i in range(box_a_start + 1, len(data)):
            try:
                if "BOX SCORE" in data[i][0]:
                    box_a_end = i - 1
                    box_b_start = i
                    break
            except TypeError:
                pass

        box_a = data[box_a_start:box_a_end + 1]
        box_b = data[box_b_start:box_b_end + 1]
        boxscore_away = box_a if away else box_b
        boxscore_home = box_b if away else box_a

        for home, [boxscore, owner] in enumerate([[boxscore_away, self.away_owner_name], [boxscore_home, self.home_owner_name]]):
            owner = self.league.owners[owner]
            roster = []
            for r in boxscore:
                plyr = None
                slot = r[0]
                if r[1] != "" and "PLAYER" not in r[1]:
                    name = player.get_name(r[1])
                    if name not in self.league.players:
                        self.league.players[name] = player.Player(r)
                    plyr = self.league.players[name]
                elif slot in self.league.lineup_positions and r[4] == "--":
                    plyr = player.NonePlayer(r)

                if plyr is not None:
                    mtup = self.home_matchup if home else self.away_matchup
                    plyr.update(mtup, r, slot)
                    roster.append(plyr)

            if home:
                self.home_roster = roster
            else:
                self.away_roster = roster

            owner.check_roster(mtup)

    def create_preview(self):
        self.preview = GamePreview(self)

    def update_database(self):
        pass


def is_regular_season(year, week):
    year = int(year)
    week = int(week)

    return week <= 13


def is_postseason(year, week):
    year = int(year)
    week = int(week)

    return week > 13


def is_consolation(year, week, game):
    return is_postseason(year, week) and not is_playoffs(year, week, game)


def is_playoffs(year, week, game):
    year = int(year)
    week = int(week)
    game = int(game)

    return (year == 2010 and week == 14 and game <= 2) \
           or (year == 2010 and week == 15 and game == 1) \
           or (year-2000 in [11, 12, 13, 14, 15, 16] and week in [14, 15] and game < 3) \
           or (week == 16 and game == 1)


def is_championship(year, week, game):
    year = int(year)
    week = int(week)
    game = int(game)

    return (year == 2010 and week == 15 and game == 1) \
           or (year-2000 in [11, 12, 13, 14, 15, 16] and week == 16 and game == 1)


class GamePreview:
    def __init__(self, game):
        away_owner = game.away_owner
        away_owner.attrib.update()
        home_owner = game.home_owner
        home_owner.attrib.update()

        mu_a = away_owner.attrib.mu
        sigma_a = away_owner.attrib.sigma
        mu_h = home_owner.attrib.mu
        sigma_h = home_owner.attrib.sigma

        point_range = range(int(min([mu_a, mu_h]) - max([sigma_a, sigma_h])) * 100,
                            int(max([mu_a, mu_h]) + max([sigma_a, sigma_h])) * 100)

        summ = 0.0
        mx = None
        for hpts in point_range:
            pts = hpts / 100.0
            sum_temp = float(abs(normpdf(pts, mu_a, sigma_a) + normpdf(pts, mu_h, sigma_h)))
            if sum_temp > summ:
                summ = sum_temp
                mx = hpts

        points = mx / 100.0
        self.ou = 2 * points
        sum_a = sumpdf(points, mu_a, sigma_a)
        sum_h = sumpdf(points, mu_h, sigma_h)
        under = average([sum_a, sum_h], rnd=6)
        over = 1 - under
        self.over_favorite = over > under
        self.under_favorite = over < under
        ou_lines = [None, None]
        for i, pct in enumerate([under, over]):
            if pct > 0.5:
                ou_line = pct / (1.0 - pct) * (-100.0)
            else:
                ou_line = (1.0 - pct) / pct * 100
            ou_line = int(ou_line / abs(ou_line)) * ((abs(ou_line) - 100) / 1.0 + 100)
            ou_line = round(round(ou_line * 4, -1) / 4, 0)
            ou_lines[i] = abs(ou_line)
        self.over_payout = ou_lines[0]
        self.under_payout = ou_lines[1]

        away_opp = away_owner.records.opponents[home_owner.name]["All"]
        away_year = away_owner.records.overall[game.year]
        home_opp = home_owner.records.opponents[away_owner.name]["All"]
        home_year = home_owner.records.overall[game.year]
        pct_a = 0.9 * sum_a / (sum_a + sum_h) + 0.1 * away_opp.percent()
        pct_h = 0.9 * sum_h / (sum_a + sum_h) + 0.1 * home_opp.percent()

        self.favorite = "Away" if pct_a > pct_h else "Home" if pct_a < pct_h else None
        self.percent = max([pct_a, pct_h])
        self.away_favorite = self.favorite == "Away"
        self.home_favorite = self.favorite == "Home"
        self.away_percent = pct_a
        self.home_percent = pct_h
        self.spread = pct_a * sigma_a + pct_h * sigma_h
        self.away_spread = self.spread * (-1 if self.away_favorite else 1)
        self.home_spread = self.spread * (-1 if self.home_favorite else 1)

        diff_a = abs(mx / 100.0 - mu_a)
        diff_h = abs(mx / 100.0 - mu_h)
        self.away_payout = int(round(round(((diff_a / (diff_a + diff_h) / 2) * 100 + 100) * 2, -1) / 2 \
                           * (-1 if self.away_favorite else 1), 0))
        self.home_payout = int(round(round(((diff_h / (diff_a + diff_h) / 2) * 100 + 100) * 2, -1) / 2 \
                           * (-1 if self.home_favorite else 1), 0))

        adjm = int(average([abs(n) for n in [self.away_payout, self.home_payout]]) - 100)
        money_lines = [None, None]
        for i, pct in enumerate([pct_a, pct_h]):
            if pct > 0.5:
                mline = pct / (1.0 - pct) * (-100.0)
            else:
                mline = (1.0 - pct) / pct * 100
            mline = int(mline / abs(mline)) * ((abs(mline) - 100) + 100)
            mline = int(round(mline * 2, -1) / 2) if mline != 100 else "PUSH"
            if mline != "PUSH":
                mline += abs(mline) / mline * adjm
            money_lines[i] = mline

        self.moneyline = average([abs(n) for n in money_lines])
        self.away_moneyline = money_lines[0]
        self.home_moneyline = money_lines[1]

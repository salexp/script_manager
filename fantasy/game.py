from nfl_data import player
from util.fantasy.utilities import *


class Game:
    def __init__(self, week, db_id, db_entry=None):
        self._db_entry = db_entry
        self.db_id = db_id
        self.league = week.league
        self.schedule = week.schedule
        self.week = week
        self.year = week.year

        self.detailed = None

        self._away_owner = None
        self._home_owner = None

        self._away_matchup = None
        self._away_record = None
        self._away_roster = None
        self._away_score = None
        self._away_team = None
        self._away_win = None
        self._expended = None
        self._home_matchup = None
        self._home_record = None
        self._home_roster = None
        self._home_score = None
        self._home_team = None
        self._home_win = None
        self._played = False
        self._preview = None
        self._raw_details = None
        self._raw_summary = None
        self._score = None
        self._winner = None
        self._is_regular_season = is_regular_season(self._year, self._week.number)
        self._is_postseason = is_postseason(self._year, self._week.number)
        self._is_consolation = is_consolation(self._year, self._week.number, self._index)
        self._is_playoffs = is_playoffs(self._year, self._week.number, self._index)
        self._is_championship = is_championship(self._year, self._week.number, self._index)

    @property
    def away_owner(self):
        if self._away_owner is None:
            owner_id = self.db_entry.get('AWAY_OWNER_ID')
            self._away_owner = self.league.find_owner(owner_id, 'USER_ID')
        return self._away_owner

    @property
    def away_owner_name(self):
        return self.away_owner.name

    @property
    def db_entry(self):
        if self._db_entry is None:
            query = """SELECT * FROM Games WHERE GAME_ID={}""".format(self.db_id)
            self._db_entry = self.league.db.query_return_dict_single(query)
        return self._db_entry

    @property
    def home_owner(self):
        if self._home_owner is None:
            owner_id = self.db_entry.get('HOME_OWNER_ID')
            self._home_owner = self.league.find_owner(owner_id, 'USER_ID')
        return self._home_owner

    @property
    def home_owner_name(self):
        return self.home_owner.name


class ExcelGame:
    def __init__(self, week, data, index, detailed=False):
        self.detailed = detailed
        self.index = index
        self.league = week.league
        self.schedule = week.schedule
        self.week = week
        self.year = week.year

        self._db_entry = None
        self._id = None
        self._margin = None
        self._preview = None
        self._total_points = None
        self._url = None

        self.away_matchup = None
        self.away_owner = None
        self.away_owner_name = None
        self.away_record = None
        self.away_roster = []
        self.away_score = None
        self.away_team = None
        self.away_win = None
        self.expended = None
        self.home_matchup = None
        self.home_owner = None
        self.home_owner_name = None
        self.home_record = None
        self.home_roster = []
        self.home_score = None
        self.home_team = None
        self.home_win = None
        self.played = False
        self.raw_details = None
        self.raw_summary = None
        self.score = None
        self.winner = None
        self.is_regular_season = is_regular_season(self.year, self.week.number)
        self.is_postseason = is_postseason(self.year, self.week.number)
        self.is_consolation = is_consolation(self.year, self.week.number, self.index)
        self.is_playoffs = is_playoffs(self.year, self.week.number, self.index)
        self.is_championship = is_championship(self.year, self.week.number, self.index)

        if detailed:
            self.build_from_matchup(data)
        else:
            self.build_from_summary(data)

    @property
    def db_entry(self):
        if self._db_entry is None:
            query = """SELECT * FROM Games WHERE YEAR={} AND WEEK={} AND AWAY_OWNER_ID={} AND HOME_OWNER_ID={}""".format(
                self.year, self.week.number, self.away_owner.id, self.home_owner.id
            )
            db_entry = self.league.db.query_return_dict_single(query)
            if db_entry:
                self._db_entry = db_entry
                self._id = self.db_entry['GAME_ID']
            else:
                self._db_entry = {}
                self._id = False
        return self._db_entry

    @property
    def id(self):
        if self._id is None:
            query = """SELECT * FROM Games WHERE YEAR={} AND WEEK={} AND AWAY_OWNER_ID={} AND HOME_OWNER_ID={}""".format(
                self.year, self.week.number, self.away_owner.id, self.home_owner.id
            )
            db_entry = self.league.db.query_return_dict_single(query)
            if db_entry:
                self._db_entry = db_entry
                self._id = self.db_entry['GAME_ID']
            else:
                self._db_entry = None
                self._id = False
        return self._id

    @property
    def margin(self):
        if self._margin is None and self.total_points is not None:
            self._margin = abs(self.away_score - self.home_score)
        return self._margin

    @property
    def preview(self):
        if self._preview is None:
            self._preview = GamePreview(self)
        return self._preview

    @property
    def total_points(self):
        if self._total_points is None:
            self._total_points = self.away_score + self.home_score
        return self._total_points

    @property
    def url(self):
        if self._url is None:
            self._url = "http://games.espn.com/ffl/boxscorequick?leagueId={}&teamId={}&scoringPeriodId={}&seasonId={}&view=scoringperiod&version=quick".format(
                self.league.espn_id, self.home_owner.espn_id, self.week.number, self.year)
        return self._url

    def add_to_database(self):
        db = self.league.db
        query = """
        INSERT INTO Games (LEAGUE_ESPNID, YEAR, WEEK, AWAY_OWNER_ID, HOME_OWNER_ID, AWAY_SCORE, HOME_SCORE, POSTSEASON,
        PLAYOFFS, CHAMPIONSHIP) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE
        AWAY_SCORE=COALESCE(VALUES(AWAY_SCORE), AWAY_SCORE), HOME_SCORE=COALESCE(VALUES(HOME_SCORE), HOME_SCORE);
        """
        params = (
            self.league.espn_id, self.year, self.week.number, self.away_owner.id, self.home_owner.id,
            self.away_score, self.home_score, self.is_postseason, self.is_playoffs, self.is_championship
        )
        db.query_set(query, params)

    def update_db_score(self):
        if self.db_entry['AWAY_SCORE'] != self.away_score and self.db_entry['HOME_SCORE'] != self.home_score:
            query = """UPDATE Games SET AWAY_SCORE={0}, HOME_SCORE={1} WHERE GAME_ID={2};""".format(
                self.away_score, self.home_score, self.id)

            self.league.db.query_set(query)

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
                if r[1] not in ("", " ") and "PLAYER" not in r[1]:
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


class GamePreview:
    def __init__(self, game):
        away_owner = game.away_owner
        away_owner.attrib.update(start_game=game)
        home_owner = game.home_owner
        home_owner.attrib.update(start_game=game)

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


def game_from_sheet(week, data, index, detailed=False, db_entry=None):
    return ExcelGame(week, data, index, detailed)

import keyring
import os
import xlrd
from copy import deepcopy
from datetime import datetime
from operator import itemgetter
from selenium import webdriver
from xlutils.copy import copy
from fantasy.owner import Owner
from fantasy.rankings import Rankings
from fantasy.schedule import Schedule, schedule_from_sheet
from fantasy.year import Year
from util.fantasy import plotter
from util.fantasy.utilities import *
from util.sql.database import Database


class League:
    def __init__(self, espn_id, database_settings=None, database_connection=None, resources_folder=None, update_resources=False, full_update=False):
        self.database_settings = database_settings
        self._db = database_connection

        self.espn_id = espn_id
        self.resources_folder = resources_folder
        self.url = "http://games.espn.go.com/ffl/leagueoffice?leagueId=%s" % espn_id
        # http://games.espn.go.com/ffl/leagueoffice?leagueId=190153

        self._current_year = None
        self._db_games = None
        self._db_entry = None
        self._driver = None
        self._league_name = None
        self._owners = None
        self._years = None

        self.current_week = None
        self.historic_playoffs = None
        self.future_playoffs = None
        self.lineup_positions = []
        self.players = {}
        self.power_rankings = {}
        self.rankings = []
        self.records = LeagueRecords(self)

        if resources_folder is not None:
            history_file = self.file_string.format('history')
            year_files = {}
            for year in self.years_list:
                year_file = self.file_string.format(year)
                if os.path.isfile(year_file):
                    year_files[year] = year_file

            if update_resources:
                rb = xlrd.open_workbook(history_file)
                work_book = copy(rb)
                years = self.years_list if full_update else [self.current_year]
                self.download_history(years=years, book=work_book, full_history=full_update)
                work_book.save(history_file)

                rb = xlrd.open_workbook(year_files[self.current_year])
                work_book = copy(rb)
                self.download_games(self.current_year, book=work_book)
                work_book.save(year_files[self.current_year])

            work_book = xlrd.open_workbook(history_file)
            self.add_history(self.years_list, work_book, push_database=None)

            for y, year_file in year_files.items():
                work_book = xlrd.open_workbook(year_file)
                self.add_games(y, work_book)

    @property
    def current_year(self):
        if self._current_year is None:
            self._current_year = max(self.years_list)
        return self._current_year

    @property
    def db(self):
        if self._db is None:
            self._db = Database(**self.database_settings)
        return self._db

    @property
    def db_games(self):
        if self._db_games is None:
            query = """SELECT * FROM Games WHERE LEAGUE_ESPNID={}""".format(self.espn_id)
            games = self.db.query_return_dict_lookup(query, 'GAME_ID')
            self._db_games = games
        return self._db_games

    @property
    def db_entry(self):
        if self._db_entry is None:
            query = """SELECT * FROM Leagues WHERE LEAGUE_ESPNID={}""".format(self.espn_id)
            self._db_entry = self.db.query_return_dict_single(query)
        return self._db_entry

    @property
    def file_string(self):
        return os.path.join(os.getcwd(), self.resources_folder, self.league_name.lower().replace(' ', '_') + '_{}.xls')

    @property
    def league_name(self):
        if self._league_name is None:
            self._league_name = self.db_entry['LEAGUE_NAME']
        return self._league_name

    @property
    def owners(self):
        if self._owners is None:
            query = """SELECT * FROM Users WHERE LEAGUE_ESPNID={}""".format(self.espn_id)
            owners = self.db.query_return_dict_lookup(query, 'USER_ESPNNAME')
            self._owners = {k: Owner(k, self, v) for k, v in owners.items()}
        return self._owners

    @property
    def power_rankings_simple(self):
        if self.power_rankings.get(self.current_week):
            pwr_ranks = self.power_rankings.get(self.current_week)
            owner_names = [r[0].split()[0] for r in pwr_ranks]
            out_str = '\n'.join(["{}. {}".format(i+1, o) for i, o in enumerate(owner_names)])
            return out_str.rstrip('\n')
        else:
            return

    @property
    def years(self):
        if self._years is None:
            years = sorted(list(set([_['YEAR'] for k, _ in self.db_games.items()])))
            self._years = {y: Year() for y in years}
        return self._years

    @property
    def years_list(self):
        return sorted(self.years.keys())

    def add_history(self, years, book, push_database=None):
        for yi, year in enumerate(years):
            sheet = book.sheet_by_index(yi)

            if not self.years.get(year):
                self.years[year] = Year()
            sch = schedule_from_sheet(self, sheet, year)
            self.years[year].schedule = sch
            self.update_season_records(year)
            if sch.complete:
                pass
            else:
                self.current_year = year
                self.current_week = sch.current_week

        if push_database is not None:
            for y in push_database:
                year = self.years[y]
                for w, week in year.schedule.weeks.items():
                    for game in week.games:
                        game.add_to_database()

            self.db.commit()

    def download_games(self, year, book):
        schedule = self.years[year].schedule
        for w, week in sorted(schedule.weeks.items(), key=itemgetter(1)):
            wi = int(w) - 1
            sh = book.get_sheet(wi)
            if week.complete:
                write_col = -6
                for game in week.games:
                    write_row = 0
                    write_col += 6

                    self.get_driver().get(game.url)

                    try:
                        has_bench = True
                        self.get_driver().find_element_by_class_name('playerTableShowHideGroupLink').click()
                    except:
                        has_bench = False

                    team_infos = self.get_driver().find_element_by_xpath('//*[@id="teamInfos"]')

                    team_infos_lines = team_infos.text.split('\n')
                    for line in team_infos_lines:
                        sh.write(write_row, write_col, line)
                        write_row += 1

                    write_row += 1

                    if has_bench:
                        team_l_starters = self.get_driver().find_element_by_xpath('//*[@id="playertable_0"]')
                        team_l_bench = self.get_driver().find_element_by_xpath('//*[@ id="playertable_1"]')
                        team_r_starters = self.get_driver().find_element_by_xpath('//*[@ id="playertable_2"]')
                        team_r_bench = self.get_driver().find_element_by_xpath('//*[@ id="playertable_3"]')
                        team_l_details = [team_l_starters, team_l_bench]
                        team_r_details = [team_r_starters, team_r_bench]
                    else:
                        team_l_starters = self.get_driver().find_element_by_xpath('//*[@id="playertable_0"]')
                        team_r_starters = self.get_driver().find_element_by_xpath('//*[@ id="playertable_1"]')
                        team_l_details = [team_l_starters]
                        team_r_details = [team_r_starters]

                    for detail in [team_l_details, team_r_details]:
                        for table in detail:
                            rows = table.find_elements_by_xpath('.//tr')
                            for ri, row in enumerate(rows):
                                cols = row.find_elements_by_xpath('.//td')
                                write_row += 1
                                for ci, col in enumerate(cols):
                                    sh.write(write_row, write_col+ci, col.text)

    def download_history(self, years, book, full_history=True):
        week_str = "week {}".format(self.current_week)
        for year in years:
            yi = year % 10
            sh = book.get_sheet(yi)

            self.get_driver().get("http://games.espn.com/ffl/schedule?leagueId={}&seasonId={}".format(self.espn_id, year))
            table = self.get_driver().find_element_by_class_name('tableBody')
            rows = table.find_elements_by_xpath('.//tr')

            start_write = False
            for ri, row in enumerate(rows):
                cols = row.find_elements_by_xpath('.//td|.//th')
                for ci, col in enumerate(cols):
                    if full_history or start_write:
                        sh.write(ri, ci, col.text.rstrip())
                    elif week_str in col.text.lower() and year == self.current_year:
                        sh.write(ri, ci, col.text.rstrip())
                        start_write = True

    def find_owner(self, value, key):
        for o, owner in self.owners.items():
            if value == owner.db_entry[key]:
                return owner

    def get_driver(self):
        if self._driver is None:
            drv = webdriver.Chrome()
            drv.get("http://www.espn.com/login")
            frms = drv.find_elements_by_xpath('(//iframe)')
            drv.switch_to.frame(frms[0])
            drv.find_element_by_xpath("(//input)[1]").send_keys("legosap")
            drv.find_element_by_xpath("(//input)[2]").send_keys(keyring.get_password('system', 'espn'))
            drv.find_element_by_xpath("(//button[2])").click()
            drv.switch_to.default_content()

            waiting = True
            while waiting:
                try:
                    drv.find_element_by_class_name('user')
                    waiting = False
                except:
                    waiting = True

            drv.get(self.url)
            self._driver = drv
        return self._driver

    def add_games(self, year, book):
        for w in range(1, len(self.years[year].schedule.weeks) + 1):
            wk = str(w)
            week = self.years[year].schedule.weeks[wk]
            sheet = book.sheet_by_index(w - 1)
            week.add_details(sheet)

    def generate_rankings(self, year=None, week=None, plot=False):
        rkngs = Rankings(self)
        if year is None:
            year = max(self.years.keys())
        if week is None:
            week = self.years[year].current_week

        rstr = self.years[year].schedule.weeks[week].records.make_roster()
        rkngs.roster = rstr

        for owner in self.owners:
            rkngs.add_owner(self.owners[owner], year, week)

        hgh = 0.0
        mx = {}
        for key in rkngs.keys:
            wgt = rkngs.keys[key]
            rkngs.ranks[key] = {"List": None}
            if key == "QB":
                lst = [[o, rkngs.owners[o].qb] for o in rkngs.owners]
            elif key == "RB":
                lst = [[o, rkngs.owners[o].rb] for o in rkngs.owners]
            elif key == "WR":
                lst = [[o, rkngs.owners[o].wr] for o in rkngs.owners]
            elif key == "TE":
                lst = [[o, rkngs.owners[o].te] for o in rkngs.owners]
            elif key == "D/ST":
                lst = [[o, rkngs.owners[o].dst] for o in rkngs.owners]
            elif key == "K":
                lst = [[o, rkngs.owners[o].k] for o in rkngs.owners]
            elif key == "WP":
                lst = [[o, rkngs.owners[o].wpct] for o in rkngs.owners]
            elif key == "PF":
                lst = [[o, rkngs.owners[o].pf] for o in rkngs.owners]
            elif key == "PA":
                lst = [[o, rkngs.owners[o].pa] for o in rkngs.owners]
            elif key == "PLOB":
                lst = [[o, rkngs.owners[o].plob] for o in rkngs.owners]

            mx[key] = max([l[1] for l in lst])
            mx["WP"] = 1.0
            mx["PLOB"] = min([l[1] for l in lst])

            if key not in ["PLOB"]:
                mlst = [[i[0], i[1]/mx[key]*wgt] for i in lst]
            else:
                mlst = [[i[0], mx[key]/i[1]*wgt] for i in lst]

            slst = sorted(mlst, key=lambda p: p[1], reverse=True)
            hgh += slst[0][1]
            rlst = add_ranks(slst, 1)
            rkngs.ranks[key]["List"] = rlst

            for lne in rlst:
                nlne = lne[1:]
                if lne[1] != 0:
                    cntrb = lne[1]
                else:
                    cntrb = 0.0
                nlne.append(cntrb)
                rkngs.ranks[key][lne[0]] = nlne

        power_rankings = []
        rkngs.ranks["PR"] = {}
        for owner in self.owners:
            trnk = 0.0
            for key in rkngs.keys:
                trnk += rkngs.ranks[key][owner][2]

            trnk = trnk / hgh
            rkngs.ranks["PR"][owner] = trnk
            power_rankings.append([owner, trnk])

        self.rankings.append(rkngs)
        power_rankings = sorted(power_rankings, key=lambda p: p[1], reverse=True)
        self.power_rankings[week] = add_ranks(power_rankings, 1)

        for r, rank in enumerate(self.power_rankings[week]):
            owner = rank[0]
            rkngs.ranks[owner] = r

        if plot:
            plotter.computer_rankings(self)

    def make_historic_playoffs(self, nxt=False):
        most_wins = int(self.current_week) + nxt
        playoffs = {}
        records = ["{}-{}".format(most_wins-i, i) for i in range(most_wins+1)]
        for r in records:
            playoffs[r] = [0, 0.0]

        seasons = [y for y in self.years]
        seasons.remove(self.current_year)
        for y in seasons:
            owner_seasons = self.years[y].owner_seasons
            for s in owner_seasons:
                ows = owner_seasons[s]
                for rcd in records:
                    if rcd in ows.wl_records:
                        playoffs[rcd][0] += ows.playoffs
                        playoffs[rcd][1] += 1

        self.historic_playoffs = playoffs

    def make_future_playoffs(self, all_points=True):
        t_a = datetime.now()
        schedule = self.years[self.current_year].schedule
        weeks_left = schedule.week_list[int(self.current_week):]
        games_left = [i for s in [schedule.weeks[w].games for w in weeks_left] for i in s]
        games_left = [g for g in games_left if g.is_regular_season]
        if games_left and g.is_regular_season:
            game_outcomes = range(0, 2 ** (len(weeks_left) * len(schedule.weeks[weeks_left[0]].games)))
            game_outcomes = [bin(g).split('b')[1].zfill(len(weeks_left) * len(schedule.weeks[weeks_left[0]].games))
                             for g in game_outcomes]
        #     game_outcomes = [bin(g).split('b')[1].zfill(15) for g in range(2**5)]
        else:
            game_outcomes = []

        init_records = {}
        season_finishes = {}
        for owner in self.owners:
            w = self.owners[owner].seasons[self.current_year].wins
            l = self.owners[owner].seasons[self.current_year].losses
            t = self.owners[owner].seasons[self.current_year].ties
            pf = self.owners[owner].seasons[self.current_year].ppg
            d = self.owners[owner].division
            init_records[owner] = [owner, w, l, t, pf, d]
            season_finishes[owner] = [0, 0, 0]  # Division, playoffs, total

        if game_outcomes:
            for io, outcome in enumerate(game_outcomes):
                highest_list = [None] if not all_points else self.owners.keys()
                for highest_owner in highest_list:
                    record = deepcopy(init_records)
                    if highest_owner is not None:
                        record[highest_owner][4] = 999.9
                    for g, game in enumerate(outcome):
                        away_owner = games_left[g].away_owner.name
                        home_owner = games_left[g].home_owner.name
                        record[away_owner][1] += int(game)
                        record[away_owner][2] += not int(game)
                        record[home_owner][1] += not int(game)
                        record[home_owner][2] += int(game)

                    finished = [record[o] for o in record]
                    finished = sorted(finished, key=lambda p: (p[1], p[4]), reverse=True)

                    # Look for division winners
                    found = {"East": False, "West": False}
                    for i, f in enumerate(finished):
                        if not found.get(f[5]):
                            found[f[5]] = f[0]
                            finished.pop(i)
                    for d in found:
                        season_finishes[found[d]][0] += 1
                        season_finishes[found[d]][1] += 1
                        season_finishes[found[d]][2] += 1

                    # Look for wildcards
                    for i, f in enumerate(finished[:4]):
                        season_finishes[f[0]][1] += 1
                        season_finishes[f[0]][2] += 1

                    # Total remaining
                    for i, f in enumerate(finished[4:]):
                        season_finishes[f[0]][2] += 1
                # if int(outcome, 2) % (int(game_outcomes[-1], 2) / 100) == 0:
                #     t_b = datetime.now()
                #     t_d = (t_b - t_a).seconds
                #     print outcome,
                #     print ": {0}m {1}s: {2:.0%}".format(t_d / 60, t_d % 60, io / float(int(game_outcomes[-1], 2)))
        else:
            finished = [init_records[o] for o in init_records]
            finished = sorted(finished, key=lambda p: (p[1], p[4]), reverse=True)

            # Look for division winners
            found = {"East": False, "West": False}
            for i, f in enumerate(finished):
                if not found.get(f[5]):
                    found[f[5]] = f[0]
                    finished.pop(i)
            for d in found:
                season_finishes[found[d]][0] += 1
                season_finishes[found[d]][1] += 1
                season_finishes[found[d]][2] += 1

            # Look for wildcards
            for i, f in enumerate(finished[:4]):
                season_finishes[f[0]][1] += 1
                season_finishes[f[0]][2] += 1

            # Total remaining
            for i, f in enumerate(finished[4:]):
                season_finishes[f[0]][2] += 1

        self.future_playoffs = season_finishes

        for owner_name in season_finishes:
            owner = self.owners[owner_name]
            chc = season_finishes[owner_name]
            if chc[1] == chc[2]:
                owner.add_playoff_appearance(self.current_year)
            if chc[0] == chc[2]:
                owner.add_division_championship(self.current_year)

    def recursive_rankings(self, year=None, playoffs=True):
        if year is None:
            year = max(self.years.keys())

        self.current_week = self.years[year].current_week
        self.current_year = year

        weeks = [str(w) for w in range(1, int(self.current_week)+1)]
        for week in weeks:
            self.generate_rankings(week=week, plot=week is weeks[-1])

        if playoffs:
            self.make_historic_playoffs()
            self.make_future_playoffs()

    def search_players(self, name="   ", position="   "):
        found = []
        for plyr in self.players:
            if name in self.players[plyr].name:
                found.append(self.players[plyr])
            if position in self.players[plyr].position:
                found.append(self.players[plyr])

        return found

    def update_season_records(self, year, key=None, number=50):
        records = self.records.season
        owner_seasons = self.years[year].owner_seasons

        if key is not None:
            keys = [key]
        else:
            keys = []
            keys += records.keys()

        for ownr in owner_seasons:
            ownr_season = owner_seasons[ownr]
            for key in keys:
                if key == "Most PF":
                    rcd = records[key]
                    if len(rcd) < number:
                        rcd.append(ownr_season)
                    else:
                        if rcd[-1].ppg < ownr_season.ppg:
                            rcd[-1] = ownr_season
                    records[key] = \
                        sorted(rcd, key=lambda param: param.ppg, reverse=True)

                elif key == "Fewest PF":
                    rcd = records[key]
                    if len(rcd) < number:
                        rcd.append(ownr_season)
                    else:
                        if rcd[-1].ppg > ownr_season.ppg:
                            rcd[-1] = ownr_season
                    records[key] = \
                        sorted(rcd, key=lambda param: param.ppg, reverse=False)

                elif key == "Most PA":
                    rcd = records[key]
                    if len(rcd) < number:
                        rcd.append(ownr_season)
                    else:
                        if rcd[-1].pag < ownr_season.pag:
                            rcd[-1] = ownr_season
                    records[key] = \
                        sorted(rcd, key=lambda param: param.pag, reverse=True)

                elif key == "Fewest PA":
                    rcd = records[key]
                    if len(rcd) < number:
                        rcd.append(ownr_season)
                    else:
                        if rcd[-1].pag > ownr_season.pag:
                            rcd[-1] = ownr_season
                    records[key] = \
                        sorted(rcd, key=lambda param: param.pag, reverse=False)

    def to_string(self, games=True, mtchups=False, owners=True, plyffs=True, power=True, seasons=True, rcds=10):
        week = self.current_week
        body = "Week {} Computer Rankings and Matchup Previews\n\n".format(int(week)+1)

        if power:
            i_week = int(self.current_week) - 1
            last_week = str(int(week) - 1) if week != "1" else None
            i_last_week = int(last_week) - 1 if last_week is not None else None
            year = self.current_year
            rnks = self.power_rankings[week]
            body += "[b]Week {} Computer Rankings[/b]\n".format(int(week)+1)
            for rnk in rnks:
                owner = self.owners[rnk[0]]
                if i_last_week is not None:
                    diff = self.rankings[i_last_week].ranks[owner.name] - self.rankings[i_week].ranks[owner.name]
                else:
                    diff = False
                diff = " -- " if not diff else "+{}".format(diff) if diff > 0 else " {}".format(diff)
                body += "{0} ({1}) [{2:.4f}] {3}{4}{5} ({6})\n".format(rnk[2],
                                                                       diff,
                                                                       rnk[1],
                                                                       owner.team_names[-1].rstrip().encode("utf-8"),
                                                                       "*" if year in owner.playoffs else "",
                                                                       "*" if year in owner.division_championships else "",
                                                                       owner.seasons[self.current_year].record())
            body += "** - Clinched division\n"
            body += "* - Clinched playoffs\n"

            body += "\n"
            body += "[b]Rankings Graph[/b]\n"
            body += "[image][/image]\n"

            body += "\n"
            rstr = self.years[year].schedule.weeks[week].records.alltime_roster
            body += "[b]Team Bonuses (Week {})[/b]\n".format(week)
            winner_names = sorted([o.first_name for o in self.years[year].schedule.weeks[week].winning_owners])
            body += "W: {}\n".format(', '.join(winner_names))
            body += "PF: {} ({})\n".format(self.years[year].schedule.weeks[week].highest_score.pf,
                                                 self.years[year].schedule.weeks[week].highest_score.owner.first_name)
            pos = ["QB1", "RB1", "WR1"]
            for p, plyr in enumerate([rstr.qb, rstr.rb1, rstr.wr1]):
                body += "{0}. {1} ({2}) - {3}\n".format(pos[p],
                                                        plyr.name,
                                                        plyr.owner.name,
                                                        plyr.points)
            other_players = sorted([rstr.te, rstr.dst, rstr.k], key=lambda p: p.points, reverse=True)
            top_other = other_players[0]
            body += "{0}. {1} ({2}) - {3}\n".format(top_other.slot,
                                                    top_other.name,
                                                    top_other.owner.name,
                                                    top_other.points)

        if owners:
            body += "\n"
            ownrs = sorted([o for o in self.owners], key=lambda p: (p[0].upper(), p[1]))
            for o in ownrs:
                body += self.owners[o].records.to_string()
                body += "\n"

        if plyffs:
            body += "\n"
            plys = self.historic_playoffs
            body += "[b]Historic Playoff Chances[/b]\n"
            for r in sorted(plys.keys(), key=lambda p: int(p.split('-')[0]), reverse=True):
                rcd = plys[r]
                body += "{0}: {1}{2}{3} team{4} gone {5}{6}\n".format(r,
                    "{:.1%}".format(rcd[0] / rcd[1]) if rcd[1] else "No",
                    ", " if rcd[1] else "",
                    "{:.0f}".format(rcd[1]) if rcd[1] else "",
                    "s have" if rcd[1] != 1 else " has",
                    r,
                    ", {} made playoffs".format(rcd[0]) if rcd[1] else "")

            body += "\n"
            plys = self.future_playoffs
            sims = plys[plys.keys()[0]][2]
            body += "[b]Playoff Simulations ({} scenarios)[/b]\n".format(sims)
            owners = plys.keys()
            owners = sorted(owners, key=lambda p: (p[0].upper(), p[1].upper()))
            for owner in owners:
                rcd = plys[owner]
                body += "[u]{}[/u]\n".format(owner)
                body += "{0}{1} end in division championship\n".format(
                    "<" if float(rcd[0]) / float(rcd[2]) < 0.0001 and rcd[0] != 0 else "",
                    "No scenarios" if rcd[0] == 0 else "{0:.2%}".format(float(rcd[0]) / float(rcd[2])))
                body += "{0}{1} end in playoff berth\n\n".format(
                    "<" if float(rcd[1]) / float(rcd[2]) < 0.0001 and rcd[1] != 0 else "",
                    "No scenarios" if rcd[1] == 0 else "{0:.2%}".format(float(rcd[1]) / float(rcd[2])))

        if mtchups:
            body += "\n"
            week = self.current_week
            next_week = str(int(week) + 1)
            year = self.current_year

            if next_week in self.years[year].schedule.weeks.keys():
                owner_ranks = self.rankings[-1].ranks

                body += "[b]Matchup Previews[/b]\n"
                gms = self.years[year].schedule.weeks[next_week].games
                for gm in gms:
                    gm.create_preview()
                    p = gm.preview
                    body += "[{0}] [u]{1}[/u] at\n".format(owner_ranks[gm.away_owner.name]+1, gm.away_team.rstrip().encode("utf-8"))
                    body += "[{0}] [u]{1}[/u]\n".format(owner_ranks[gm.home_owner.name]+1, gm.home_team.rstrip().encode("utf-8"))
                    body += "{0}| S:{1}{2:.1f}{1}{3:.0f} ML:{1}{4} O:{5}{6} O/U:{7:.1f}\n".format(
                        gm.away_owner.initials,
                        "+" if p.home_favorite else " ",
                        p.away_spread,
                        p.away_payout,
                        p.away_moneyline,
                        "+" if p.under_favorite and p.over_payout != 100 else " -" if p.over_payout != 100 else "",
                        "{:.0f}".format(p.over_payout) if p.over_payout != 100 else "PUSH",
                        p.ou,)
                    body += "{0}| S:{1}{2:.1f}{1}{3:.0f} ML:{1}{4} U:{5}{6}\n".format(
                        gm.home_owner.initials,
                        "+" if p.away_favorite else " ",
                        p.home_spread,
                        p.home_payout,
                        p.home_moneyline,
                        "+" if p.over_favorite and p.under_payout != 100 else " -"if p.under_payout != 100 else "",
                        "{:.0f}".format(p.under_payout) if p.under_payout != 100 else "PUSH",)

                    away_opp_rcd = gm.away_owner.records.opponents[gm.home_owner.name]["All"]
                    home_opp_rcd = gm.home_owner.records.opponents[gm.away_owner.name]["All"]
                    away_all = away_opp_rcd.percent() > home_opp_rcd.percent()
                    home_all = away_opp_rcd.percent() < home_opp_rcd.percent()
                    tied_all = away_opp_rcd.percent() == home_opp_rcd.percent()
                    body += "{0} {1} all-time {2}\n".format(
                        gm.away_owner.first_name if away_all else gm.home_owner.first_name if home_all else "Series",
                        "leads" if not tied_all else "tied",
                        away_opp_rcd.to_string(pfpa=False) if away_all else home_opp_rcd.to_string(pfpa=False))

                    body += "\n"

        if rcds:
            if games:
                body += "\n"
                rcd = self.records.teams["Most PF"]
                body += "[b]Most PF in a Single Game[/b]\n"
                for r in range(rcds):
                    mtch = rcd[r]
                    body += "{0} {1} pts, {2} {3} {4} {5} {6} week {7}\n".format(add_suffix(r+1),
                                                                                mtch.pf,
                                                                                mtch.owner_name,
                                                                                "won" if mtch.won else "lost",
                                                                                "vs" if mtch.home else "at",
                                                                                mtch.opponent.name,
                                                                                mtch.year, mtch.week.number)

                body += "\n"
                rcd = self.records.teams["Fewest PF"]
                body += "[b]Fewest PF in a Single Game[/b]\n"
                for r in range(rcds):
                    mtch = rcd[r]
                    body += "{0} {1} pts, {2} {3} {4} {5} {6} week {7}\n".format(add_suffix(r+1),
                                                                                mtch.pf,
                                                                                mtch.owner_name,
                                                                                "won" if mtch.won else "lost",
                                                                                "vs" if mtch.home else "at",
                                                                                mtch.opponent.name,
                                                                                mtch.year, mtch.week.number)

                body += "\n"
                rcd = self.records.games["Highest Scoring"]
                body += "[b]Highest Scoring Game[/b]\n"
                for r in range(rcds):
                    game = rcd[r]
                    body += "{0} {1}, {2} {3} {4} {5} {6} week {7}\n".format(add_suffix(r+1),
                                                                            make_score(game.away_score, game.home_score),
                                                                            game.home_owner_name if game.winner == "Home"
                                                                            else game.away_owner_name,
                                                                            "tied" if game.winner == "Tie" else "won",
                                                                            "vs" if game.winner == "Home" else "at",
                                                                            game.away_owner_name if game.winner == "Home"
                                                                            else game.home_owner_name,
                                                                            game.year, game.week.number)

                body += "\n"
                rcd = self.records.games["Lowest Scoring"]
                body += "[b]Lowest Scoring Game[/b]\n"
                for r in range(rcds):
                    game = rcd[r]
                    body += "{0} {1}, {2} {3} {4} {5} {6} week {7}\n".format(add_suffix(r+1),
                                                                            make_score(game.away_score, game.home_score),
                                                                            game.home_owner_name if game.winner == "Home"
                                                                            else game.away_owner_name,
                                                                            "tied" if game.winner == "Tie" else "won",
                                                                            "vs" if game.winner == "Home" else "at",
                                                                            game.away_owner_name if game.winner == "Home"
                                                                            else game.home_owner_name,
                                                                            game.year, game.week.number)

                body += "\n"
                rcd = self.records.games["Highest Margin"]
                body += "[b]Largest Margin of Victory[/b]\n"
                for r in range(rcds):
                    game = rcd[r]
                    body += "{0} {1}, {2} {3} {4} {5} {6} week {7}\n".format(add_suffix(r+1),
                                                                            make_score(game.away_score, game.home_score),
                                                                            game.home_owner_name if game.winner == "Home"
                                                                            else game.away_owner_name,
                                                                            "tied" if game.winner == "Tie" else "won",
                                                                            "vs" if game.winner == "Home" else "at",
                                                                            game.away_owner_name if game.winner == "Home"
                                                                            else game.home_owner_name,
                                                                            game.year, game.week.number)

                body += "\n"
                rcd = self.records.games["Lowest Margin"]
                body += "[b]Smallest Margin of Victory[/b]\n"
                for r in range(rcds):
                    game = rcd[r]
                    body += "{0} {1}, {2} {3} {4} {5} {6} week {7}\n".format(add_suffix(r+1),
                                                                            make_score(game.away_score, game.home_score),
                                                                            game.home_owner_name if game.winner == "Home"
                                                                            else game.away_owner_name,
                                                                            "tied" if game.winner == "Tie" else "won",
                                                                            "vs" if game.winner == "Home" else "at",
                                                                            game.away_owner_name if game.winner == "Home"
                                                                            else game.home_owner_name,
                                                                            game.year, game.week.number)

            body += "\n"

            if seasons:
                rcd = self.records.season["Most PF"]
                body += "[b]Most PPG in a Single Season[/b]\n"
                for r in range(rcds):
                    ows = rcd[r]
                    body += "{0} {1:.1f} ppg, {2}{3}{4} ({5})\n".format(add_suffix(r+1),
                                                                       ows.ppg,
                                                                       ows.owner_name,
                                                                       "*" if ows.playoffs else "",
                                                                       "*" if ows.championship else "",
                                                                       ows.year)

                body += "\n"
                rcd = self.records.season["Fewest PF"]
                body += "[b]Fewest PPG in a Single Season[/b]\n"
                for r in range(rcds):
                    ows = rcd[r]
                    body += "{0} {1:.1f} ppg, {2}{3}{4} ({5})\n".format(add_suffix(r+1),
                                                                       ows.ppg,
                                                                       ows.owner_name,
                                                                       "*" if ows.playoffs else "",
                                                                       "*" if ows.championship else "",
                                                                       ows.year)

                body += "\n"
                rcd = self.records.season["Most PA"]
                body += "[b]Most PA/G in a Single Season[/b]\n"
                for r in range(rcds):
                    ows = rcd[r]
                    body += "{0} {1:.1f} {2}{3}{4} ({5})\n".format(add_suffix(r+1),
                                                                  ows.pag,
                                                                  ows.owner_name,
                                                                  "*" if ows.playoffs else "",
                                                                  "*" if ows.championship else "",
                                                                  ows.year)

                body += "\n"
                rcd = self.records.season["Fewest PA"]
                body += "[b]Fewest PA/G in a Single Season[/b]\n"
                for r in range(rcds):
                    ows = rcd[r]
                    body += "{0} {1:.1f} {2}{3}{4} ({5})\n".format(add_suffix(r+1),
                                                                  ows.pag,
                                                                  ows.owner_name,
                                                                  "*" if ows.playoffs else "",
                                                                  "*" if ows.championship else "",
                                                                  ows.year)

        return body.rstrip('\n')


class LeagueRecords:
    def __init__(self, league):
        self.league = league
        self.games = {"Highest Scoring": [], "Lowest Scoring": [], "Highest Margin": [], "Lowest Margin": [],
                      "Biggest Upset": []}
        self.season = {"Most PF": [], "Fewest PF": [], "Most PA": [], "Fewest PA": []}
        self.teams = {"Most PF": [], "Fewest PF": []}

    def check_records(self, matchup, key=None, number=50):
        if key is not None:
            keys = [key]
        else:
            keys = []
            keys += self.games.keys()
            keys += self.teams.keys()

        for key in keys:
            if key == "Most PF":
                rcd = self.league.records.teams[key]
                if len(rcd) < number:
                    rcd.append(matchup)
                else:
                    if rcd[-1].pf < matchup.pf:
                        rcd[-1] = matchup
                self.league.records.teams[key] = \
                    sorted(rcd, key=lambda param: param.pf, reverse=True)

            elif key == "Fewest PF":
                if not matchup.game.is_consolation:
                    rcd = self.league.records.teams[key]
                    if len(rcd) < number:
                        rcd.append(matchup)
                    else:
                        if rcd[-1].pf > matchup.pf:
                            rcd[-1] = matchup
                    self.league.records.teams[key] = \
                        sorted(rcd, key=lambda param: param.pf, reverse=False)

            elif key == "Highest Scoring":
                game = matchup.game
                rcd = self.league.records.games[key]
                if len(rcd) < number and game not in rcd:
                    rcd.append(game)
                elif game not in rcd:
                    if rcd[-1].away_score + rcd[-1].home_score < game.away_score + game.home_score:
                        rcd[-1] = game
                self.league.records.games[key] = \
                    sorted(rcd, key=lambda param: (param.away_score + param.home_score), reverse=True)

            elif key == "Lowest Scoring":
                if not matchup.game.is_consolation:
                    game = matchup.game
                    rcd = self.league.records.games[key]
                    if len(rcd) < number and game not in rcd:
                        rcd.append(game)
                    elif game not in rcd:
                        if rcd[-1].away_score + rcd[-1].home_score > game.away_score + game.home_score:
                            rcd[-1] = game
                    self.league.records.games[key] = \
                        sorted(rcd, key=lambda param: (param.away_score + param.home_score), reverse=False)

            elif key == "Highest Margin":
                if not matchup.game.is_consolation:
                    game = matchup.game
                    rcd = self.league.records.games[key]
                    if len(rcd) < number and game not in rcd:
                        rcd.append(game)
                    elif game not in rcd:
                        if abs(rcd[-1].away_score - rcd[-1].home_score) < abs(game.away_score - game.home_score):
                            rcd[-1] = game
                    self.league.records.games[key] = \
                        sorted(rcd, key=lambda param: abs(param.away_score - param.home_score), reverse=True)

            elif key == "Lowest Margin":
                if not matchup.game.is_consolation:
                    game = matchup.game
                    rcd = self.league.records.games[key]
                    if len(rcd) < number and game not in rcd:
                        rcd.append(game)
                    elif game not in rcd:
                        if abs(rcd[-1].away_score - rcd[-1].home_score) > abs(game.away_score - game.home_score):
                            rcd[-1] = game
                    self.league.records.games[key] = \
                        sorted(rcd, key=lambda param: abs(param.away_score - param.home_score), reverse=False)

            elif key == "Biggest Upset":
                if not matchup.game.is_consolation and matchup.won:
                    game = matchup.game
                    rcd = self.league.records.games[key]
                    if len(rcd) < 5000:
                        rcd.append(matchup)
                    else:
                        if rcd[-1].win_diff > matchup.win_diff:
                            rcd[-1] = matchup
                    self.league.records.games[key] = \
                        sorted(rcd, key=lambda param: param.win_diff, reverse=False)


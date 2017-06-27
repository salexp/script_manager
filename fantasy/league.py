from copy import deepcopy
from datetime import datetime

from fantasy.owner import Owner
from fantasy.rankings import Rankings
from fantasy.schedule import Schedule, schedule_from_sheet
from fantasy.year import Year
from util.fantasy import plotter
from util.fantasy.utilities import *
from util.sql.database import Database


class League:
    def __init__(self, espn_id, database_settings):
        self.db = Database(**database_settings)
        self.espn_id = espn_id
        self.url = "http://games.espn.go.com/ffl/leagueoffice?leagueId=%s" % espn_id
        # http://games.espn.go.com/ffl/leagueoffice?leagueId=190153

        query = """SELECT * FROM Leagues WHERE LEAGUE_ESPNID={}""".format(espn_id)
        self.db_entry = self.db.query_return_dict_single(query)
        self.league_name = self.db_entry['LEAGUE_NAME']

        query = """SELECT * FROM Users WHERE LEAGUE_ESPNID={}""".format(self.espn_id)
        owners = self.db.query_return_dict_lookup(query, 'USER_ESPNNAME')
        self.owners = {k: Owner(k, self, v) for k, v in owners.items()}

        query = """SELECT * FROM Games WHERE LEAGUE_ESPNID={}""".format(self.espn_id)
        games = self.db.query_return_dict_lookup(query, 'GAME_ID')
        self.db_games = games

        query = """SELECT DISTINCT YEAR FROM Games WHERE LEAGUE_ESPNID={}""".format(self.espn_id)
        years = self.db.query_return(query)
        self.years = {y: Year() for y in years}

        self.games = {}
        for y in years:
            query = """SELECT * FROM Games WHERE LEAGUE_ESPNID={} and YEAR={}""".format(self.espn_id, y)
            self.games[y] = query

        self.current_week = None
        self.current_year = None
        self.historic_playoffs = None
        self.future_playoffs = None
        self.lineup_positions = []
        self.players = {}
        self.power_rankings = {}
        self.rankings = []
        self.records = LeagueRecords(self)
        self.years = {}

    def add_history(self, years, book, push_database=False):
        for yi, year in enumerate(years):
            if len(years) < 7:
                yi = int(year[-1])

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

            if push_database:
                # Add something to add schedule to database
                pass

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

    def recursive_rankings(self, year=None):
        if year is None:
            year = max(self.years.keys())

        self.current_week = self.years[year].current_week
        self.current_year = year

        weeks = [str(w) for w in range(1, int(self.current_week)+1)]
        for week in weeks:
            self.generate_rankings(week=week, plot=week is weeks[-1])

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
                diff = self.rankings[i_last_week].ranks[owner.name] - self.rankings[i_week].ranks[owner.name]
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
            body += "[b]Team of the Week (Week {})[/b]\n".format(week)
            pos = ["QB", "RB1", "RB2", "WR1", "WR2", "FLX", "TE", "DST", "K"]
            for p, plyr in enumerate([rstr.qb, rstr.rb1, rstr.rb2, rstr.wr1, rstr.wr2, rstr.flx, rstr.te, rstr.dst, rstr.k]):
                body += "{0}. {1} ({2}, {3}) - {4}\n".format(pos[p],
                                                             plyr.name,
                                                             plyr.owner.name,
                                                             "benched" if plyr.slot == "Bench" else "started",
                                                             plyr.points)
            body += "Total Score: {}\n".format(rstr.starter_points)

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
                        gm.away_owner.initials(),
                        "+" if p.home_favorite else " ",
                        p.away_spread,
                        p.away_payout,
                        p.away_moneyline,
                        "+" if p.under_favorite and p.over_payout != 100 else " -" if p.over_payout != 100 else "",
                        "{:.0f}".format(p.over_payout) if p.over_payout != 100 else "PUSH",
                        p.ou,)
                    body += "{0}| S:{1}{2:.1f}{1}{3:.0f} ML:{1}{4} U:{5}{6}\n".format(
                        gm.home_owner.initials(),
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
                        gm.away_owner.first_name() if away_all else gm.home_owner.first_name() if home_all else "Series",
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

        return body


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


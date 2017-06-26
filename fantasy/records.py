from nfl_data import roster


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

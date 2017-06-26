class Rankings:
    def __init__(self, league):
        self.owners = {}
        self.keys = None
        self.ranks = {}
        self.roster = None
        self.week = None
        self.year = None

    def add_owner(self, owner, year, week):
        if owner.name not in self.owners:
            self.week = week
            self.year = year
            mtrcs = Metrics(self, owner)
            self.owners[owner.name] = mtrcs
            self.keys = mtrcs.keys


class Metrics:
    def __init__(self, rankings, owner, length=None):
        self.keys = {"QB":   1.2,
                     "RB":   1.3,
                     "WR":   1.3,
                     "TE":   1.1,
                     "D/ST": 1.1,
                     "K":    1.0,
                     "WP":   1.5,
                     "PF":   1.5,
                     "PA":   0.7,
                     "PLOB": 1.0}
        self.league = owner.league
        self.owner = owner
        self.power_rank = None
        self.week = rankings.week
        self.year = rankings.year

        self.ranks = {}
        for k in self.keys:
            self.ranks[k] = 0

        qb = []
        rb = []
        wr = []
        te = []
        dst = []
        k = []
        bench = []
        pf = 0.0
        pa = 0.0
        wpct = 0.0
        plob = 0.0

        if length is None:
            length = int(self.week)
        years = [str(y) for y in range(int(self.year)-1, int(self.year)+1)]
        matchups = []
        for y in years:
            matchups += owner.seasons[y].matchups

        cw = int(self.league.current_week)
        matchups = matchups[len(matchups)-cw:len(matchups)-cw+length]
        for matchup in matchups:
            qb.append(matchup.roster.qb.points)
            rb.append(matchup.roster.rb1.points)
            rb.append(matchup.roster.rb2.points)
            if matchup.roster.rb3 is not None:
                rb.append(matchup.roster.rb3.points)
            wr.append(matchup.roster.wr1.points)
            wr.append(matchup.roster.wr2.points)
            if matchup.roster.wr3 is not None:
                wr.append(matchup.roster.wr3.points)
            te.append(matchup.roster.te.points)
            dst.append(matchup.roster.dst.points)
            k.append(matchup.roster.k.points)
            bench.append(matchup.roster.bench_points / len(matchup.roster.bench))
            for pg in matchup.roster.bench:
                if not pg.bye:
                    plyr = pg.player
                    pts = pg.points
                    if plyr.position == "QB":
                        qb.append(pts)
                    elif plyr.position == "RB":
                        rb.append(pts)
                    elif plyr.position == "WR":
                        wr.append(pts)
                    elif plyr.position == "TE":
                        te.append(pts)
                    elif plyr.position == "D/ST":
                        dst.append(pts)
                    elif plyr.position == "K":
                        k.append(pts)

            wpct += matchup.won
            pf += matchup.pf
            pa += matchup.pa

            matchup.roster.make_optimal()
            plob += (matchup.roster.optimal.starter_points - matchup.roster.starter_points)

        qb = sorted(qb, reverse=True)
        rb = sorted(rb, reverse=True)
        wr = sorted(wr, reverse=True)
        te = sorted(te, reverse=True)
        dst = sorted(dst, reverse=True)
        k = sorted(k, reverse=True)

        if len(qb) > 1.5 * length:
            qb = qb[:int(1.5*length)]
        if len(rb) > 4 * length:
            rb = rb[:int(4*length)]
        if len(wr) > 4 * length:
            wr = wr[:int(4*length)]
        if len(te) > 1.5 * length:
            te = te[:int(1.5*length)]
        if len(dst) > 1.5 * length:
            dst = dst[:int(1.5*length)]
        if len(k) > 1 * length:
            k = k[:int(1*length)]

        self.qb = sum(qb) / len(qb)
        self.rb = sum(rb) / len(rb)
        self.wr = sum(wr) / len(wr)
        self.te = sum(te) / len(te)
        self.dst = sum(dst) / len(dst)
        self.k = sum(k) / len(k)
        self.wpct = wpct / length
        self.pf = pf / length
        self.pa = pa / length
        self.plob = plob / length

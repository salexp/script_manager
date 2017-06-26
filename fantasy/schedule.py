from fantasy.week import Week


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

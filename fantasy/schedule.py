from fantasy.week import Week


class Schedule:
    def __init__(self, league, year):
        self.complete = False
        self.league = league
        self.owners = []
        self.year = year

        self.week_list = []
        self.weeks = {}

    def add_week(self, w):
        self.week_list.append(w.number)
        self.weeks[w.number] = w


def schedule_from_sheet(league, sheet, year):
    schedule = Schedule(league, year)

    wek = 0
    found_division = False
    for r in range(sheet.nrows):
        if "WEEK" in sheet.cell_value(r, 0) or "ROUND" in sheet.cell_value(r, 0):
            wek += 1
            week = Week(schedule, str(wek), sheet, r)
            schedule.add_week(week)
            schedule.complete = week.complete
            if not len(schedule.owners):
                schedule.owners = week.owners
            if schedule.complete:
                schedule.league.years[year].current_week = week.number
                schedule.league.years[year].current_year = year
        elif "Byes" in sheet.cell_value(r, 0):
            found_division = True
            for owner in schedule.owners:
                if owner not in week.owners:
                    owner.add_division_championship(year)

    if not found_division and schedule.complete:
        for wi, week in enumerate(schedule.week_list):
            if schedule.weeks[week].is_postseason():
                break

        standings = []
        for owner in schedule.owners:
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
                schedule.league.owners[f[0]].add_division_championship(year)

    return schedule

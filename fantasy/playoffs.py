import csv


class FuturePlayoffs:
    def __init__(self, datfile, league):
        self.datfile = datfile
        self.league = league

        self.scenarios = []

        with open(datfile, 'rb') as f:
            byte_list = f.read()

        self.bytes = [b for b in bytearray(byte_list)]
        scenarios = [self.bytes[i:i+42] for i in range(0, len(self.bytes), 42)]

        for scenario in scenarios:
            sc = PlayoffScenario(scenario, playoffs=self)
            self.scenarios.append(sc)

    def export_csv(self, outfile):
        owners = sorted(self.league.owners.values(), key=lambda k: k.name)

        with open(outfile, 'wb') as csvfile:
            writer = csv.writer(csvfile)

            games_left = len(self.scenarios[0].games)
            headers = ['Game ' + str(i + 1) for i in range(games_left)]
            headers += ['PF', 'D1', 'D2', 'W1', 'W2', 'W3', 'W4']
            headers += [o.first_name for o in owners]
            writer.writerow(headers)

            for sc in self.scenarios:
                for hs, outcome in sc.hi_scorers.items():
                    write_row = [o.first_name for o in sc.winners]
                    write_row += [hs.first_name if hs is not None else hs]
                    write_row += [o.first_name for o in outcome['Division']]
                    write_row += [o.first_name for o in outcome['Wildcard']]
                    write_row += ['1' if o in outcome['Division'] or o in outcome['Wildcard'] else '0' for o in owners]
                    writer.writerow(write_row)


class PlayoffScenario:
    def __init__(self, outcome_list, playoffs):
        self.outcome_list = outcome_list
        self.playoffs = playoffs

        self.games = self.playoffs.league.years[self.playoffs.league.current_year].schedule.games_left

        games_outcome = outcome_list[0:2]
        result_outcomes = outcome_list[2:]
        self.games_outcomes = sum([n << (8 if not i else 0) for i, n in enumerate(games_outcome)])
        self.games_outcomes_bin = bin(self.games_outcomes).split('b')[1].zfill(len(self.games))

        self.winners = [g.away_owner if int(self.games_outcomes_bin[i]) else g.home_owner for i, g in enumerate(self.games)]

        self.hi_scorers = {}
        for h, hi_score in enumerate(range(len(result_outcomes) / 4)):
            outcome = result_outcomes[4 * h: 4 * h + 4]
            hi_scorer = outcome[0]
            divisions = outcome[1] >> 4, outcome[1] % 16
            wildcards = outcome[2] >> 4, outcome[2] % 16, outcome[3] >> 4, outcome[3] % 16

            division_players = [self.playoffs.league.find_owner(o, 'ESPN_USER_ID') for o in divisions]
            wildcard_players = [self.playoffs.league.find_owner(o, 'ESPN_USER_ID') for o in wildcards]
            if None in wildcard_players or None in division_players:
                True
            self.hi_scorers[self.playoffs.league.find_owner(hi_scorer, 'ESPN_USER_ID')] = {'Division': division_players, 'Wildcard': wildcard_players}

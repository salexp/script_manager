from util.fantasy.utilities import *


class GameRoster:
    def __init__(self, opt=False):
        self.qb = None
        self.rb1 = None
        self.rb2 = None
        self.rb3 = None
        self.wr1 = None
        self.wr2 = None
        self.wr3 = None
        self.flx = None
        self.te = None
        self.dst = None
        self.k = None
        self.starters = []
        self.bench = []
        self.ir = None
        self.starter_points = 0.0
        self.bench_points = 0.0
        self.complete = False
        self.is_optimal = opt

        self._optimal = None

    @property
    def optimal(self):
        if self._optimal is None:
            self.make_optimal()
        return self._optimal

    def add_player(self, plyr_game, force=None):
        if "QB" == plyr_game.slot and not force or force == "QB":
            self.starters.append(plyr_game)
            self.starter_points += plyr_game.points
            self.qb = plyr_game
        elif "RB" == plyr_game.slot and not force or force == "RB":
            self.starters.append(plyr_game)
            self.starter_points += plyr_game.points
            if self.rb1 is None:
                self.rb1 = plyr_game
            elif self.rb2 is None:
                self.rb2 = plyr_game
            else:
                self.rb3 = plyr_game
                self.flx = plyr_game
        elif "WR" == plyr_game.slot and not force or force == "WR":
            self.starters.append(plyr_game)
            self.starter_points += plyr_game.points
            if self.wr1 is None:
                self.wr1 = plyr_game
            elif self.wr2 is None:
                self.wr2 = plyr_game
            else:
                self.wr3 = plyr_game
                self.flx = plyr_game
        elif "RB/WR" == plyr_game.slot and not force or force == "RB/WR":
            self.starters.append(plyr_game)
            self.starter_points += plyr_game.points
            self.flx = plyr_game
        elif "TE" == plyr_game.slot and not force or force == "TE":
            self.starters.append(plyr_game)
            self.starter_points += plyr_game.points
            self.te = plyr_game
        elif "D/ST" == plyr_game.slot and not force or force == "D/ST":
            self.starters.append(plyr_game)
            self.starter_points += plyr_game.points
            self.dst = plyr_game
        elif "K" == plyr_game.slot and not force or force == "K":
            self.starters.append(plyr_game)
            self.starter_points += plyr_game.points
            self.k = plyr_game
        elif "Bench" == plyr_game.slot and not force or force == "Bench":
            self.bench_points += plyr_game.points
            self.bench.append(plyr_game)
        elif "IR" == plyr_game.slot and not force or force == "IR":
            self.ir = plyr_game

        self.complete = self.qb is not None and self.rb1 is not None and self.rb2 is not None and self.wr1 is not None \
                        and self.wr2 is not None and self.flx is not None and self.dst is not None \
                        and self.k is not None

        if self.complete:
            self.sort_skill_positions()

    def sort_skill_positions(self):
        rbs = []
        if self.rb1 is not None: rbs.append(self.rb1)
        if self.rb2 is not None: rbs.append(self.rb2)
        wrs = []
        if self.wr1 is not None: wrs.append(self.wr1)
        if self.wr2 is not None: wrs.append(self.wr2)
        pos = self.flx.player.position if self.flx is not None else None
        if pos == "RB":
            rbs.append(self.flx)
        elif pos == "WR":
            wrs.append(self.flx)

        rbs = sorted(rbs, key=lambda p: p.points, reverse=True)
        wrs = sorted(wrs, key=lambda p: p.points, reverse=True)

        self.rb1 = rbs[0] if len(rbs) > 0 else None
        self.rb2 = rbs[1] if len(rbs) > 1 else None
        self.wr1 = wrs[0] if len(wrs) > 0 else None
        self.wr2 = wrs[1] if len(wrs) > 1 else None
        self.flx = rbs[2] if len(rbs) > 2 else wrs[2] if len(wrs) > 2 else None
        self.rb3 = self.flx if pos == "RB" else None
        self.wr3 = self.flx if pos == "WR" else None

    def make_optimal(self):
        opt = GameRoster(opt=True)
        other = []
        qbs = []
        if self.qb is not None: qbs += [self.qb]
        rbs = []
        if self.rb1 is not None: rbs += [self.rb1]
        if self.rb2 is not None: rbs += [self.rb2]
        if self.rb3 is not None: rbs += [self.rb3]
        wrs = []
        if self.wr1 is not None: wrs += [self.wr1]
        if self.wr2 is not None: wrs += [self.wr2]
        if self.wr3 is not None: wrs += [self.wr3]
        tes = []
        if self.te is not None: tes += [self.te]
        dsts = []
        if self.dst is not None: dsts += [self.dst]
        ks = []
        if self.k is not None: ks += [self.k]

        for plyr in self.bench:
            if plyr.player.position == "QB":
                qbs.append(plyr)
            elif plyr.player.position == "RB":
                rbs.append(plyr)
            elif plyr.player.position == "WR":
                wrs.append(plyr)
            elif plyr.player.position == "TE":
                tes.append(plyr)
            elif plyr.player.position == "D/ST":
                dsts.append(plyr)
            elif plyr.player.position == "K":
                ks.append(plyr)
            elif plyr.player.position == "RB,WR":
                other.append(plyr)

        qbs = sorted(qbs, key=lambda p: p.points, reverse=True)
        rbs = sorted(rbs, key=lambda p: p.points, reverse=True)
        wrs = sorted(wrs, key=lambda p: p.points, reverse=True)
        tes = sorted(tes, key=lambda p: p.points, reverse=True)
        dsts = sorted(dsts, key=lambda p: p.points, reverse=True)
        ks = sorted(ks, key=lambda p: p.points, reverse=True)

        if len(other):
            for plyr in other:
                rbb = reverse_bisect([p.points for p in rbs], plyr.points)
                wrb = reverse_bisect([p.points for p in wrs], plyr.points)
                if rbb < wrb:
                    rbs.insert(rbb, plyr)
                else:
                    wrs.insert(wrb, plyr)

        opt.add_player(qbs[0], force="QB")
        qbs = qbs[1:]
        opt.add_player(rbs[0], force="RB")
        opt.add_player(rbs[1], force="RB")
        rbs = rbs[2:]
        opt.add_player(wrs[0], force="WR")
        opt.add_player(wrs[1], force="WR")
        wrs = wrs[2:]
        if not len(wrs):
            flx = rbs[0]
            flx_rb = True
        elif not len(rbs):
            flx = wrs[0]
            flx_rb = False
        else:
            flx = rbs[0] if rbs[0].points > wrs[0].points else wrs[0]
            flx_rb = rbs[0].points > wrs[0].points
        opt.add_player(flx, force="RB/WR")
        if flx_rb:
            rbs = rbs[1:]
        else:
            wrs = wrs[1:]
        opt.add_player(tes[0], force="TE")
        tes = tes[1:]
        opt.add_player(dsts[0], force="D/ST")
        dsts = dsts[1:]
        opt.add_player(ks[0], force="K")
        ks = ks[1:]

        for bp in qbs + rbs + wrs + tes + dsts + ks:
            opt.add_player(bp, force="Bench")

        self._optimal = opt

    def update_points(self):
        self.starter_points = self.qb.points + self.rb1.points + self.rb2.points + self.wr1.points + self.wr2.points + self.flx.points + self.te.points + self.dst.points + self.k.points
        self.bench_points = sum([p.points for p in self.bench])

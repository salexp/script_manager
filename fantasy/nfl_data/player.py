from util.statistics.std_normal import StdNormal
from util.utilities import *


class Player:
    def __init__(self, info):
        self.games_ir = 0
        self.games_owned = 0
        self.games_started = 0
        self.benched = []
        self.ir = []
        self.name = get_name(info[1])
        self.points = 0.0
        self.ppg = 0.0
        self.position = get_position(info[1])

        self.attributes = PlayerAttributes(self)

        self._games_lost = None
        self._games_won = None
        self._games_started_lost = None
        self._games_started_won = None
        self._owned = []
        self._started = []

    @property
    def games_lost(self):
        if self._games_lost is None:
            self._games_lost = sum([g.matchup.lost for g in self.owned])
        return self._games_lost

    @property
    def games_won(self):
        if self._games_won is None:
            self._games_won = sum([g.matchup.won for g in self.owned])
        return self._games_won

    @property
    def games_started_lost(self):
        if self._games_started_lost is None:
            self._games_started_lost = sum([g.matchup.lost for g in self.started])
        return self._games_started_lost

    @property
    def games_started_won(self):
        if self._games_started_won is None:
            self._games_started_won = sum([g.matchup.won for g in self.started])
        return self._games_started_won

    @property
    def owned(self):
        return sorted(self._owned, key=lambda k: k.matchup.game.week_stamp)

    @property
    def started(self):
        return sorted(self._started, key=lambda k: k.matchup.game.week_stamp)

    def update(self, matchup, info, slot):
        plyr_game = PlayerGame(self, matchup, info, slot)
        self.games_owned += 1
        self._owned.append(plyr_game)
        self.points += plyr_game.points
        self.ppg = self.points / self.games_owned
        matchup.roster.add_player(plyr_game)
        if plyr_game.slot not in ["Bench", "IR"]:
            self.games_started += 1
            self._started.append(plyr_game)
            if slot not in matchup.league.lineup_positions:
                matchup.league.lineup_positions.append(slot)
        elif plyr_game.slot == "Bench":
            self.benched.append(plyr_game)
            self.ir.append(plyr_game)
        elif plyr_game.slot == "IR":
            self.games_ir += 1
            self.ir.append(plyr_game)

        self.attributes.update(n_games=self.games_owned)


class NonePlayer(Player):
    def __init__(self, info):
        Player.__init__(self, info)


class PlayerAttributes:
    def __init__(self, player):
        self.player = player
        self.mu = 0.0
        self.ssq = 0.0
        self.sigma = 0.0
        self.wavg = 0.0

        if self.player.games_owned > 0:
            self.update(n_games=self.player.games_owned)

    def check_points(self, points):
        Z = (points - self.mu) / self.sigma
        return 1 - StdNormal.get_phi_z(Z)

    def update(self, start_game=None, n_games=10):
        matchups = self.player.owned[-n_games:]
        points = [m.points for m in matchups]

        self.mu = sum(points) / len(points)
        self.ssq = sum_sqs(points)
        self.sigma = std_dev(points, self.ssq)
        self.wavg = avgw(points)


class PlayerGame:
    def __init__(self, player, matchup, info, slot):
        self.bye = "BYE" in info[2]
        self.matchup = matchup
        self.name = player.name
        self.owner = matchup.owner
        self.player = player
        self.slot = slot

        try:
            self.points = float(info[4])
        except ValueError:
            self.points = 0.0


def get_name(st):
    if "D/ST" not in st:
        name = st.split(",")[0].replace("*", "")
    else:
        name = st.split(" ")[0]
    return name


def get_position(st):
    st = st.replace(u'\xa0', u' ')
    if "QB" in st:
        pos = "QB"
    elif "RB" in st and "WR" not in st:
        pos = "RB"
    elif "WR" in st and "RB" not in st:
        pos = "WR"
    elif "WR" in st and "RB" in st:
        pos = "RB,WR"
    elif "TE" in st:
        pos = "TE"
    elif "D/ST" in st:
        pos = "D/ST"
    elif "K" in st.split(" "):
        pos = "K"
    else:
        pos = None
    return pos

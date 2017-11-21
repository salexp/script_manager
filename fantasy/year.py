from util.utilities import *


class Year:
    def __init__(self):
        self._all_games = None
        self._ppg_average = None
        self._ppg_std_deviation = None

        self.current_week = None
        self.current_year = None
        self.owner_seasons = {}
        self.schedule = None

    @property
    def all_games(self):
        if self._all_games is None:
            self._all_games = []
            for w, week in self.schedule.weeks.items():
                self._all_games += week.games
        return self._all_games

    @property
    def ppg_average(self):
        if self._ppg_average is None:
            self._ppg_average = avg([os.ppg for os in self.owner_seasons.values()])
        return self._ppg_average

    @property
    def ppg_std_deviation(self):
        if self._ppg_std_deviation is None:
            self._ppg_std_deviation = std_dev([os.ppg for os in self.owner_seasons.values()])
        return self._ppg_std_deviation

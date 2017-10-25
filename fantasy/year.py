class Year:
    def __init__(self):
        self._all_games = None

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

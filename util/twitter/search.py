from tweepy import SearchResults


class EmptyResults(SearchResults):
    count = 0

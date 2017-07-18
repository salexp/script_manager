import tweepy
from tweepy.error import TweepError, RateLimitError
from util.twitter.search import EmptyResults

from util import logger
from util.limiter import limiter


class APISession(tweepy.API):
    def __init__(self, c_key, c_secret, a_token, a_token_secret):
        logger.debug("Establishing connection to Twitter")
        self.last_response = None

        auth = tweepy.OAuthHandler(c_key, c_secret)
        auth.set_access_token(a_token, a_token_secret)
        tweepy.API.__init__(self, auth)

        self.active = self._open()

        self.search_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    # --- Instance Methods

    def _open(self):
        try:
            self.active = self.verify_credentials()
            logger.debug("Successfully authenticated")
            return True
        except TweepError as e:
            logger.debug("Error attempting to authenticate")
            return False

    def clear_timeline(self):
        count = 0
        statuses = self.home_timeline()
        while len(statuses):
            for status in statuses:
                status.destroy()
                count += 1
            statuses = self.home_timeline()

        return count

    @limiter(450, 900)
    def search(self, *args, **kwargs):
        self.search_count += 1
        try:
            return super(APISession, self).search(*args, **kwargs)
        except RateLimitError:
            logger.warning("Hit rate limit for searching after %s searches" % self.search_count)
            return EmptyResults()

    def search_all(self, query, max_count=None, increment=100):
        all_results = []
        n = 99999 + increment
        max_id = None

        while n >= increment:
            results = self.search(query, count=max_count, max_id=max_id, result_type='recent')
            n = results.count
            max_id = results.max_id
            all_results += [_ for _ in results]

            if max_count is not None and len(all_results) > max_count:
                all_results = all_results[:max_count]
                break

        return all_results

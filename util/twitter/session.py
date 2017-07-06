import tweepy
from tweepy.error import TweepError

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

    @limiter(2, 1.0)
    def search(self, *args, **kwargs):
        return super(APISession, self).search(*args, **kwargs)

    def recursive_search(self, query, max_count=1000, increment=100):
        all_results = []
        n = 99999 + increment
        max_id = None

        while n >= increment:
            results = self.search(query, count=increment, max_id=max_id)
            n = results.count
            max_id = results.max_id
            all_results += [_ for _ in results]

            if len(all_results) > max_count:
                break

        return all_results

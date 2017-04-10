import tweepy
from tweepy.error import TweepError

from util import logger


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

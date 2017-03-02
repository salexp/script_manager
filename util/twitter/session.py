import logging

import tweepy
from tweepy.error import TweepError


class APISession(tweepy.API):
    def __init__(self, c_key, c_secret, a_token, a_token_secret):
        logging.info("Establishing connection to Twitter")
        self.last_response = None

        auth = tweepy.OAuthHandler(c_key, c_secret)
        auth.set_access_token(a_token, a_token_secret)
        tweepy.API.__init__(self, auth)

        self.active = self._open()

    def _open(self):
        try:
            self.active = self.verify_credentials()
            logging.info("Successfully authenticated")
            return True
        except TweepError as e:
            logging.error("Error attempting to authenticate")
            return False
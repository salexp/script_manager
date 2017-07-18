import re


class Tweet:
    def __init__(self, status):
        self.created = status.created_at
        self.favorite_count = status.favorite_count
        self.raw_text = status.text
        self.retweet_count = status.retweet_count
        self.user_id = status.user.id

        self._text = None

    @property
    def text(self):
        if self._text is None:
            text = self.raw_text
            text = re.sub(r"http\S+", "", text)
            text = re.sub("&#?\w+;", "", text)
            text = re.sub("[\[\]\(\)\:\;\*]", "", text)
            text = text.replace("'", "")
            text = text.replace('"', "")
            text = re.sub("\n", "", text)
            text = re.sub(' +', ' ', text)
            self._text = text
        return self._text


def tweets_from_list(tweets):
    return [Tweet(_) for _ in tweets]

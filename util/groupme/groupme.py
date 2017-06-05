import requests
from requests import session


class GMeBot:
    def __init__(self, bot_id, group_id):
        self.bot_id = bot_id
        self.group_id = group_id

        self.uri = "https://api.groupme.com/v3/bots/post"
        self.session = session()

    def __post(self, data):
        self.session.post(self.uri, data=data)

    def say(self, text):
        data = {'bot_id': self.bot_id, 'text': text}
        self.__post(data)


class GroupMe:
    def __init__(self, auth_id):
        self.auth_id = auth_id

        self.uri = "https://api.groupme.com/v3/"
        self.session = session()

        auth = self.session.get("https://api.groupme.com/v3/groups?token={}".format(auth_id))
        self.active = auth.status_code == 200

    def __post(self, uri, data):
        r = self.session.post(uri, json=data)

    def _url(self, *args):
        url = self.uri + "/".join(args) + '?token=' + self.auth_id
        return url

    def say(self, text):
        data = {'message': {"text": text, "source_guid": "PY"}}
        self.__post(self._url('groups', '31565455', 'messages'), data)


if __name__ == '__main__':
    # gmbot = GMeBot('51ca226dadc1679d0f35b87814', '31565455')
    # gmbot.say('hello!')
    grpme = GroupMe('a18445d02c650135596377fc92423bce')
    grpme.say("testing2")

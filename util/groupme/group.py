from member import GMeMember


class GMeGroup:
    def __init__(self, groupme, dict_):
        self.groupme = groupme
        self.raw = dict_

        self.id = dict_['id']
        self.members = [GMeMember(groupme=self.groupme, dict_=_, group=self) for _ in dict_['members']]
        self.name = dict_['name']

    def say(self, text):
        self.groupme.say(self.id, text)

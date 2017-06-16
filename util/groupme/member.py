class GMeMember:
    def __init__(self, groupme, dict_, group=None):
        self.groups = []
        self.raw = dict_
        self.groupme = groupme

        self.id = dict_['id']
        self.name = dict_['nickname']
        self.user_id = dict_['id']

        if group is not None:
            self.add_group(group)

    def add_group(self, group):
        self.groups.append(group)

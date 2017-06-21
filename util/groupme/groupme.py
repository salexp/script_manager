class GroupMe:
    def __init__(self, auth_id):
        self.auth_id = auth_id

        self.uri = "https://api.groupme.com/v3/"
        self.session = session()

        groups = self.session.get(self._url('groups'))
        self.active = groups.status_code == 200

        self.groups = []
        self.users = {}

        if self.active:
            res = json.loads(groups.content)
            self.groups = [GMeGroup(groupme=self, dict_=_) for _ in res['response']]

    def __post(self, uri, data):
        r = self.session.post(uri, json=data)

    def _url(self, *args):
        url = self.uri + "/".join(args) + '?token=' + self.auth_id
        return url

    def find_group(self, id=None, name=None):
        found = None

        if id is None and name is None:
            raise
        elif id is not None:
            f = [g for g in self.groups if int(g.id) == int(id)]
            if len(f) == 1:
                found = f[0]
        elif name is not None:
            f = [g for g in self.groups if str(g.name) == str(name)]
            if len(f) == 1:
                found = f[0]

        return found

    def say(self, group_id, text):
        data = {'message': {"text": text, "source_guid": "PY"}}
        self.__post(self._url('groups', group_id, 'messages'), data)

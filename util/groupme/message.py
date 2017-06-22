class GMeMessage:
    def __init__(self, data, listening):
        self.data = data
        self.listening = listening

        self._is_command = None
        self._command = None

        self._sender = None

    @property
    def is_command(self):
        if self._is_command is None:
            self._is_command = self.data['text'].startswith('!') and ';' not in self.data['text']
        return self._is_command

    @property
    def command(self):
        if self.is_command and self._command is None:
            self._command = self.data['text'].partition(' ')[0].lower()
        return self._command

    @property
    def sender(self):
        if self.is_command and self._sender is None:
            self._sender = self.data['sender_id']
        return self._sender

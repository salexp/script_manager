commands = {
    '!help': 'help',
}


class GMeMessage:
    def __init__(self, data, listening):
        self.data = data
        self.listening = listening

        self._is_command = None
        self._command = None

    @property
    def is_command(self):
        if self._is_command is None:
            self._is_command = self.data['text'].startswith('!')
        return self._is_command

    @property
    def command(self):
        if self.is_command and self._command is None:
            self._command = self.data['text'].partition(' ')[0].lower()
        return self._command

class Command:
    def __init__(self, created, requestor, text, force_text=None):
        self.created = created
        self.requester = requestor
        self.text = text if force_text is None else force_text

        full_key, other = self.text.partition(' ')[::2]
        value, other = other.partition(' ')[::2]
        value = None if value == '' else value

        self.key = full_key.split('-')[0]
        self.option = full_key.split('-')[1] if '-' in full_key else None
        self.value = value
        self.other = other

        self.help = '?' == self.option

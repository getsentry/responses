class ResponseException(Exception):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.get("request")
        self.response = kwargs.get("response")
        super().__init__(*args)

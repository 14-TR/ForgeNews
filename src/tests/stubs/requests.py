class Response:
    def __init__(self):
        self.status_code = 200
    def json(self):
        return {}

def get(*args, **kwargs):
    return Response()

def post(*args, **kwargs):
    return Response()


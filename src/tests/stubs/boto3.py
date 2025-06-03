class session:
    class Session:
        def __init__(self, *args, **kwargs):
            pass
        def client(self, *args, **kwargs):
            class Dummy:
                def get_secret_value(self, *a, **kw):
                    return {"SecretString": "{}"}
            return Dummy()


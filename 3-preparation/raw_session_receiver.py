from common.json_io import JsonIO


class RawSessionReceiver:
    def receive_raw_session(self, path: str):
        return JsonIO.load(path)
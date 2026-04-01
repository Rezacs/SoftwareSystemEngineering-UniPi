from common.json_io import JsonIO


class PreparedSessionController:
    def receive_prepared_session(self, path: str):
        return JsonIO.load(path)

    def load_existing_sessions(self, path: str):
        try:
            data = JsonIO.load(path)
            return data if isinstance(data, list) else []
        except FileNotFoundError:
            return []

    def save_sessions(self, sessions: list, path: str):
        JsonIO.save(path, sessions)
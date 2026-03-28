from .utils.json_io import JsonIO


class SessionRepository:
    def receive(self, path: str):
        return JsonIO.load(path)

    def store(self, prepared_session: dict, path: str):
        stored_sessions = self.receiveStored(path)
        stored_sessions.append(prepared_session)
        JsonIO.save(path, stored_sessions)
        return stored_sessions

    def receiveStored(self, path: str):
        try:
            data = JsonIO.load(path)
            return data if isinstance(data, list) else []
        except FileNotFoundError:
            return []

    def receive_prepared_session(self, path: str):
        return self.receive(path)

    def load_existing_sessions(self, path: str):
        return self.receiveStored(path)

    def save_sessions(self, sessions: list, path: str):
        JsonIO.save(path, sessions)

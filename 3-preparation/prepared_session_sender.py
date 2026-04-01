from common.json_io import JsonIO


class PreparedSessionSender:
    def send_prepared_session(self, prepared_session: dict, output_path: str):
        JsonIO.save(output_path, prepared_session)
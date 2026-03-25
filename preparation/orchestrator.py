from preparation.raw_session_receiver import RawSessionReceiver
from preparation.prepared_session_creator import PreparedSessionCreator
from preparation.prepared_session_sender import PreparedSessionSender


class PreparationSystemOrchestrator:
    def __init__(self):
        self.receiver = RawSessionReceiver()
        self.creator = PreparedSessionCreator()
        self.sender = PreparedSessionSender()

    def run(
        self,
        input_path="data/outputs/raw_session.json",
        output_path="data/outputs/prepared_session.json"
    ):
        raw_session = self.receiver.receive_raw_session(input_path)
        prepared_session = self.creator.create_prepared_session(raw_session)
        self.sender.send_prepared_session(prepared_session, output_path)
        return prepared_session
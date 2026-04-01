from common.json_io import JsonIO
from ingestion.record_receiver import RecordReceiver
from ingestion.raw_session_creator import RawSessionCreator


class IngestionSystemOrchestrator:
    def __init__(self):
        self.receiver = RecordReceiver()
        self.creator = RawSessionCreator()

    def run(self,
            input_path="data/outputs/client_message.json",
            output_path="data/outputs/raw_session.json"):
        record = self.receiver.receive_record(input_path)

        if not self.receiver.validate_record(record):
            raise ValueError("Invalid input record received by Ingestion System")

        raw_session = self.creator.create_raw_session(record)
        JsonIO.save(output_path, raw_session)

        return raw_session
from client_side.service import ClientSideService
from client_side.timestamp_log_controller import TimestampLogController

service = ClientSideService()
logger = TimestampLogController()

message = service.save_json_message()

print("Generated JSON message:")
print(message)

log = logger.create_log_entry("client_message_generated")
print("\nTimestamp log:")
print(log)
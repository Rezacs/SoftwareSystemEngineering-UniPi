from common.storage_controller import StorageController

storage = StorageController()
storage.store({"id": 1, "name": "record1"})
storage.store({"id": 2, "name": "record2"})

print(storage.retrieve_all())

storage.clear()
print(storage.retrieve_all())
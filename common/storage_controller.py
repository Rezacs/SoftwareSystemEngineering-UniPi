class StorageController:
    def __init__(self):
        self.data = []

    def store(self, item):
        self.data.append(item)

    def retrieve_all(self):
        return self.data.copy()

    def clear(self):
        self.data.clear()
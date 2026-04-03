class Record:
    
    def __init__(self):
        self.uuid=-1
        self.samples=list()

    def get_uuid(self):
        return self.uuid
    
    def set_uuid(self,uuid):
        self.uuid = uuid

    def get_samples(self) -> list:
        return self.samples
    
    def add_sample(self,sample : dict):
        self.samples.append(sample)
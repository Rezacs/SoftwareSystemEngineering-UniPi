from .utils.json_io import JsonIO


class BufferController:
    def load_buffer(self, path: str) -> list:
        try:
            data = JsonIO.load(path)
            return data if isinstance(data, list) else []
        except FileNotFoundError:
            return []

    def save_buffer(self, buffer_data: list, path: str) -> None:
        JsonIO.save(path, buffer_data)

    def add_label_pair(self, label_pair: dict, path: str) -> list:
        buffer_data = self.load_buffer(path)
        buffer_data.append(label_pair)
        self.save_buffer(buffer_data, path)
        return buffer_data

    def clear_buffer(self, path: str) -> None:
        self.save_buffer([], path)

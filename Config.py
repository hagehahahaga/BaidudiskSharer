import json
import os


class Config(dict):
    """
    You can use it like a dict naturally by with it as an object
    """

    def __init__(self, file: str) -> None:
        self.file = file

        if not os.path.exists(self.file):
            super().__init__()
            return

        with open(self.file, mode='r') as file:
            super().__init__(json.load(file))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        with open(self.file, mode='w') as file:
            json.dump(self, file, indent=2)

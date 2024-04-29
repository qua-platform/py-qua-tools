from typing import Any


class Definition:
    def __init__(self, name: str, type: str, value: Any):
        self.name = name
        self.type = type
        self.value = value


from abc import ABC
from pathlib import Path


__all__ = ["DataProcessor"]


class DataProcessor(ABC):
    def process(self, data):
        return data

    def post_process(self, data_folder: Path):
        pass

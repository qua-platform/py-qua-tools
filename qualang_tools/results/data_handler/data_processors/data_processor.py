from abc import ABC
from pathlib import Path


__all__ = ["DataProcessor"]


class DataProcessor(ABC):
    # Default separator for filename keys in the processed data
    nested_separator: str = "."

    def process(self, data):
        return data

    def post_process(self, data_folder: Path):
        pass

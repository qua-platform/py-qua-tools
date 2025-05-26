from pathlib import Path

from .data_processor import DataProcessor
from .helpers import (
    copy_nested_dict,
    iterate_nested_dict_with_lists,
    update_nested_dict,
)


class PlotlyGraphSaver(DataProcessor):
    file_format: str = "html"
    nested_separator: str = "."

    def __init__(self, file_format=None):
        if file_format is not None:
            self.file_format = file_format
        self.figures = {}

    @property
    def file_suffix(self) -> str:
        suffixes = {"html": ".html", "json": ".json"}
        return suffixes.get(self.file_format.lower(), ".html")

    def process(self, data):
        import plotly.graph_objs as go

        self.figures = {}
        processed_data = copy_nested_dict(data)

        for keys, val in iterate_nested_dict_with_lists(data):
            if not isinstance(val, go.Figure):
                continue

            path = Path(self.nested_separator.join(keys))
            self.figures[path] = val
            update_nested_dict(processed_data, keys, f"./{path}{self.file_suffix}")
        return processed_data

    def post_process(self, data_folder: Path):
        for path, fig in self.figures.items():
            file_path = data_folder / f"{path}{self.file_suffix}"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            if self.file_format.lower() == "html":
                fig.write_html(str(file_path))
            elif self.file_format.lower() == "json":
                fig.write_json(str(file_path))
            else:
                raise NotImplementedError(f"File format {self.file_format} is not supported for Plotly graphs")

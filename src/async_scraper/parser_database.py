import json
import pathlib
from typing import Any, Iterator


class JSONDatabase:
    def __init__(self, path_to_file: str):
        path = pathlib.Path(path_to_file)
        if not path.parent.exists():
            raise ValueError(f"No parent path for {path_to_file} exists")

        self.path_to_file = path_to_file

    def add(self, key: str, value: Any):
        try:
            with open(self.path_to_file, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        data[key] = value
        with open(self.path_to_file, "w") as f:
            json.dump(data, f)

    def get(self, key: str):
        with open(self.path_to_file, "r") as f:
            data = json.load(f)
        return data[key]

    def __iter__(self) -> Iterator[tuple[str, Any]]:
        with open(self.path_to_file, "r") as f:
            data = json.load(f)

        for key, value in data.items():
            yield key, value

import json
import pathlib
from typing import Any, Iterator

from anyio import open_file


class JSONDatabase:
    def __init__(self, path_to_file: str):
        path = pathlib.Path(path_to_file)
        if not path.parent.exists():
            raise ValueError(f"No parent path for {path_to_file} exists")

        self.path_to_file = path_to_file

    async def add(self, key: str, value: Any):
        try:
            async with await open_file(self.path_to_file, "r") as f:
                contents = await f.read()
            data = json.loads(contents)
        except FileNotFoundError:
            data = {}

        data[key] = value
        data_j = json.dumps(data)
        async with await open_file(self.path_to_file, "w") as f:
            await f.write(data_j)

    async def get(self, key: str):
        async with await open_file(self.path_to_file, "r") as f:
            contents = await f.read()
        data = json.loads(contents)
        return data[key]

    # TODO create separate implementations for a sync and async JSONDatabase
    def __iter__(self) -> Iterator[tuple[str, Any]]:
        try:
            with open(self.path_to_file, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        for key, value in data.items():
            yield key, value

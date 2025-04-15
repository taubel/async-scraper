import json
import logging
import pathlib
from typing import Any, Iterator

from anyio import open_file

logger = logging.getLogger(__name__)


class JSONDatabase:
    def __init__(self, path_to_file: str):
        path = pathlib.Path(path_to_file)
        if not path.parent.exists():
            raise ValueError(f"No parent path for {path_to_file} exists")

        self.path_to_file = path_to_file

    async def _read(self) -> dict:
        try:
            async with await open_file(self.path_to_file, "r") as f:
                contents = await f.read()
            data = json.loads(contents)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
            logger.error("Failed to decode json in database file")
            data = None
        return data

    async def add(self, key: str, value: Any):
        data = await self._read()
        if data is None:
            logger.error("Failed to read database")
            return

        data[key] = value
        data_j = json.dumps(data)
        async with await open_file(self.path_to_file, "w") as f:
            await f.write(data_j)

    async def get(self, key: str) -> str | None:
        data = await self._read()
        if data is None:
            logger.error("Failed to read database")
            return None
        return data[key]

    # TODO create separate implementations for a sync and async JSONDatabase
    def __iter__(self) -> Iterator[tuple[str, Any]]:
        try:
            with open(self.path_to_file, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
            logger.error("Failed to decode json in database file")
            return

        for key, value in data.items():
            yield key, value

import json
import logging
import pathlib
from typing import Any, Iterator

from anyio import open_file

from ..interfaces.database import AsyncDatabaseInterface

logger = logging.getLogger(__name__)


# TODO use jsonl
# The JSON Lines format is useful because it’s stream-like, so you can easily append new records to it.
# It doesn’t have the same problem as JSON when you run twice.
# Also, as each record is a separate line, you can process big files without having to fit everything in memory,
# there are tools like JQ to help do that at the command-line.
class AsyncJSONDatabase(AsyncDatabaseInterface):
    def __init__(self, path_to_file: str, lock):
        path = pathlib.Path(path_to_file)
        if not path.parent.exists():
            raise ValueError(f"No parent path for {path_to_file} exists")

        self.path_to_file = path_to_file
        self.lock = lock

    async def _read(self) -> dict | None:
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

    async def _read_safe(self) -> dict | None:
        with self.lock:
            return await self._read()

    async def _add(self, key: str, value: Any):
        data = await self._read()
        if data is None:
            logger.error("Failed to read database")
            return

        data[key] = value
        data_j = json.dumps(data)
        async with await open_file(self.path_to_file, "w") as f:
            await f.write(data_j)

    async def _add_safe(self, key: str, value: Any):
        with self.lock:
            await self._add(key, value)

    async def add(self, url: str, value: Any):
        await self._add(url, value)

    async def get(self, url: str) -> Any:
        data = await self._read_safe()
        if data is None:
            logger.error("Failed to read database")
            return None
        return data[url]

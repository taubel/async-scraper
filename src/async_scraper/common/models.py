from typing import Type

from pydantic import BaseModel

from ..interfaces.parser import ParserInterface


class ParserItemModel(BaseModel):
    parser: Type[ParserInterface]
    contents: str
    url: str

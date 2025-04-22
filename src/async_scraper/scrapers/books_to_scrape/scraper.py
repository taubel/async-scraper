import asyncio
import functools
import logging
import re
from collections.abc import Callable
from typing import Any, Awaitable
from urllib.parse import urlparse

import aiohttp
from pydantic import BaseModel

from .parsers import BookParser, HomeParser, CategoryParser
from ...common.models import ParserItemModel
from ...interfaces import ScraperInterface, ParserInterface

logger = logging.getLogger(__name__)


type ScrapeCallback = Callable[[ParserItemModel], Awaitable[None]]


async def get_page_contents(url: str) -> str:
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.text()


# TODO turn into package
async def add_to_dict(in_dict: dict, key: str, value: Any):
    in_dict[key] = value


# TODO add_to_async_queue and add_to_sync_queue depend on implementation details
#  There should be a wrapper that provides async methods and hides the underlying queue implementation
async def add_to_async_queue(queue: asyncio.Queue[ParserItemModel], item: ParserItemModel):
    await queue.put(item)


async def add_to_sync_queue(queue, item: ParserItemModel):
    queue.put(item)


class Page:
    # TODO make paths an abstract attribute
    paths: list[str] = []

    @classmethod
    def match(cls, url: str) -> bool:
        path = urlparse(url).path
        for path_pattern in cls.paths:
            if re.match(path_pattern, path):
                return True
        return False


class HomePage(Page):
    # https://books.toscrape.com
    # https://books.toscrape.com/
    # https://books.toscrape.com/index.html

    paths: list[str] = [
        r"^$",
        r"^/$",
        r"^index.html$",
        r"^/index.html$",
        r"^/?catalogue/category/books_1/index.html$",
    ]


class CategoryPage(Page):
    # https://books.toscrape.com/catalogue/category/books/travel_2/index.html

    paths: list[str] = [
        r"^/?catalogue/category/books/[A-Za-z0-9-_]+/index.html$",
    ]


class BookPage(Page):
    # https://books.toscrape.com/catalogue/its-only-the-himalayas_981/index.html

    paths: list[str] = [
        r"^/?catalogue/[A-Za-z0-9-_]+/index.html$",
    ]


class PageConfig(BaseModel):
    parser: type[ParserInterface]


class BooksToScrapeScraper(ScraperInterface):
    # https://books.toscrape.com/index.html

    def __init__(self, parser_queue):
        self.parser_queue = parser_queue

        self.pages = {
            HomePage: PageConfig(parser=HomeParser),
            CategoryPage: PageConfig(parser=CategoryParser),
            BookPage: PageConfig(parser=BookParser),
        }

    def _create_scraping_task(self, link: str, callback: Callable) -> asyncio.Task:
        for page, config in self.pages.items():
            if page.match(link):
                task = asyncio.create_task(self.scrape_page(link, callback, config.parser))
                return task
        else:
            raise ValueError(f"No scraper found for link {link}")

    async def scrape(self, url: str):
        callback = functools.partial(add_to_sync_queue, self.parser_queue)

        parsed_url = urlparse(url)
        for page, config in self.pages.items():
            if page.match(parsed_url.path):
                await self.scrape_page(url, callback, config.parser)
                break
        else:
            raise ValueError(f"Url: {url} does not match any defined page")

        logger.debug(f"Finished scraping {url}")

    async def scrape_url(self, url: str) -> str | None:
        logger.debug(f"Scraping url {url}")
        try:
            contents = await get_page_contents(url)
            return contents
        except (aiohttp.ClientResponseError, asyncio.TimeoutError) as e:
            logger.error(f"Failed to get page contents from {url}")
            logger.error(e)
            return None

    async def scrape_page(self, url: str, scrape_callback: ScrapeCallback, parser: type[ParserInterface]):
        contents = await self.scrape_url(url)
        if contents:
            item = ParserItemModel(parser=parser, contents=contents, url=url)
            await scrape_callback(item)

import asyncio
import functools
import logging
import re
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse

import aiohttp

from .parsers import BookParser, HomeParser, CategoryParser
from ...common.models import ParserItemModel
from ...interfaces import ScraperInterface

logger = logging.getLogger(__name__)


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


class BooksToScrapeScraper(ScraperInterface):
    # https://books.toscrape.com/index.html

    def __init__(self, parser_queue):
        self.parser_queue = parser_queue

        self.pages = {
            # TODO typehint scraping callback
            HomePage: {"scraper": self.scrape_home},
            CategoryPage: {"scraper": self.scrape_category},
            BookPage: {"scraper": self.scrape_book},
        }

    def _create_scraping_task(self, link: str, callback: Callable) -> asyncio.Task:
        for page, value in self.pages.items():
            if page.match(link):
                scraper = value["scraper"]
                task = asyncio.create_task(scraper(link, callback))
                return task
        else:
            raise ValueError(f"No scraper found for link {link}")

    async def scrape(self, url: str):
        parsed = {}
        callback = functools.partial(add_to_sync_queue, parsed)

        parsed_url = urlparse(url)
        for page, value in self.pages.items():
            if page.match(parsed_url.path):
                await value["scraper"](url, callback)
                break
        else:
            raise ValueError(f"Url: {url} does not match any defined page")

        logger.debug(f"Finished scraping {url}")

    # TODO typehint callback
    async def scrape_home(self, url: str, scrape_callback: Callable):
        # FIXME define function for getting contents and calling appropriate parser
        try:
            contents = await get_page_contents(url)
        except aiohttp.ClientResponseError as e:
            logger.error(f"Failed to get page contents from {url}")
            logger.error(e)
            return
        except asyncio.TimeoutError as e:
            logger.error(f"Failed to get page contents from {url}")
            logger.error(e)
            return
        item = ParserItemModel(parser=HomeParser, contents=contents, url=url)
        await scrape_callback(item)

    # TODO typehint callback
    async def scrape_category(self, url: str, scrape_callback: Callable):
        logger.debug(f"Scraping category: {url}")
        # FIXME define function for getting contents and calling appropriate parser
        try:
            contents = await get_page_contents(url)
        except aiohttp.ClientResponseError as e:
            logger.error(f"Failed to get page contents from {url}")
            logger.error(e)
            return
        except asyncio.TimeoutError as e:
            logger.error(f"Failed to get page contents from {url}")
            logger.error(e)
            return
        item = ParserItemModel(parser=CategoryParser, contents=contents, url=url)
        await scrape_callback(item)

    # TODO typehint callback
    async def scrape_book(self, url: str, scrape_callback: Callable):
        logger.debug(f"Scraping book: {url}")
        # FIXME define function for getting contents and calling appropriate parser
        try:
            contents = await get_page_contents(url)
        except aiohttp.ClientResponseError as e:
            logger.error(f"Failed to get page contents from {url}")
            logger.error(e)
            return
        except asyncio.TimeoutError as e:
            logger.error(f"Failed to get page contents from {url}")
            logger.error(e)
            return
        item = ParserItemModel(parser=BookParser, contents=contents, url=url)
        await scrape_callback(item)

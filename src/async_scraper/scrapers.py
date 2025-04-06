import asyncio
from abc import ABC, abstractmethod
import functools
import logging
import re
from typing import Callable
from urllib.parse import urlparse, urljoin

import aiohttp
from bs4 import BeautifulSoup


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def get_page_contents(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.text()


def add_to_dict(in_dict, key, value):
    in_dict[key] = value


class ParserInterface(ABC):
    @classmethod
    @abstractmethod
    def parse(cls, contents: str, url: str) -> dict:
        pass


class BookParser(ParserInterface):
    @classmethod
    def parse(cls, contents: str, url: str) -> dict:
        book_soup = BeautifulSoup(contents, "html.parser")
        product_main = book_soup.find("div", class_="col-sm-6 product_main")
        if not product_main:
            logger.debug("No book data found")
            return {}

        name = product_main.h1
        price_str = product_main.find("p", class_="price_color")
        assert price_str, f"{name} does not contain a price (can't be)"
        # TODO define model
        # TODO return tag contents, not the tag itself
        return {"name": name, "price": price_str}


class HomeParser(ParserInterface):
    @classmethod
    def parse(cls, contents: str, url: str) -> dict:
        soup = BeautifulSoup(contents, "html.parser")

        links = []
        for link in soup.find_all("a"):
            href = link.get("href")
            if not href:
                continue
            url_joined = urljoin(url, href)
            links.append(url_joined)

        # Leave only unique links
        links = list(set(links))
        return {
            "links": links,
        }


class CategoryParser(ParserInterface):
    @classmethod
    def parse(cls, contents: str, url: str) -> dict:
        soup = BeautifulSoup(contents, "html.parser")

        links = []
        for link in soup.find_all("a"):
            href = link.get("href")
            if not href:
                continue
            url_joined = urljoin(url, href)
            links.append(url_joined)

        # Leave only unique links
        links = list(set(links))
        return {
            "links": links,
        }


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


class ScraperInterface(ABC):
    @abstractmethod
    def scrape(self, url: str):
        pass


class BooksToScrapeScraper(ScraperInterface):
    # https://books.toscrape.com/index.html

    def __init__(self):
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
        callback = functools.partial(add_to_dict, parsed)

        parsed_url = urlparse(url)
        for page, value in self.pages.items():
            if page.match(parsed_url.path):
                await value["scraper"](url, callback)
                break
        else:
            raise ValueError(f"Url: {url} does not match any defined page")
        print(parsed)

    # TODO typehint callback
    async def scrape_home(self, url: str, parse_callback: Callable):
        try:
            contents = await get_page_contents(url)
        except aiohttp.ClientResponseError as e:
            logger.error(f"Failed to get page contents from {url}")
            logger.error(e)
            return
        parsed = HomeParser.parse(contents, url)
        callback = functools.partial(add_to_dict, parsed)

        tasks = []
        for link in parsed["links"]:
            logger.debug(f"Found link: {link}")
            # Avoid looping the same page
            if HomePage.match(link):
                logger.debug(f"Link matched home page: {link}")
                continue

            try:
                task = self._create_scraping_task(link, callback)
            except ValueError as e:
                logger.error(e)
                continue
            tasks.append(task)

        await asyncio.gather(*tasks)
        parse_callback(url, parsed)

    # TODO typehint callback
    async def scrape_category(self, url: str, parse_callback: Callable):
        logger.debug(f"Scraping category: {url}")
        try:
            contents = await get_page_contents(url)
        except aiohttp.ClientResponseError as e:
            logger.error(f"Failed to get page contents from {url}")
            logger.error(e)
            return
        parsed = CategoryParser.parse(contents, url)
        callback = functools.partial(add_to_dict, parsed)

        tasks = []
        for link in parsed["links"]:
            # FIXME this pattern of defining what pages to skip in all scrapers is error prone
            logger.debug(f"Found link: {link}")
            # Avoid looping the same page
            if HomePage.match(link):
                logger.debug(f"Link matched home page: {link}")
                continue
            # Avoid scraping other categories
            elif CategoryPage.match(link):
                logger.debug(f"Link matched other category page: {link}")
                continue

            try:
                task = self._create_scraping_task(link, callback)
            except ValueError as e:
                logger.error(e)
                continue
            tasks.append(task)

        await asyncio.gather(*tasks)
        parse_callback(url, parsed)

    # TODO typehint callback
    async def scrape_book(self, url: str, parse_callback: Callable):
        logger.debug(f"Scraping book: {url}")
        try:
            contents = await get_page_contents(url)
        except aiohttp.ClientResponseError as e:
            logger.error(f"Failed to get page contents from {url}")
            logger.error(e)
            return
        parsed = BookParser.parse(contents, url)
        parse_callback(url, parsed)


class OxylabsSandboxScraper(ScraperInterface):
    # https://sandbox.oxylabs.io/products
    pass


def create_parser(url: str) -> ScraperInterface:
    if re.match(r"^https?://books.toscrape.com.*$", url):
        return BooksToScrapeScraper()
    elif re.match(r"^https?://sandbox.oxylabs.io/products.*$", url):
        return OxylabsSandboxScraper()
    else:
        raise ValueError(f"No scraper defined for url: {url}")

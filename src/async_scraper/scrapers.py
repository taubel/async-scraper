from abc import ABC, abstractmethod
import logging
import re

import aiohttp
from bs4 import BeautifulSoup


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def get_page_contents(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            # TODO check status
            return await resp.text()


# TODO define parser interface
class BookParser:
    pattern = r"catalogue\/[A-Za-z\-\_0-9]+\/index.html"

    @classmethod
    def match(cls, link: str) -> bool:
        return bool(re.match(cls.pattern, link))

    @classmethod
    def parse(cls, contents: str) -> dict:
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


class ScraperInterface(ABC):
    @abstractmethod
    def scrape(self):
        pass


class BooksToScrapeScraper(ScraperInterface):
    # https://books.toscrape.com/index.html

    def __init__(self, url: str):
        self.url = url

    async def scrape(self):
        contents = await get_page_contents(self.url)
        data = await self.parse(contents)
        print(data)

    async def parse(self, contents: str) -> list[dict]:
        soup = BeautifulSoup(contents, "html.parser")
        data = []
        for link in soup.find_all("a"):
            href = link.get("href")
            if not href:
                continue
            if BookParser.match(href):
                # TODO run concurrently
                contents = await get_page_contents(self.url + href)
                book_data = BookParser.parse(contents)
                data.append(book_data)
            else:
                continue
        return data


class OxylabsSandboxScraper(ScraperInterface):
    # https://sandbox.oxylabs.io/products
    pass


def create_parser(url: str) -> ScraperInterface:
    if re.match(r"^https?://books.toscrape.com.*$", url):
        return BooksToScrapeScraper(url)
    elif re.match(r"^https?://sandbox.oxylabs.io/products.*$", url):
        return OxylabsSandboxScraper(url)
    else:
        raise ValueError(f"No scraper defined for url: {url}")

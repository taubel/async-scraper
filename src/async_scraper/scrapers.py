import asyncio
from abc import ABC, abstractmethod
import logging
import re
from urllib.parse import urlparse, urljoin

import aiohttp
from bs4 import BeautifulSoup


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def get_page_contents(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            # TODO check status
            return await resp.text()


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
            url_parsed = urlparse(url_joined)
            links.append(url_parsed.path)

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
            url_parsed = urlparse(url_joined)
            links.append(url_parsed.path)

        # Leave only unique links
        links = list(set(links))
        return {
            "links": links,
        }


class Page:
    # TODO make paths an abstract attribute
    paths: list[str] = []

    @classmethod
    def match(cls, path: str) -> bool:
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
    ]


class CategoryPage(Page):
    # https://books.toscrape.com/catalogue/category/books/travel_2/index.html

    paths: list[str] = [
        r"^/?catalogue/category/books/.*",
    ]


class BookPage(Page):
    # https://books.toscrape.com/catalogue/its-only-the-himalayas_981/index.html

    paths: list[str] = [
        # TODO this pattern can match a category, need to update it
        r"^/?catalogue/.*",
    ]


class ScraperInterface(ABC):
    @abstractmethod
    def scrape(self):
        pass


class BooksToScrapeScraper(ScraperInterface):
    # https://books.toscrape.com/index.html

    def __init__(self, url: str):
        self.url = url
        self.pages = {
            # TODO typehint scraping callback
            HomePage: {"scraper": self.scrape_home},
            CategoryPage: {"scraper": self.scrape_category},
            BookPage: {"scraper": self.scrape_book},
        }

    async def scrape(self):
        # TODO does url need to be stored in instance?
        parsed_url = urlparse(self.url)
        for page, value in self.pages.items():
            if page.match(parsed_url.path):
                data = await value["scraper"](self.url)
                break
        else:
            raise ValueError(f"Url: {self.url} does not match any defined page")
        print(data)

    async def scrape_home(self, url: str) -> dict:
        contents = await get_page_contents(url)
        parsed = HomeParser.parse(contents, url)
        data = []
        tasks = []
        for link in parsed["links"]:
            logger.debug(f"Found link: {link}")
            # Avoid looping the same page
            if HomePage.match(link):
                logger.debug(f"Link matched home page: {link}")
                continue

            # TODO move this for loop to function to make it reusable
            for page, value in self.pages.items():
                if page.match(link):
                    scraper = value["scraper"]
                    task = asyncio.create_task(scraper(self.url + link))
                    tasks.append(task)
                    # TODO decide how output is collected
                    # data.append(_data)
        await asyncio.gather(*tasks)
        return data

    async def scrape_category(self, url: str) -> dict:
        logger.debug(f"Scraping category: {url}")
        contents = await get_page_contents(url)
        parsed = CategoryParser.parse(contents, url)
        data = []
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

            # TODO move this for loop to function to make it reusable
            for page, value in self.pages.items():
                if page.match(link):
                    scraper = value["scraper"]
                    task = asyncio.create_task(scraper(self.url + link))
                    tasks.append(task)
                    # TODO decide how output is collected
                    # data.append(_data)
        await asyncio.gather(*tasks)
        return data

    async def scrape_book(self, url: str) -> dict:
        logger.debug(f"Scraping book: {url}")
        contents = await get_page_contents(url)
        data = BookParser.parse(contents, url)
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

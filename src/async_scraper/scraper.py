import enum
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


class Scrapeables(enum.Enum):
    category = r"catalogue\/category\/books\/[A-Za-z\-\_0-9]+\/index.html"
    book = r"catalogue\/[A-Za-z\-\_0-9]+\/index.html"


class Scraper:
    def __init__(self, url: str):
        self.url = url

    async def scrape(self, what_to_scrape: Scrapeables):
        contents = await get_page_contents(self.url)
        data = await self.parse(contents, what_to_scrape)
        print(data)

    async def parse(self, contents: str, what_to_scrape: Scrapeables) -> list[dict]:
        soup = BeautifulSoup(contents, "html.parser")
        # TODO should depend on scraper
        books = []
        for link in soup.find_all("a"):
            href = link.get("href")
            if not href:
                continue
            if re.match(what_to_scrape.value, href):
                # TODO run concurrently
                contents = await get_page_contents(self.url + href)
                book_soup = BeautifulSoup(contents, "html.parser")
                product_main = book_soup.find("div", class_="col-sm-6 product_main")
                if product_main:
                    name = product_main.h1
                    price_str = product_main.find("p", class_="price_color")
                    assert price_str, f"{name} does not contain a price (can't be)"
                    books.append(
                        {"name": name, "price": price_str}
                    )
        return books

from urllib.parse import urljoin

from async_scraper.interfaces import ParserInterface
from bs4 import BeautifulSoup
from pydantic import BaseModel


class BasePageModel(BaseModel):
    pass


class BookPageModel(BaseModel):
    name: str
    price: str


class HomePageModel(BaseModel):
    links: list[str]


class CategoryPageModel(BaseModel):
    links: list[str]


class BookParser(ParserInterface):
    @classmethod
    def parse(cls, contents: str, url: str) -> BookPageModel:
        book_soup = BeautifulSoup(contents, "html.parser")
        product_main = book_soup.find("div", class_="col-sm-6 product_main")
        if not product_main:
            raise ValueError(f"No book data found for url {url}")

        name = product_main.h1.contents[0]
        price_tag = product_main.find("p", class_="price_color")
        assert price_tag, f"{name} does not contain a price (can't be)"
        price_str = str(price_tag.contents[0])
        return BookPageModel(name=name, price=price_str)


# TODO define models
class HomeParser(ParserInterface):
    @classmethod
    def parse(cls, contents: str, url: str) -> HomePageModel:
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
        return HomePageModel(links=links)


class CategoryParser(ParserInterface):
    @classmethod
    def parse(cls, contents: str, url: str) -> CategoryPageModel:
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
        return CategoryPageModel(links=links)

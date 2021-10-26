import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup as bs
from marshmallow import Schema, fields
from requests import get

def cache_property(func):
    def cache(self, *args, **kwargs):
        if func.__name__ in self._cache:
            return self._cache[func.__name__]
        hold = func(self, *args, **kwargs)
        self._cache[func.__name__] = hold
        return hold
    return cache

class ProductDetailSchema(Schema):
    description = fields.Str()
    instructions = fields.List(fields.Str)
    ingredients = fields.List(fields.Str)

    class Meta:
        ordered = True


class ProductSchema(Schema):
    link = fields.Str()
    image = fields.Str()
    brand = fields.Str()
    name = fields.Str()
    price = fields.Str()
    rating = fields.Str()
    details = fields.Dict()
    # details = fields.Nested(ProductDetailSchema)

    class Meta:
        ordered = True


class ProductDetails:
    def __init__(self, link):
        self._cache = {}
        self.link = link
        self.schema = ProductDetailSchema()

    def for_json(self):
        return self.schema.dump(self)

    @property
    @cache_property
    def soup(self):
        response = get(self.link)
        return bs(response.text, "lxml")

    @property
    @cache_property
    def details(self):
        if details := self.soup.select_one(
            "div.ProductDetail__productDetails div.ProductDetail__productContent"
        ):
            return details
        return ["No details avaliable"]

    @property
    @cache_property
    def description(self):
        details = self.details
        if details == ["No details avaliable"]:
            return details
        elif details.select_one("p"):
            return str(details.select_one("p").text).strip()
        return str(details.text).strip()

    @property
    @cache_property
    def instructions(self):
        comp = re.compile(r"[\d]\.[\w ]+|[ \w\d,()-]+\.")
        if instructions := self.soup.select_one(
            "div.ProductDetail__howToUse div.ProductDetail__productContent"
        ):
            instructions = comp.findall(str(instructions.text))
            if len(instructions) > 0:
                return instructions
        return ["No instructions provided"]

    @property
    @cache_property
    def ingredients(self):
        if ingredients := self.soup.select_one(
            "div.ProductDetail__ingredients div.ProductDetail__productContent"
        ):
            return [ingred.strip() for ingred in str(ingredients.text).split(",")]
        return ["No ingredients listed"]


class Product:
    base_url = "https://www.ulta.com/"

    def __init__(self, item):
        self.item = item
        self.link = urljoin(self.base_url, item.select_one("a").attrs["href"])
        self.image = str(item.select_one("div.quick-view-prod img").attrs["src"])[:-3]
        self.name = str(item.select_one("p.prod-desc a").text).strip()
        self.schema = ProductSchema()
        self._cache = {}

    @property
    @cache_property
    def brand(self):
        tag = self.item.select_one("h4.prod-title a") or self.item.select_one(
            "h4.prod-title"
        )
        return str(tag.text).strip()

    @property
    @cache_property
    def details(self):
        return ProductDetails(self.link).for_json()

    @property
    @cache_property
    def price(self):
        if tag := self.item.select_one("span.pro-new-price") or self.item.select_one(
            "span.regPrice"
        ):
            return str(tag.text).strip()
        return "No price found"

    @property
    @cache_property
    def rating(self):
        if tag := self.item.select_one("label.sr-only"):
            return str(tag.text)
        return "No rating avaliable"

    def for_json(self):
        return self.schema.dump(self)

from concurrent.futures import ThreadPoolExecutor
from itertools import chain

from requests import get
from marshmallow import Schema, fields
from bs4 import BeautifulSoup as bs

from .products import ProductSchema, Product, cache_property

class SubCategorySchema(Schema):
    name = fields.Str()
    length = fields.Integer(attribute='total')
    products = fields.Nested(ProductSchema, many=True)

    class Meta:
        ordered = True

class SubCatergory:
    def __init__(self, name, link, chunk_size=100):
        self.name = name 
        self.link = link
        self.chunk_size = chunk_size
        self.schema = SubCategorySchema()
        self._cache = {}

    @property
    @cache_property
    def total(self):
        response = get(self.link).text
        soup = bs(response, "lxml")
        return int(soup.select_one("span.search-res-number").text)

    def _generate_product_link(self, offset):
        return self.link + f"&No={offset}&Nrpp={self.chunk_size}"

    def _generate_products(self, link):
        response = get(link).text
        soup = bs(response, "lxml")
        items = soup.select("div.productQvContainer")
        return [Product(i) for i in items]

    @property
    @cache_property
    def products(self):
        links = [self._generate_product_link(offset*self.chunk_size) for offset in range(int(self.total/self.chunk_size) + 1)]
        with ThreadPoolExecutor(len(links)) as pool:
            results = pool.map(self._generate_products, links)
        return list(chain(*results))

    def for_json(self):
        return self.schema.dump(self)

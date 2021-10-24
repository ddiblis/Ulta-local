from urllib.parse import urljoin
from marshmallow import Schema, fields


class ProductSchema(Schema):
    link = fields.Str()
    image = fields.Str()
    brand = fields.Str()
    name = fields.Str()
    price = fields.Str()
    rating = fields.Str()


class Product:
    base_url = "https://www.ulta.com/"

    def __init__(self, item):
        self.item = item
        self.link = urljoin(self.base_url, item.select_one("a").attrs["href"])
        self.image = item.select_one("div.quick-view-prod img").attrs["src"][:-3]
        self.name = item.select_one("p.prod-desc a").text.strip()
        self.schema = ProductSchema()

    @property
    def brand(self):
        tag = self.item.select_one("h4.prod-title a") or self.item.select_one(
            "h4.prod-title"
        )
        return tag.text.strip()

    @property
    def price(self):
        tag = self.item.select_one("span.pro-new-price") or self.item.select_one(
            "span.regPrice"
        )
        return tag.text.strip() if tag else "No price found"

    @property
    def rating(self):
        tag = self.item.select_one("label.sr-only")
        return tag.text if tag else "No rating avaliable"

    def for_json(self):
        return self.schema.dump(self)

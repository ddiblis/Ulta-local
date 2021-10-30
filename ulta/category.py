from marshmallow import Schema, fields
from requests import get

import re
from ulta.products import cache_property

from ulta.subCategory import SubCatergory, SubCategorySchema


class CategorySchema(Schema):
    name = fields.Str()
    links = fields.List(fields.Str)
    subcategories = fields.Nested(SubCategorySchema, many=True)

    class Meta:
        ordered = True


class Category:
    def __init__(self, link):
        self.link = link
        self.schema = CategorySchema()
        self._cache = {}

    @property
    @cache_property
    def links(self):
        resp = get(self.link).text
        if "gifts" in self.link:
            return re.findall(r"f=\"([\S\.]+/gifts[\S]+)\"", resp)[1:-1]
        else:
            return re.findall(r"\"(https://[\S]+m/[\w\d?=&;%=-]+)\"", resp)[:-1]

    @property
    @cache_property
    def subcategories(self):
        name_reg = r"m\/([\S]+)\?"
        return [SubCatergory(re.findall(name_reg, r)[0], r) for r in self.links]

    def for_json(self):
        return self.schema.dump(self)

    @property
    @cache_property
    def name(self):
        return self.link.split('/')[-1]

    @property
    def total(self):
        return sum([i.total for i in self.subcategories])    
from marshmallow import Schema, fields
from requests import get

import re
from codecs import decode

from ulta.category import Category, CategorySchema
from ulta.products import cache_property


class SiteSchema(Schema):
  name = fields.Str()
  links = fields.List(fields.Str)
  categories = fields.Nested(CategorySchema, many=True)

  class Meta:
    ordered = True

class Site:
  def __init__(self, link):
    self.link = link
    self.schema = SiteSchema()
    self._cache = {}

  @property
  @cache_property
  def links(self):
    response = get(self.link).text
    regex = re.findall(r'L":"([\S]+)","f', response)
    raw = [decode(i, "unicode-escape") for i in regex]
    return list(set(r for r in raw if "brand" not in r))

  @property
  @cache_property
  def categories(self):
    return [Category(l) for l in self.links]
  
  @property
  def name(self):
    return str(self.link.split(".")[1])

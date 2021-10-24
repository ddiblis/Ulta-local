from concurrent.futures import ThreadPoolExecutor
from itertools import chain

from marshmallow import Schema, fields
from products import ProductSchema, Product


class SubCategoriesSchema(Schema):
  name = fields.Str()
  products = fields.Nested(ProductSchema)

class SubCatergories:

  def __init__(self, name, chunk_size=100):
    self.name = name
    self.chunk_size = chunk_size
    self.schema = SubCategoriesSchema()

  @property
  def link(self):
      """ Put logic to create link here"""
      pass

  @property
  def _total(self):
      """ Put logic for first fetch to get total here"""
      pass

  def _generate_product_link(self, offset):
          """ Product link generation logic 
              example: self.link + #Whatever...
          """
  def _generate_products(self, index):
      """ Put logic to generate final link and return products

      ########### EXAMPLE  #############
          link = #your link logic
          resp = requests.get(link)
          soup = bs4(resp.text, 'lxml')
          items = #your item parse logic
          return [Product(i) for i in items]
      """
      pass

  @property
  def products(self):
      """ Product generation logic

      ########### Example ###########
      # You'll have to change Product to just accept a link, not base/offset
          links = [self._generate_product_link(offset)
              for offset in range(self._total/self.chunk_size)
          ]
          with ThreadPoolExecutor(len(links)) as pool:
              results = pool.map(self._generate_products, links)
          return list(chain(*results))
      """
      pass

  def for_json(self):
      return self.schema.dump(self)


from concurrent.futures import ThreadPoolExecutor
import re
import time
from itertools import repeat, chain

import simplejson as json
import requests
from tqdm import tqdm
from requests import get
from bs4 import BeautifulSoup as bs
import os
if not os.environ.get('LOGURU_LEVEL', None):
  os.environ['LOGURU_LEVEL'] = 'INFO'
from loguru import logger

from .products import Product

# Gets categories from main page
def get_cats():
  categories = {}

  resp = get("https://www.ulta.com/").text
  reg = re.findall(r'L":"[\S]+","f', resp)
  raw = [i[4:-4] for i in reg]
  lst = list(set(re.sub(r"\\u002F", "/", r) for r in raw))
  lst.remove("https://www.ulta.com/brand/ulta")

  return lst

# Gets sub categories for each category
def get_subcats():
  prods = {}
  
  for i in get_cats():
    if "gifts" in i:
      resp = get(i).text
      reg = re.findall(r'f=\"[\S\.]+/gifts[\S]+\"', resp)
      raw = [i[3:-1] for i in reg][1:-1]
      prods[i[26:]] = raw
    resp = get(i).text
    reg = re.findall(r'\"https://[\S]+m/[\w\d?=&;%=-]+\"', resp)
    raw = [i[1:-1] for i in reg][:-1]
    prods[i[26:]] = raw
  return prods

# Get products info
def get_prods():
  subs = get_subcats()
  data = {}
  progress = tqdm()

  def run_chunk(n, s):
      link = s + f"&No={n*100}&Nrpp=100"
      resp = get(link).text
      soup = bs(resp, "html.parser")
      items = soup.select("div.productQvContainer")
      return [Product(i) for i in items]

  for s in chain(*subs.values()):
      key = re.findall(r"m\/[\S]+\?", s)[0][2:-1]
      with ThreadPoolExecutor(30) as pool:
        arrs = pool.map(run_chunk, range(30), repeat(s))
      output = []
      for i in chain(*arrs):
        if i not in output:
          output.append(i)
      progress.update(len(output))
      data[key] = output
  return data


def pull_details(value, soup):
  details = soup.select("div.ProductDetail__productDetails div.ProductDetail__productContent")[0] if soup.select("div.ProductDetail__productDetails div.ProductDetail__productContent") else "No details avaliable"
  description = details if details == "No details avaliable" else str(details.select_one("p").text).strip() if details.select_one("p") else str(details.text).strip()
  instructions = str(soup.select("div.ProductDetail__howToUse div.ProductDetail__productContent")[0].text) if soup.select("div.ProductDetail__howToUse div.ProductDetail__productContent") else "No instructions provided"
  instructions_split = re.findall(r"[\d]\.[\w ]+|[ \w\d,()-]+\.", instructions) if len(re.findall(r"[\d]\.[\w ]+|[ \w\d,()-]+\.", instructions)) > 0 else instructions
  ingredients = [i.strip() for i in str(soup.select("div.ProductDetail__ingredients div.ProductDetail__productContent")[0].text).split(",")] if soup.select("div.ProductDetail__ingredients div.ProductDetail__productContent") else "No ingredients listed"
  value.update({'description': str(description),
          'ingredients': ingredients,
          'instructions': instructions_split,})
  return value

def pull(key, value):
    logger.debug(key + " " + value["link"])
    try:
      resp = requests.get(value["link"]).text
      soup = bs(resp, "lxml")
    except requests.exceptions.ConnectionError:
      print(f"#################ERROR IS HERE {value['link']}")
    details = pull_details(value, soup, resp)
    return details

def gen_output(data):
  for key, values in data.items():
    with ThreadPoolExecutor(5) as pool:
      products = pool.map(pull, repeat(key), values)
    yield dict(name=key, products=products)

def get_details():
  data = json.load(open('./data.json'))
  with open('test.json', 'w') as outfile:
    json.dump(gen_output(data), outfile, ensure_ascii=False, indent=4, iterable_as_array=True)

def save_json():
  t0 = time.time()
  with open('data.json', 'w') as outfile:
    json.dump(get_prods(), outfile, indent=4, ensure_ascii=False, for_json=True)
  t1 = time.time()
  print(t1 - t0)

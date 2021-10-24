#!/usr/bin/env python
from concurrent.futures.thread import ThreadPoolExecutor
import re
import time
from itertools import repeat, chain

import simplejson as json
from tqdm import tqdm
from requests import get
from bs4 import BeautifulSoup as bs

from products import Product

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

def get_details():
  single_item = {}
  full = {}
  with open('./data.json') as f:
    data = json.load(f)
    single_item = data["nail-polish"]
  for s in single_item:
    print(s["link"])
    resp = get(s["link"]).text
    soup = bs(resp, "html.parser")
    details = soup.select("div.ProductDetail__productDetails div.ProductDetail__productContent")[0]
    description = details.select_one("p").text.strip() if details.select_one("p") else details.text.strip()
    instructions = soup.select("div.ProductDetail__howToUse div.ProductDetail__productContent")[0].text if soup.select("div.ProductDetail__howToUse div.ProductDetail__productContent") else "No instructions provided"
    instructions_split = re.findall(r"[\d]\.[\w ]+", instructions) if len(re.findall(r"[\d]\.[\w ]+", instructions)) > 0 else instructions
    ingredients = [i.strip() for i in soup.select("div.ProductDetail__ingredients div.ProductDetail__productContent")[0].text.split(",")] if soup.select("div.ProductDetail__ingredients div.ProductDetail__productContent") else "No ingredients listed"
    s.update({'description': description,
            'ingredients': ingredients,
            'instructions': instructions_split,})
    full.update({s["link"]: s})

    reg = re.findall(r"[\w ]+ <br>", resp)
    titles = [i.strip()[:-4] for i in reg]
    features = details.select("ul")
    for i in range(len(features)):
      s.update({titles[i] if reg else "Features": [r.text for r in features[i].select("li")]})

  with open('test.json', 'w') as outfile:
    json.dump(full, outfile, ensure_ascii=False, indent=4)

def save_json():
  t0 = time.time()
  with open('data.json', 'w') as outfile:
    json.dump(get_prods(), outfile, indent=4, ensure_ascii=False, for_json=True)
  t1 = time.time()
  print(t1 - t0)


get_details()
# save_json()
# print(get_cats())
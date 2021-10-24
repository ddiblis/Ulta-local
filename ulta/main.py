#!/usr/bin/env python
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from urllib.parse import urljoin
# import json
import re
import time
from itertools import repeat, chain

import simplejson as json
from tqdm import tqdm
from requests import get
from bs4 import BeautifulSoup as bs

from sub import Product

# Gets categories from main page
def get_cats():
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


def save_json():
  t0 = time.time()
  with open('data.json', 'w') as outfile:
    json.dump(get_prods(), outfile, indent=4, ensure_ascii=False, for_json=True)
  t1 = time.time()
  print(t1 - t0)

save_json()
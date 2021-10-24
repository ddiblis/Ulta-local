from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from urllib.parse import urljoin
import json
import re
import time
from itertools import repeat

from tqdm import tqdm
from requests import get
from bs4 import BeautifulSoup as bs

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

def push_prod(item, link):
  base_url = "https://www.ulta.com/"

  for retry in range(5):
    rating = item.select_one("label.sr-only") or ""
    price = item.select_one("span.regPrice") or item.select_one("span.pro-new-price")
    brand = item.select_one("h4.prod-title") or item.select_one("h4.prod-title a")
    ratingif = rating.text if rating else "No rating avaliable"
    priceif = price.text.strip() if price else "No price found"
    nameif = item.select_one("p.prod-desc a").text.strip() if item.select_one("p.prod-desc a") else ""
    brandif = brand.text.strip() if brand else ""
    imgif = item.select_one("div.quick-view-prod img").attrs["src"][:-3] if item.select_one("div.quick-view-prod img") else ""
    urlif = urljoin(base_url, item.select_one("a").attrs["href"]) if item.select_one("a") else ""
    if not imgif:
      print(item.select_one("div.quick-view-prod img"))
      print(link)
      # with open('wtf.html') as f_:
      #   f_.write(item.html())
    if imgif and brandif and nameif:
      break
  return {
            "parent-link": link,
            "link": urlif,
            "image": imgif,
            "brand": brandif,
            "name": nameif,
            "price": priceif,
            "rating": ratingif,
          }

def get_prods():
  subs = get_subcats()
  data = {}
  progress = tqdm()

  for subcat in subs:
      for s in subs[subcat]:
          key = ""
          arr = []
          for n in range(15):
              link = s + f"&No={n}000&Nrpp=200"
              key = re.findall(r"m\/[\S]+\?", link)[0][2:-1]
              resp = get(link).text
              soup = bs(resp, "html.parser")
              items = soup.select("div.productQvContainer")
              with ThreadPoolExecutor(30) as pool:
                  nref = list(pool.map(push_prod, items, repeat(link)))
                  progress.update(len(nref))
                  arr.extend(nref)
              # for item in items:
              #   arr.append(push_prod(item, link))
          data[key] = arr
  return data


def save_json():
  t0 = time.time()
  with open('data.json', 'w') as outfile:
    json.dump(get_prods(), outfile, indent=4, ensure_ascii=False)
  t1 = time.time()
  print(t1 - t0)

save_json()
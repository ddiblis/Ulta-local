from concurrent.futures import ThreadPoolExecutor
import re
import time
from itertools import repeat, chain

import simplejson as json
from tqdm import tqdm
from requests import get
from bs4 import BeautifulSoup as bs
import os


if not os.environ.get("LOGURU_LEVEL", None):
    os.environ["LOGURU_LEVEL"] = "INFO"
from loguru import logger

from .categories import Categories
from .subCategories import SubCatergories
from .products import Product

# Gets categories from main page
def get_categories():
    cats = Categories("https://www.ulta.com/")
    return cats.for_json()

# Gets sub categories for each category
def get_subcats():
    prods = {}

    for i in get_categories()["link_list"]:
        if "gifts" in i:
            resp = get(i).text
            reg = re.findall(r"f=\"[\S\.]+/gifts[\S]+\"", resp)
            raw = [i[3:-1] for i in reg][1:-1]
            prods[i[26:]] = raw
        resp = get(i).text
        reg = re.findall(r"\"https://[\S]+m/[\w\d?=&;%=-]+\"", resp)
        raw = [i[1:-1] for i in reg][:-1]
        prods[i[26:]] = raw
    return prods

def run_chunk(n, s):
    link = s + f"&No={n*25}&Nrpp=25"
    resp = get(link).text
    soup = bs(resp, "lxml")
    items = soup.select("div.productQvContainer")
    results = [Product(i) for i in items]
    for d in results:
        d.details
    return results

# Get products info
def get_prods():
    subs = get_subcats()
    progress = tqdm()

    for s in chain(*subs.values()):
        key = re.findall(r"m\/[\S]+\?", s)[0][2:-1]
        with ThreadPoolExecutor(10) as pool:
            arrs = pool.map(run_chunk, range(120), repeat(s))
        output = []
        dup_check = []
        for i in chain(*arrs):
            if i.link not in dup_check:
                dup_check.append(i.link)
                output.append(i)
        progress.update(len(output))
        yield dict(name=key, products=output)

def save_json():
    t0 = time.time()
    with open("data.json", "w") as outfile:
        json.dump(get_prods(), outfile, indent=4, ensure_ascii=False, for_json=True, iterable_as_array=True)
    t1 = time.time()
    print(t1 - t0)



def test():
    t0 = time.time()
    test = Categories("https://www.ulta.com/").subcategories
    with open("test.json", "w") as outfile:
        json.dump(test.for_json(), outfile, indent=4, ensure_ascii=False, for_json=True, iterable_as_array=True)
    t1 = time.time()
    print(t1 - t0)
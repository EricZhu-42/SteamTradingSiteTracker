import re
import time
import urllib

import numpy as np
import requests
from bs4 import BeautifulSoup
from loguru import logger
from retrying import retry

from database import MongoDB
from url_formats import (buff_index_json_fmt, c5_search_page_fmt,
                         igxe_search_page_fmt, steam_item_page_fmt,
                         uuyp_search_page_fmt)
from utils import asian_proxies, default_header, random_delay

logger.add('../log/update_meta.log', enqueue=True, rotation='1 MB', backtrace=True, diagnose=True)

# ==== configs ====
META_EXPIRE_TIME = 14 * 24 * 60 * 60

# ==== init ====

# load buff_cookie
with open('./secrets/buff_cookie.txt', 'r', encoding='utf-8') as f:
    buff_cookie = f.read().strip()
    assert 'session' in buff_cookie

# load c5 cookie
with open('./secrets/c5_cookie.txt', 'r', encoding='utf-8') as f:
    c5_cookie = f.read().strip()
    assert 'C5Login' in c5_cookie

# load UUYP cookie
with open("./secrets/uuyp_cookie.txt", "r", encoding="utf-8") as f:
    uuyp_cookie = f.read().strip()
    assert "Bearer" in uuyp_cookie

headers = default_header.copy()
headers['Cookie'] = buff_cookie + ';' + c5_cookie
headers['authorization'] = uuyp_cookie

game_info = [
    {'game': 'csgo',  'appid':730},
    {'game': 'dota2', 'appid':570},
]

# ==== update a single entry ====

@retry(stop_max_attempt_number=2, wait_fixed=10000)
def get_buff_index(page_num:int, game:str):
    r = requests.get(buff_index_json_fmt.format(page_num=page_num, game=game), headers=headers, timeout=20)
    assert r.status_code == 200, "Falied to fetch buff index with code: " + str(r.status_code)

    assert r.json()['code'] == 'OK', str(r.json())

    return r.json()['data']['items']

@retry(stop_max_attempt_number=2, wait_fixed=10000)
def get_uuyp_id(name:str):
    data = {
        "gameId": '730',
        'keyWords': name,
        'listSortType': '1',
        'listType': '10',
        'pageIndex': 1,
        'pageSize': 20,
        'sortType': 0,
    }
    r = requests.post(uuyp_search_page_fmt, headers=headers, json=data, timeout=20)
    assert r.status_code == 200, "Falied to get uuyp id of " + name + " with code: " + str(r.status_code)

    assert r.json()['Code'] == 0, str(r.json())

    if r.json()['Data'] is None:
        logger.warning("Did not find item {} in UUYP", name)
        return 0

    for item in r.json()['Data']:
        if item['CommodityName'].strip() == name.strip():
            logger.success("Update UUYP id {} for item {}", item['Id'], name)
            return item['Id']
    
    logger.warning("Did not find UUYP id for item {}, candidates: {}", name, [item['CommodityName'].strip() for item in r.json()['Data']])
    return 0


@retry(stop_max_attempt_number=2, wait_fixed=20000)
def get_market_id(hash_name:str, appid:int):
    r = requests.get(steam_item_page_fmt.format(hash_name=urllib.parse.quote(hash_name), appid=appid), headers=headers, timeout=30)
    assert r.status_code == 200, "Falied to get market id of " + hash_name + " with code: " + str(r.status_code)

    try:
        market_id = eval(re.search(r'Market_LoadOrderSpread\((.*?)\);', r.text).group(1).strip())
    except Exception as e:
        logger.warning("Failed to find market id for item {} in app {} for {}", hash_name, appid, e)
        market_id = 0

    return market_id

@retry(stop_max_attempt_number=2, wait_fixed=10000)
def get_igxe_id(game:str, name:str):
    r = requests.get(igxe_search_page_fmt.format(game=game, name=urllib.parse.quote(name)), headers=headers, timeout=30)
    assert r.status_code == 200, "Falied to get igxe id of " + name + " with code: " + str(r.status_code)

    # parse html
    soup = BeautifulSoup(r.text, 'html.parser')
    data_list = soup.find_all(class_='list list')
    assert len(data_list) == 1, "unmatched data list"

    candidates = [a for a in data_list[0].find_all("a") if a.find(class_='name').text == name]

    if len(candidates) == 1:
        # the correct one
        a = candidates[0]
        return eval(re.search(r'/product/\d+/(\d+)', a.attrs['href']).group(1))
    else:
        # 0 or >1 candidates; stop
        logger.warning("Find invalid igxe name in {} ({} candidates)", r.url, len(candidates))
        return 0

@retry(stop_max_attempt_number=2, wait_fixed=2000)
def get_c5_id(game:str, name:str):

    r = requests.get(c5_search_page_fmt.format(name=name, game=game), timeout=20)
    assert r.status_code == 200, "Falied to get c5 id of " + name + " with code: " + str(r.status_code)

    c5_id = 0
    
    # prase html
    soup = BeautifulSoup(r.text, 'html.parser')
    for div in soup.findAll('div', class_='el-col el-col-4'):
        div_name = div.find(class_='ellipsis pointer li-btm-title mb10').text.strip()
        if div_name == name:
            c5_id = int(re.search('/(\d+)/', div.a['href']).group(1))
            break

    if not c5_id:
        logger.warning('Find invalid c5 id in {}', r.url)

    return c5_id

# ==== update an item ====

def update_once(game:str, appid:int, page_num:int):
    logger.info("Fetch game {} at page num {}", game, page_num)
    items = get_buff_index(page_num, game)

    for item in items:
        quick_price = eval(item.get('quick_price', '0'))
        sell_min_price = eval(item.get('sell_min_price', '0'))
        buy_max_price = eval(item.get('buy_max_price', '0'))
        sell_num = item.get('sell_num', '0')

        # filt item

        if (quick_price < 1) or (quick_price < 10 and sell_num < 80):
            continue

        if buy_max_price:
            buff_ratio = (sell_min_price / buy_max_price)
        else:
            buff_ratio = 999

        if buff_ratio > 1.64:
            continue

        # get market id
        buff_id = item['id']
        name = item['name']
        hash_name = item['market_hash_name']
        short_name = item['short_name']

        market_id = get_market_id(hash_name=hash_name, appid=appid)
        if market_id == 0:
            continue

        # get igxe id
        try:
            igxe_id = get_igxe_id(game=game, name=name)
        except Exception as e:
            logger.warning("Unable to find igxe id for item {}", name)
            igxe_id = 0

        # get c5 id
        try:
            c5_id = get_c5_id(game=game, name=name)
        except Exception as e:
            logger.warning("Unable to find c5 id for item {} {}", name, e)
            c5_id = 0
        
        uuyp_id = 0
        if game == 'csgo':
            try:
                uuyp_id = get_uuyp_id(name=name)
            except Exception as e:
                logger.warning("Unable to find UUYP id for item {} {}", name, e)

        # parse item
        item = {
            'buff_id' : buff_id,
            'igxe_id' : igxe_id,
            'c5_id' : c5_id,
            'market_id' : market_id,
            'uuyp_id': uuyp_id,
            'hash_name' : hash_name,
            'short_name': short_name,
            'buff_ratio': buff_ratio,
            'buff_reference_price' : eval(item['sell_reference_price']),
            'buff_buy_num' : item['buy_num'],
            'buff_sell_num' : item['sell_num'],
            'name' : item['name'],
            'created_at' : int(time.time()),
            'appid' : appid,
            'game' : game,
        }

        # save item
        storage = MongoDB("meta")
        if storage.get_item(buff_id):
            assert storage.update_item(item)
            logger.info("Updated item {:s} with ratio {:.2f}", hash_name, buff_ratio)
        else:
            assert storage.insert_item(item)
            logger.info("Insert item {:s} with ratio {:.2f}", hash_name, buff_ratio)
        storage.close()

        random_delay()


# ==== main ====
if __name__ == '__main__':
    logger.info("Start to fetch metadata ...")
    while True:
        to_update_list = []
        for info in game_info:
            INITIAL_PAGE_URL = buff_index_json_fmt.format(game=info['game'], page_num=9999)
            page_data = requests.get(INITIAL_PAGE_URL, headers=headers).json()['data']

            page_count = page_data['total_page']
            item_count = page_data['total_count']
            logger.info('Game {:s}: {:d} items in {:d} pages', info['game'], item_count, page_count)

            for page_num in range(1, page_count+1):
                to_update_list.append({'page_num':page_num, **info})

            random_delay()

        # shuffle the list to update meta randomly
        np.random.shuffle(to_update_list)
        logger.info("Updating {:d} pages ... ", len(to_update_list))

        for update in to_update_list:
            try:
                update_once(**update)
            except Exception as e:
                logger.exception("Update failed for page {}", update)
                random_delay(300, 360)

        # delete old items
        storage = MongoDB("meta")
        for buff_id in storage.get_valid_item_ids():
            if storage.get_item(buff_id)['created_at'] + META_EXPIRE_TIME < time.time():
                storage.delete_item(buff_id)
        storage.close()

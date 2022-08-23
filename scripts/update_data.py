import locale
import multiprocessing
import time
import urllib
from math import floor

import numpy as np
import requests
from loguru import logger
from retrying import retry

from database import MongoDB
from url_formats import (buff_json_fmt, c5_json_fmt, igxe_json_fmt,
                         order_json_fmt, volume_json_fmt)
from utils import asian_proxies, default_header, global_proxies, random_delay, calculate_after_fee

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8' )
logger.add('../log/update_data.log', enqueue=True, rotation='2 MB', backtrace=True, diagnose=True)

# ==== config ====
PROCESS_NUM = 15
MIN_INTERVAL_PER_PROCESS = 3

RESTART_INTERVAL =  40 * 60
SPEEDRUN_INTERVAL = 40 * 60
SPEEDRUN_UPDATE_NUM = 600

# ==== init ====
headers = default_header.copy()
platforms = ['buff', 'igxe', 'c5']

# ==== utils ====
def parse_ratio(buy, sell_raw):
    return sell_raw*0.85, buy/(sell_raw*0.85)

def parse_igxe_delivery_time(time_str:str):
    if time_str == '-':
        return None
    time_str = time_str.replace('小时', ' ').replace('分', '')
    h, m = time_str.split(' ')
    return eval(h) * 3600 + eval(m) * 60

def parse_igxe_delivery_rate(rate_str:str):
    if rate_str == '-':
        return None
    return eval(rate_str.replace('%', '')) / 100.0

# ==== update a single entry ====

@retry(stop_max_attempt_number=2, wait_fixed=500)
def get_volume_data(hash_name, appid):
    """
        always use proxy
        traffic: 0.5 KB
    """
    r = requests.get(volume_json_fmt.format(hash_name=urllib.parse.quote(hash_name), appid=appid), proxies=global_proxies)
    assert r.status_code == 200, "Failed to get item with hash_name @ 1: " + str(hash_name) + " with code: " + str(r.status_code)

    volume_data = r.json()
    assert volume_data['success'], "Failed to get item with hash_name @ 2: " + str(hash_name)

    return volume_data

@retry(stop_max_attempt_number=2, wait_fixed=500)
def get_order_data(market_id):
    """
        always use proxy
        traffic: 2.75 KB
    """
    r = requests.get(order_json_fmt.format(market_id=market_id), proxies=asian_proxies)
    assert r.status_code == 200, "Failed to get item with market_id @ 1: " + str(market_id) + " with code: " + str(r.status_code)

    volume_data = r.json()
    assert volume_data['success'], "Failed to get item with market_id @ 2: " + str(market_id)

    return volume_data

@retry(stop_max_attempt_number=2, wait_random_min=5000, wait_random_max=10000)
def get_buff_data(buff_id, game, use_proxy=False):
    """
        traffic: 27.4 KB
    """
    proxies = None
    if use_proxy:
        proxies = asian_proxies

    r = requests.get(buff_json_fmt.format(buff_id=buff_id, game=game), proxies=proxies)
    assert r.status_code == 200, "Failed to get item with buff_id @ 1: " + str(buff_id) + " with code: " + str(r.status_code)

    buff_data = r.json()
    assert buff_data['code'] == 'OK', "Failed to get item with buff_id @ 2: " + str(buff_id)

    return buff_data

@retry(stop_max_attempt_number=2, wait_random_min=5000, wait_random_max=10000)
def get_igxe_data(igxe_id:int, appid, use_proxy=False):
    """
        traffic: 13.1 KB
    """
    proxies = None
    if use_proxy:
        proxies = asian_proxies

    r = requests.get(igxe_json_fmt.format(igxe_id=igxe_id, appid=appid), timeout=10, proxies=proxies)
    if r.status_code == 404: 
        return None
    assert r.status_code == 200, "Failed to get item with igxe_id @ 1: " + str(igxe_id) + " with code: " + str(r.status_code)

    igxe_data = r.json()
    assert igxe_data['succ'], "Failed to get item with igxe_id @ 2: " + str(igxe_id)

    return igxe_data

# @retry(stop_max_attempt_number=2, wait_random_min=10000, wait_random_max=10000)
def get_c5_data(c5_id:int, use_proxy=False):
    """
        traffic: 27 KB
    """
    proxies = None
    if use_proxy:
        proxies = asian_proxies

    r = requests.get(c5_json_fmt.format(c5_id=c5_id), headers=headers, timeout=10, proxies=proxies)
    assert r.status_code == 200, "Failed to get item with c5_id @ 1: " + str(c5_id) + " with code: " + str(r.status_code)

    c5_data = r.json()
    assert c5_data['success'], "Failed to get item with c5_id @ 2: " + str(c5_id)

    return c5_data


# ==== update an item ====
def update_item(item:dict, group:int=-1, use_proxy:bool=False):
    """
        total traffic: about 70 KB
    """
    start = time.time()

    buff_id = item['buff_id']
    igxe_id = item['igxe_id']
    c5_id = item['c5_id']
    market_id = item['market_id']
    hash_name = item['hash_name']
    game = item['game']
    appid = item['appid']
    quick_price = item['buff_reference_price']
    age = time.time() - item.get('updated_at', 0)

    # update steam trade volume
    volume_data = get_volume_data(hash_name, appid)
    item['count_in_24'] = locale.atoi(volume_data.get('volume', "0"))

    proc_storage = MongoDB('data')

    # ignore items with too low volume
    if item['count_in_24'] < 2:
        item['weighted_ratio'] = 100 # assign lowest update priority
        item['updated_at'] = int(time.time())
        proc_storage.update_item(item)
        proc_storage.close()
        logger.info("ignore item {:s} for low volume with age {:.2f} hours", hash_name, age / 3600)
        return

    # update buff order
    buff_data = get_buff_data(buff_id, game, use_proxy)
    item['buff_sell_list'] = [(eval(order['price']), order['recent_average_duration'], order['recent_deliver_rate']) for order in buff_data['data']['items']]

    # update steam order
    order_data = get_order_data(market_id)
    item['buy_order_list'] = list(tuple(order[:2]) for order in order_data['buy_order_graph'][:10])
    item['sell_order_list'] = list(tuple(order[:2]) for order in order_data['sell_order_graph'][:10])

    # update igxe order; igxe page not exist if igxe_id == 0
    item['igxe_sell_list'] = []
    if igxe_id:
        igxe_data = get_igxe_data(igxe_id, appid, use_proxy)
        if igxe_data:
            item['igxe_sell_list'] = [(eval(order['unit_price']), parse_igxe_delivery_time(order.get('delivery_rank_avg_time', '-')), parse_igxe_delivery_rate(order.get('delivery_send_rate', '-'))) for order in igxe_data['d_list']]

    # update c5 order; c5 page not exist if c5_id == 0
    item['c5_sell_list'] = []
    if c5_id:
        c5_data = get_c5_data(c5_id, use_proxy)
        if c5_data:
            item['c5_sell_list'] = [(eval(order['price']), None, None) for order in c5_data['data']['list']]

    # compute ratio for each platform
    if len(item['buff_sell_list']) and len(item['buy_order_list']) and len(item['sell_order_list']):

        # parse platforms
        for platform in platforms:
            if len(item['{p}_sell_list'.format(p=platform)]):
                if quick_price > 8:
                    # for items with higer price, optimal := 1-st min, safe := 3-rd min
                    item['{p}_optimal_price'.format(p=platform)] = item['{p}_sell_list'.format(p=platform)][0][0]
                    safe_index = np.argmin([t[1] if t[1] else 9999 for t in item['{p}_sell_list'.format(p=platform)][:3]])
                    item['{p}_safe_price'.format(p=platform)] = item['{p}_sell_list'.format(p=platform)][safe_index][0]
                else:
                    # for items with lower price, optimal := avg of top-10 min, safe := optimal
                    item['{p}_optimal_price'.format(p=platform)] = np.mean([t[0] for t in item['{p}_sell_list'.format(p=platform)][:10]])
                    item['{p}_safe_price'.format(p=platform)] = item['{p}_optimal_price'.format(p=platform)]
            else:
                # missing sell list
                item['{p}_optimal_price'.format(p=platform)] = 9999999
                item['{p}_safe_price'.format(p=platform)] = 9999999

        # parse steam
        safe_buy_list = [price for price, num in item['buy_order_list'] if num >= 3]
        safe_buy_price_raw = safe_buy_list[0] if len(safe_buy_list) else item['buy_order_list'][-1][0]
        optimal_buy_price_raw = item['buy_order_list'][0][0]
        optimal_sell_price_raw = item['sell_order_list'][0][0]

        item['optimal_buy_price'] = calculate_after_fee(optimal_buy_price_raw)
        item['safe_buy_price'] = calculate_after_fee(safe_buy_price_raw)
        item['optimal_sell_price'] = calculate_after_fee(optimal_sell_price_raw)
        item['safe_sell_price'] = item['optimal_sell_price'] # just a placeholder; sell should not be safe

        # compute ratio
        for safe in ['optimal', 'safe']:
            for mode in ['buy', 'sell']:
                for platform in platforms:
                    item['{p}_{s}_{m}_ratio'.format(p=platform, s=safe, m=mode)] = item['{p}_{s}_price'.format(p=platform, s=safe)] / item['{s}_{m}_price'.format(s=safe, m=mode)]

        optimal_buy_ratio = min(item['{p}_optimal_buy_ratio'.format(p=platform)] for platform in platforms)
        optimal_sell_ratio = min(item['{p}_optimal_sell_ratio'.format(p=platform)] for platform in platforms)

        # assign update priority
        item['weighted_ratio'] = optimal_buy_ratio * 0.6 + optimal_sell_ratio * 0.4

    else:

        if item['count_in_24'] > 10: # popular item; what happened?
            logger.warning("Find item {:s} (buff_id = {:d}) with empty order list", item['name'], item['buff_id'])
        item['weighted_ratio'] = 100

    # update time
    item['updated_at'] = int(time.time())

    # save to database
    proc_storage.update_item(item)
    proc_storage.close()

    # ensure min updating interval
    elapsed = time.time() - start
    if elapsed < MIN_INTERVAL_PER_PROCESS:
        time.sleep(MIN_INTERVAL_PER_PROCESS - elapsed)

    logger.info("Update item {:s} in group {:d}, age {:.2f} hours, time elapsed {:.2f}", hash_name, group, age / 3600, time.time() - start)

def safe_update_item(*a, **k):
    try:
        return update_item(*a, **k)
    except Exception as e:
        logger.exception('Error after retrying ...') # print traceback
        random_delay()

# ==== main ====
if __name__ == '__main__':
    while True:
        # count items with data entry
        storage = MongoDB('data')
        prev_valid = storage.get_valid_item_ids()
        logger.info("Prev valid: {:d} items", len(prev_valid))

        # count items with meta entry
        meta_storage = MongoDB('meta')
        curr_valid = meta_storage.get_valid_item_ids()
        logger.info("Curr valid: {:d} items", len(curr_valid))

        # delete items in (data - meta)
        should_delete = prev_valid - curr_valid
        for buff_id in should_delete:
            assert storage.delete_item(buff_id)
        logger.info("Deleted {:d} items", len(should_delete))

        # create items in (meta - data)
        should_create = curr_valid - prev_valid
        for buff_id in should_create:
            assert storage.insert_item({'buff_id':buff_id, 'updated_at':0, 'weighted_ratio':0, **meta_storage.get_item(buff_id)})
        logger.info("Created {:d} items", len(should_create))

        meta_storage.close()

        # init updating groups
        num_items = len(curr_valid)
        group_size_list   = [floor(0.01*num_items), floor(0.04*num_items), floor(0.05*num_items), floor(0.1*num_items), floor(0.3*num_items), floor(0.5*num_items)]
        group_weight_list = [40,                    20,                    6,                     4,                    2,                    1,                  ]
        group_slice_list  = [(sum(group_size_list[:i]), sum(group_size_list[:i+1])) for i in range(len(group_size_list))]
        assert len(group_size_list) == len(group_size_list) == len(group_slice_list)
        group_weighted_size = np.array([s*w for s, w in zip(group_size_list, group_weight_list)])
        group_proba = group_weighted_size / group_weighted_size.sum()

        # start to update
        last_restart = time.time()
        while time.time() < last_restart + RESTART_INTERVAL:
            last_speedrun = time.time()

            # regular update
            while time.time() < last_speedrun + min(SPEEDRUN_INTERVAL, RESTART_INTERVAL):
                # find a candidate
                all_items = list(storage.get_sorted_items(sort='weighted_ratio'))

                group_index = np.random.choice(range(len(group_slice_list)), p=group_proba)
                group_slice = slice(*group_slice_list[group_index])
                group_items = all_items[group_slice]
                group_items.sort(key=lambda item: item['updated_at'])

                item_to_update = group_items[0]

                # update the candidate item
                safe_update_item(item_to_update, group_index)

            if RESTART_INTERVAL < SPEEDRUN_INTERVAL: # if speedrun disabled
                continue

            # speedrun update
            logger.info("Start to sppedrun ...")

            speedrun_candidates = list(storage.get_sorted_items(sort='weighted_ratio', limit=int(2*SPEEDRUN_UPDATE_NUM)))
            speedrun_items = sorted(speedrun_candidates, key=lambda item: item['updated_at'])[:SPEEDRUN_UPDATE_NUM]

            with multiprocessing.Pool(processes=PROCESS_NUM) as pool:
                for item in speedrun_items:
                    pool.apply_async(safe_update_item, (item, -1, True))
                pool.close()
                pool.join()

            # speedrun finished; return to regular mode
            logger.info("Speedrun finished ...")

        random_delay()

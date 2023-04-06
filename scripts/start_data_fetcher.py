import asyncio
import locale
import time
import urllib
from multiprocessing import Lock, Process

import aiohttp
from database import TaskList
from loguru import logger
from utils import load_proxies

locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
from url_formats import (
    buff_json_fmt,
    c5_json_fmt,
    igxe_json_fmt,
    order_json_fmt,
    uuyp_json_fmt,
    volume_json_fmt,
)

TIMEOUT = 12  # timeout for single async request
N_PROCESSES = 4  # number of parallel fetchers
N_TRIALS = 80  # number of maxmium requests to update an item

task_list = TaskList()


async def fetch_volume(task_id, task, proxy, session, index=0):
    hash_name = task["hash_name"]
    appid = task["appid"]

    try:
        async with session.get(
            volume_json_fmt.format(
                hash_name=urllib.parse.quote(hash_name), appid=appid
            ),
            proxy=f"http://{proxy}",
            timeout=TIMEOUT,
        ) as resp:
            assert resp.status == 200
            data = await resp.json()
            assert data["success"]
            logger.info("[{}] [volume] {}", index, task_id)
    except Exception as e:
        # This is quite common since we're working with highly-unreliable proxies,
        # just return and retry. items that failed to be fetched for too many times are
        # automatically removed from the task list.
        return

    task_list.update_task(task_id, "volume_data", data)
    task_list.update_task(task_id, "tasks", task["tasks"][1:])

    if locale.atoi(data.get("volume", "0")) < 2:
        task_list.complete(task_id)
        logger.success("[{}] [skip] {}", index, task_id)


async def fetch_order(task_id, task, proxy, session, index=0):
    market_id = task["market_id"]

    try:
        async with session.get(
            order_json_fmt.format(market_id=market_id),
            proxy=f"http://{proxy}",
            timeout=TIMEOUT,
        ) as resp:
            assert resp.status == 200
            data = await resp.json()
            assert data["success"]
            logger.info("[{}] [order] {}", index, task_id)
    except Exception as e:
        return

    task_list.update_task(task_id, "order_data", data)
    task_list.update_task(task_id, "tasks", task["tasks"][1:])


async def fetch_buff(task_id, task, proxy, session, index=0):
    buff_id = task["buff_id"]
    game = task["game"]

    try:
        async with session.get(
            buff_json_fmt.format(buff_id=buff_id, game=game),
            proxy=f"http://{proxy}",
            timeout=TIMEOUT,
        ) as resp:
            assert resp.status == 200
            data = await resp.json()
            assert data["code"] == "OK"
            logger.info("[{}] [buff] {}", index, task_id)
    except Exception as e:
        return

    task_list.update_task(task_id, "buff_data", data)
    task_list.update_task(task_id, "tasks", task["tasks"][1:])


async def fetch_c5(task_id, task, proxy, session, index=0):
    c5_id = task["c5_id"]

    try:
        async with session.get(
            c5_json_fmt.format(c5_id=c5_id),
            proxy=f"http://{proxy}",
            timeout=TIMEOUT,
        ) as resp:
            assert resp.status in [200, 404]
            if resp.status == 404:
                data = None
            else:
                data = await resp.json()
                assert data["success"]
            logger.info("[{}] [c5] {}", index, task_id)
    except Exception as e:
        return

    task_list.update_task(task_id, "c5_data", data)
    task_list.update_task(task_id, "tasks", task["tasks"][1:])


async def fetch_igxe(task_id, task, proxy, session, index=0):
    igxe_id = task["igxe_id"]
    appid = task["appid"]

    try:
        async with session.get(
            igxe_json_fmt.format(igxe_id=igxe_id, appid=appid),
            proxy=f"http://{proxy}",
            timeout=TIMEOUT,
        ) as resp:
            assert resp.status in [200, 404]
            if resp.status == 404:
                data = None
            else:
                data = await resp.json()
                assert data["succ"]
            logger.info("[{}] [igxe] {}", index, task_id)
    except Exception as e:
        return

    task_list.update_task(task_id, "igxe_data", data)
    task_list.update_task(task_id, "tasks", task["tasks"][1:])


async def fetch_uuyp(task_id, task, proxy, session, index=0):
    uuyp_id = task["uuyp_id"]

    data = {
        "listSortType": 1,
        "listType": 10,
        "pageIndex": 1,
        "pageSize": 10,
        "sortType": 1,
        "templateId": str(uuyp_id),
    }

    try:
        async with session.post(
            uuyp_json_fmt,
            json=data,
            proxy=f"http://{proxy}",
            timeout=TIMEOUT,
        ) as resp:
            assert resp.status in [200, 404]
            if resp.status == 404:
                data = None
            else:
                data = await resp.json()
                assert data["Code"] == 0
            logger.info("[{}] [uuyp] {}", index, task_id)
    except Exception as e:
        return

    task_list.update_task(task_id, "uuyp_data", data)
    task_list.update_task(task_id, "tasks", task["tasks"][1:])


fetch_adapters = {
    "volume": fetch_volume,
    "order": fetch_order,
    "buff": fetch_buff,
    "c5": fetch_c5,
    "igxe": fetch_igxe,
    "uuyp": fetch_uuyp,
}


async def fetch(task_id, task, proxy, session, index=0):
    task_list.acquire(task_id)

    next_task = task["tasks"][0]
    await fetch_adapters[next_task](task_id, task, proxy, session, index)

    if not task_list.get_remaining_tasks(task_id):
        task_list.complete(task_id)
        logger.success("[{}] [success] {}", index, task_id)

    trials = task_list.get_trials(task_id)
    if trials > N_TRIALS:
        task_list.complete(task_id)
        logger.warning("Complete stale task {}", task_id)
    else:
        task_list.update_trials(task_id, trials + 1)

    task_list.release(task_id)


async def safe_fetch(task_id, task, proxy, session, index=0):
    try:
        await fetch(task_id, task, proxy, session, index)
    except Exception as e:
        task_list.release(task_id)
        logger.exception(e)


async def start_tasks(task_ids, proxies, index, lock):
    fetcher_tasks = []

    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False, limit=0)
    ) as session:
        for task_id, proxy in zip(task_ids, proxies):

            task = task_list.get_task(task_id)
            if task is None:
                continue
            assert not task["running"]

            fetcher_task = asyncio.create_task(
                safe_fetch(task_id, task, proxy, session, index)
            )
            fetcher_tasks.append(fetcher_task)

        time.sleep(1)
        lock.release()

        await asyncio.gather(*fetcher_tasks)


def job(index, lock):
    loop = asyncio.new_event_loop()

    while True:
        proxies = load_proxies()

        lock.acquire()
        time.sleep(1)
        task_ids = task_list.get_free_task_ids()

        task_ids.sort(key=lambda i: task_list.get_priority(i))

        logger.info("[{}] Get {} free tasks", index, len(task_ids))

        loop.run_until_complete(start_tasks(task_ids, proxies, index, lock))


if __name__ == "__main__":
    lock = Lock()
    task_list.flush()  # clear existing tasks
    time.sleep(20)  # wait for mapper to load new tasks

    ps = []
    for index in range(N_PROCESSES):
        p = Process(
            target=job,
            args=(
                index,
                lock,
            ),
        )
        time.sleep(3)
        p.start()
        ps.append(p)

    for p in ps:
        p.join()

import time
import numpy as np
from database import MongoDB, TaskList
from loguru import logger
from utils import calculate_after_fee

platforms = ["buff", "igxe", "c5", "uuyp"]

storage = MongoDB("data")
task_list = TaskList()


parse_ratio = lambda buy, sell_raw: (sell_raw * 0.85, buy / (sell_raw * 0.85))


def collect(buff_id, results):
    item = storage.get_item(buff_id)

    hash_name = item["hash_name"]
    quick_price = item["buff_reference_price"]
    age = time.time() - item.get("updated_at", 0)
    elapsed = time.time() - results["start"]

    if results.get("volume_data") is None:
        action = "ignore"
    else:
        item["count_in_24"] = int(
            results["volume_data"].get("volume", "0").replace(",", "")
        )
        if item["count_in_24"] < 2:
            action = "skip"
        elif results.get("order_data") is None or results.get("buff_data") is None:
            action = "ignore"
        else:
            action = "parse"

    if action == "ignore" or action == "skip":
        item["weighted_ratio"] = 100  # assign lowest update priority
        item["updated_at"] = int(time.time())
        storage.update_item(item)

        if action == "ignore":
            logger.warning(
                "Ignore item {:s} for error with age {:.2f} hours, time elapsed = {:.2f}",
                hash_name,
                age / 3600,
                elapsed,
            )
        else:
            logger.info(
                "Skip item {:s} for low volume with age {:.2f} hours, time elapsed = {:.2f}",
                hash_name,
                age / 3600,
                elapsed,
            )
        return

    order_data = results["order_data"]
    item["buy_order_list"] = list(
        tuple(order[:2]) for order in order_data["buy_order_graph"][:10]
    )
    item["sell_order_list"] = list(
        tuple(order[:2]) for order in order_data["sell_order_graph"][:10]
    )

    buff_data = results["buff_data"]
    item["buff_sell_list"] = [
        (eval(order["price"]), 0, 0) for order in buff_data["data"]["items"]
    ]

    item["igxe_sell_list"] = []
    igxe_data = results.get("igxe_data")
    if igxe_data:
        item["igxe_sell_list"] = [
            (eval(order["unit_price"]), 0, 0) for order in igxe_data["d_list"]
        ]

    item["c5_sell_list"] = []
    c5_data = results.get("c5_data")
    if c5_data:
        item["c5_sell_list"] = [
            (eval(order["price"]), 0, 0) for order in c5_data["data"]["list"]
        ]

    item["uuyp_sell_list"] = []
    uuyp_data = results.get("uuyp_data")
    if uuyp_data and uuyp_data["Data"].get("CommodityList", []):
        item["uuyp_sell_list"] = [
            (eval(order["Price"]), 0, 0) for order in uuyp_data["Data"]["CommodityList"]
        ]

    # compute ratio for each platform
    if (
        len(item["buff_sell_list"])
        and len(item["buy_order_list"])
        and len(item["sell_order_list"])
    ):

        # parse platforms
        for platform in platforms:
            if len(item["{p}_sell_list".format(p=platform)]):
                if quick_price > 8:
                    # for items with higer price, optimal := 1-st min, safe := 3-rd min
                    item["{p}_optimal_price".format(p=platform)] = item[
                        "{p}_sell_list".format(p=platform)
                    ][0][0]
                    safe_index = np.argmin(
                        [
                            t[1] if t[1] else 9999
                            for t in item["{p}_sell_list".format(p=platform)][:3]
                        ]
                    )
                    item["{p}_safe_price".format(p=platform)] = item[
                        "{p}_sell_list".format(p=platform)
                    ][safe_index][0]
                else:
                    # for items with lower price, optimal := avg of top-10 min, safe := optimal
                    item["{p}_optimal_price".format(p=platform)] = np.mean(
                        [t[0] for t in item["{p}_sell_list".format(p=platform)][:10]]
                    )
                    item["{p}_safe_price".format(p=platform)] = item[
                        "{p}_optimal_price".format(p=platform)
                    ]
            else:
                # missing sell list
                item["{p}_optimal_price".format(p=platform)] = 9999999
                item["{p}_safe_price".format(p=platform)] = 9999999

        # parse steam
        median_price = results["volume_data"].get("median_price", None)
        if median_price is not None:
            median_price_raw = float(median_price.replace(",", "")[2:])
        else:
            median_price_raw = 0

        safe_buy_list = [price for price, num in item["buy_order_list"] if num >= 3]
        safe_buy_price_raw = (
            safe_buy_list[0] if len(safe_buy_list) else item["buy_order_list"][-1][0]
        )
        optimal_buy_price_raw = item["buy_order_list"][0][0]
        optimal_sell_price_raw = item["sell_order_list"][0][0]

        item["optimal_buy_price"] = calculate_after_fee(optimal_buy_price_raw)
        item["safe_buy_price"] = calculate_after_fee(safe_buy_price_raw)
        item["optimal_sell_price"] = calculate_after_fee(optimal_sell_price_raw)
        item["safe_sell_price"] = item["optimal_sell_price"] # just a placeholder; sell should not be safe
        item["safe_transaction_price"] = calculate_after_fee(median_price_raw)
        item["optimal_transaction_price"] = item["safe_transaction_price"] # just a placeholder

        for safe in ["optimal", "safe"]:
            for mode in ["buy", "sell", "transaction"]:
                for platform in platforms:
                    item["{p}_{s}_{m}_ratio".format(p=platform, s=safe, m=mode)] = (
                        item["{p}_{s}_price".format(p=platform, s=safe)]
                        / item["{s}_{m}_price".format(s=safe, m=mode)]
                    )

        optimal_buy_ratio = min(
            item["{p}_optimal_buy_ratio".format(p=platform)] for platform in platforms
        )
        optimal_sell_ratio = min(
            item["{p}_optimal_sell_ratio".format(p=platform)] for platform in platforms
        )
        optimal_transaction_ratio = min(
            item["{p}_optimal_transaction_ratio".format(p=platform)] for platform in platforms
        )

        # assign update priority
        if optimal_transaction_ratio > 0:
            # PS: I think the latest transaction price is the most informative :)
            item["weighted_ratio"] = optimal_buy_ratio * 0.4 + optimal_sell_ratio * 0.2 + optimal_transaction_ratio * 0.4
        else:
            item["weighted_ratio"] = optimal_buy_ratio * 0.6 + optimal_sell_ratio * 0.4
        
    else:
        # get an empty sell/buy list, ignore unpopular items
        if item["count_in_24"] > 10:  # it is popular! what happened?
            logger.warning(
                "Find item {:s} (buff_id = {:d}) with empty order list",
                item["name"],
                item["buff_id"],
            )
        item["weighted_ratio"] = 100

    item["updated_at"] = int(time.time())

    # save to database
    storage.update_item(item)

    logger.info(
        "Update item {:s}, age {:.2f} hours, time elapsed {:.2f}",
        hash_name,
        age / 3600,
        elapsed,
    )


if __name__ == "__main__":

    while True:

        task_ids = task_list.get_task_ids()

        for task_id in task_ids:
            task = task_list.get_task(task_id)
            if task is None:
                continue
            if task["complete"]:
                try:
                    collect(int(task_id), task)
                except Exception as e:
                    logger.exception(e)
                task_list.delete_task(task_id)

        time.sleep(10)  # scan every 10 secs

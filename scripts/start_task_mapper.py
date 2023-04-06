import locale
import time

from database import MongoDB, TaskList
from loguru import logger

locale.setlocale(locale.LC_ALL, "en_US.UTF-8")


def parse_task(item: dict):

    buff_id = item["buff_id"]
    igxe_id = item["igxe_id"]
    c5_id = item["c5_id"]
    uuyp_id = item.get("uuyp_id", 0)
    market_id = item["market_id"]
    hash_name = item["hash_name"]
    game = item["game"]
    appid = item["appid"]

    task = {
        "buff_id": buff_id,
        "hash_name": hash_name,
        "appid": appid,
        "game": game,
        "market_id": market_id,
        "tasks": ["volume", "buff"],
        "complete": False,
        "running": False,
        "start": time.time(),
        "trials": 0,
    }

    if igxe_id:
        task["igxe_id"] = igxe_id
        task["tasks"].append("igxe")

    if c5_id:
        task["c5_id"] = c5_id
        task["tasks"].append("c5")

    if uuyp_id:
        task["uuyp_id"] = uuyp_id
        task["tasks"].append("uuyp")

    # Update steam order at the end. Since this API has the hardest rate limit,
    # one may turn to paid proxy service for this request.
    # This ensures that we only process tasks one request away from completion.
    task["tasks"].append("order")

    return task


if __name__ == "__main__":

    task_list = TaskList()

    while True:
        # count items with data entry
        storage = MongoDB("data")
        prev_valid = storage.get_valid_item_ids()
        logger.info("Prev valid: {:d} items", len(prev_valid))

        # count items with meta entry
        meta_storage = MongoDB("meta")
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
            assert storage.insert_item(
                {
                    "buff_id": buff_id,
                    "updated_at": 0,
                    "weighted_ratio": 0,
                    **meta_storage.get_item(buff_id),
                }
            )
        logger.info("Created {:d} items", len(should_create))

        meta_storage.close()

        # this loop runs ~1h, then start over to add new items from meta
        for index in range(200):

            count = task_list.count_free()
            logger.info("Find {} tasks", count)

            if count < 800:
                all_candidates = list(storage.get_sorted_items(sort="weighted_ratio"))
                N = len(all_candidates)

                # split items into 3 groups
                group_params = [(0.0, 0.1), (0.1, 0.3), (0.3, 1.0)]
                current_task_ids = task_list.get_task_ids()

                for low, high in group_params:
                    group = all_candidates[int(N * low) : int(N * high)]
                    group.sort(key=lambda item: item["updated_at"])
                    # map the oldest 600 items in each group
                    for item in group[:600]:
                        if str(item["buff_id"]) not in current_task_ids:
                            task_list.create_task(item["buff_id"], parse_task(item))

                logger.success("Mapping ends with {} tasks", task_list.count())

            time.sleep(20)

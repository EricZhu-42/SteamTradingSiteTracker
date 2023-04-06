import pymongo
import redis

MONGODB_PORT = "YOUR_MONGODB_PORT"
REDIS_PORT = "YOUR_REDIS_PORT"


class MongoDB(object):
    def __init__(self, collection, database="steam"):
        self.client = pymongo.MongoClient(host="localhost", port=MONGODB_PORT)
        self.database = self.client[database]
        self.col = self.database[collection]

    def get_valid_item_ids(self):
        return set([item["buff_id"] for item in self.col.find()])

    def get_item(self, buff_id):
        res = self.col.find({"buff_id": buff_id})
        if len(list(res.clone())):
            return res[0]
        else:
            return None

    def insert_item(self, item):
        res = self.col.insert_one(item)
        return res.acknowledged

    def delete_item(self, buff_id):
        res = self.col.delete_one({"buff_id": buff_id})
        return res.acknowledged

    def update_item(self, item):
        res = self.col.replace_one({"buff_id": item["buff_id"]}, item)
        return res.acknowledged

    def get_all_items(self, rule=None):
        if rule is None:
            rule = {}
        return self.col.find(rule)

    def get_sorted_items(self, sort, rule=None, limit=0):
        if rule is None:
            rule = {}
        return self.col.find(rule).sort(sort, pymongo.ASCENDING).limit(limit)

    def close(self):
        self.client.close()

    def _clear(self):
        return self.col.delete_many({})

    def get_size(self):
        return self.col.estimated_document_count()


class TaskList(object):
    def __init__(self):
        self.redis = redis.Redis(
            host="localhost", port=REDIS_PORT, db=0, decode_responses=True
        )

    def count(self):
        return len(self.redis.keys())

    def count_free(self):
        return len(self.get_free_task_ids())

    def complete(self, buff_id):
        self.redis.json().set(name=str(buff_id), path="complete", obj=True)

    def get_trials(self, buff_id):
        return self.redis.json().get(buff_id, "trials")

    def update_trials(self, buff_id, num):
        self.redis.json().set(buff_id, "trials", num)

    def acquire(self, buff_id):
        self.redis.json().set(name=str(buff_id), path="running", obj=True)

    def release(self, buff_id):
        self.redis.json().set(name=str(buff_id), path="running", obj=False)

    def create_task(self, buff_id, data: dict):
        self.redis.json().set(name=str(buff_id), path=".", obj=data)

    def get_remaining_tasks(self, buff_id):
        return self.redis.json().get(buff_id, "tasks")

    def get_priority(self, buff_id):
        tasks = self.redis.json().get(buff_id, "tasks")
        if tasks is None or not len(tasks):
            return 2
        elif tasks[0] == "volume":
            return 1
        else:
            return 0

    def flush(self):
        self.redis.flushdb()

    def update_task(self, buff_id, key, value):
        self.redis.json().set(name=str(buff_id), path=key, obj=value)

    def get_task_ids(self):
        return self.redis.keys()

    def delete_task(self, task_id):
        self.redis.delete(task_id)

    def get_free_task_ids(self):
        return [
            k
            for k in self.redis.keys()
            if not (
                self.redis.json().get(k, "complete")
                or self.redis.json().get(k, "running")
            )
        ]

    def get_task(self, buff_id):
        return self.redis.json().get(str(buff_id))

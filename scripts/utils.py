import time

import numpy as np

default_header = {
    'User-Agent': 'SOME_UA_STRING',
}

asian_proxies = {
    'http': 'SOME_PROXY',
    'https': 'SOME_PROXY'
}

global_proxies = {
    'http': 'SOME_PROXY',
    'https': 'SOME_PROXY'
}

def random_delay(min=15, max=17):
    delay = np.random.rand() * (max-min) + min
    time.sleep(delay)
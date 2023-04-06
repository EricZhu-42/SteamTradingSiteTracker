import time
from math import floor
from typing import Union

import numpy as np

default_header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
    "Accept": "*/*;",
}


def load_proxies():
    assert 0, "Not implemented!"
    # return your HTTP proxies, e.g., "127.0.0.1:1234"
    return []


def random_delay(min=15, max=17):
    delay = np.random.rand() * (max - min) + min
    time.sleep(delay)


def calculate_fee_helper(received_amount: float) -> dict:
    steam_fee = floor(max(received_amount * 0.05, 1))
    publisher_fee = floor(max(received_amount * 0.1, 1))
    amount_to_send = received_amount + steam_fee + publisher_fee

    return {
        "steam_fee": steam_fee,
        "publisher_fee": publisher_fee,
        "fees": steam_fee + publisher_fee,
        "amount": amount_to_send,
    }


def calculate_after_fee(amount: Union[int, float, str]) -> float:
    if isinstance(amount, str):
        amount = round(float(amount))

    amount *= 100

    iteration = 0
    estimated_amount_of_wallet = floor(amount / (0.05 + 0.1 + 1))
    ever_undershot = False
    fees = calculate_fee_helper(estimated_amount_of_wallet)

    while fees["amount"] != amount and iteration < 10:
        if fees["amount"] > amount:
            if ever_undershot:
                fees = calculate_fee_helper(estimated_amount_of_wallet - 1)
                fees["steam_fee"] += amount - fees["amount"]
                fees["amount"] = amount
                break
            else:
                estimated_amount_of_wallet -= 1
        else:
            ever_undershot = True
            estimated_amount_of_wallet += 1

        fees = calculate_fee_helper(estimated_amount_of_wallet)
        iteration += 1

    return (amount - fees["fees"]) / 100

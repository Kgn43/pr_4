from json import load
from random import choice, randint, uniform
from time import sleep
import string
from requests import post, get, JSONDecodeError, delete


def set_bot_name(length=6):
    characters = string.ascii_letters
    random_string = ''
    for _ in range(length):
        random_char = choice(characters)
        random_string += random_char
    return random_string


def get_X_key(name : string, addr):
    ans = send_request(addr, {"user": name})
    return ans["key"]


def send_request(addr, body = {}, headers = {}):
    if body:
        ans = post(addr, None, body, headers = headers)
    else:
        ans = get(addr, headers = headers)
    try:
        result = ans.json()
    except JSONDecodeError:
        raise ValueError("wrong request or answer")
    return result

def get_right_pairs(addr, id : string):
    pairs = send_request(addr + "/pair")
    right_pairs = []
    for one_pair in pairs:
        if one_pair["buy_lot_id"] == id:
            right_pairs.append(one_pair)
    return right_pairs

def get_left_pairs(addr, id : string):
    pairs = send_request(addr + "/pair")
    right_pairs = []
    for one_pair in pairs:
        if one_pair["sale_lot_id"] == id:
            right_pairs.append(one_pair)
    return right_pairs


def get_reversed_pair(pairs, sale_lot, buy_lot):
    for pair in pairs:
        pid = pair["pair_id"]
        sale_lit_new = pair["sale_lot_id"]
        buy_lot_new = pair["buy_lot_id"]
        if sale_lit_new == buy_lot and buy_lot_new == sale_lot:
            return pid

def is_enough_money(addr, num : float, id : string, x_key):
    ans = send_request(addr + "/balance", headers = {
                "X-USER-KEY": x_key
            })
    for money in ans:
        if money["lot_id"] == id:
            return float(money["quantity"]) >= num


def main():
    bot_name = set_bot_name()
    address = ''
    with open('cfg.json', 'r', encoding='utf-8') as config:
        config = load(config)
        ip = config["stock_exchange_ip"]
        port = config["stock_exchange_port"]
        address += f"http://{ip}:{port}"
    x_key = get_X_key(bot_name, address + '/user')
    pairs = send_request(address + "/pair")
    right_pairs = get_right_pairs(address, "1")
    left_pairs = get_left_pairs(address, "1")
    while True:
        orders = send_request(address + "/order")
        for order in orders:
            closed = order["closed"]
            if closed != "None":
                continue
            Type = order["Type"]
            lot_id = order["lot_id"]
            if Type == "buy":
                for pair in right_pairs:
                    pid = pair["pair_id"]
                    if pid != lot_id:
                        continue
                    sale_lot = pair["sale_lot_id"]
                    buy_lot = pair["buy_lot_id"]
                    print(order["order_id"])
                    reversed_id = get_reversed_pair(pairs, sale_lot, buy_lot)
                    quantity = order["quantity"]
                    price = order["price"]
                    if is_enough_money(address, float(quantity) * float(price), buy_lot, x_key):
                        print("sneding")
                        send_request(address + "/order", {
                            "pair_id": pid,
                            "quantity": quantity,
                            "price": price,
                            "type": "sell" 
                        }, {
                            "X-USER-KEY": x_key
                        })
            else:
                for pair in left_pairs:
                    pid = pair["pair_id"]
                    if pid != lot_id:
                        continue
                    sale_lot = pair["sale_lot_id"]
                    buy_lot = pair["buy_lot_id"]
                    print(order["order_id"])
                    reversed_id = get_reversed_pair(pairs, sale_lot, buy_lot)
                    quantity = order["quantity"]
                    price = order["price"]
                    if is_enough_money(address, float(quantity) * float(price), sale_lot, x_key): #id - от 1 до 5 (buy_loy_id/sell_lot_id)
                        print("sneding")
                        send_request(address + "/order", {
                            "pair_id": pid,
                            "quantity": quantity,
                            "price": price,
                            "type": "buy" 
                        }, {
                            "X-USER-KEY": x_key
                        })
        sleep(2)

if __name__ == "__main__":
    main()

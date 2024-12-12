from json import load
from random import choice, randint, uniform
from time import sleep
import string
from requests import post, get, JSONDecodeError


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

    while True:
        try:
            send_request(address + "/order", {
                "pair_id": choice(pairs)["pair_id"],
                "quantity": randint(1, 50),
                "price": round(uniform(0.5, 10), 2),
                "type": "buy" if randint(0, 1) == 0 else "sell"
            }, {
                "X-USER-KEY": x_key
            })["order_id"]
        except ValueError as ex:
            print(str(ex))
        sleep(2)


if __name__ == "__main__":
    main()

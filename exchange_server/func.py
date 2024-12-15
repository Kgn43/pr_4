from typing import List, Dict, Optional
from random import choice, randint # for generateon unic id
from string import hexdigits # for generateon unic id
import socket


def connect_to_db(ip: str, port: int):
    global DB_socket
    DB_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    DB_socket.connect((ip, port))
    print(f"Connected to DB {ip}:{port}")


def disconnect_from_db():
    global DB_socket
    DB_socket.close()


def send_message(message: str) -> None:
    print(f"[DEBUG]: {message = }")
    try:
        DB_socket.sendall(message.encode())
    except ConnectionResetError:
        print("Connection refused by server")
    except Exception as ex:
        print(f"Error while sending message: {ex}")


def receive_more():
    try:
        data = DB_socket.recv(1024, socket.MSG_DONTWAIT).decode()
    except BlockingIOError:
        return ""
    return data + receive_more()



def receive_messages() -> Optional[str]:
    try:
        data = DB_socket.recv(1024).decode()
        data += receive_more()
        print(f"[DEBUG]: {data = }")
        if data == "EMPTY":
            return None
        return data

    except BlockingIOError:
        pass
    except ConnectionResetError:
        print('Connection closed by server')
    except Exception as ex:
        print(f"Error while sending message: {ex}")


def get_selected(query: str) -> Optional[str]:
    send_message(query)
    res = receive_messages()
    if not res:
        return None
    return res.strip()


def safe_send(query):
    send_message(query)
    res = receive_messages()
    if res == "EMPTY":
        return None
    if res != "Success!":
        raise Exception


def gen_id(length: int = 32) -> str:
    return ''.join(choice(hexdigits) for _ in range(length))

def is_number(n):
    try:
        float(n)
        return True
    except ValueError:
        return False


def new_user(username : str):
    if not username:
        raise ValueError("Please type a username")
    if get_selected(f"select users.user_name from users where users.user_name = {username}"):
        raise ValueError("This user already exist")
    user_id = randint(1, 1000)
    key = gen_id()
    safe_send(f"insert into users values {user_id} {username} {key}")
    lot_ids = get_selected("select lot.lot_id from lot")
    for lot_id in lot_ids.strip().split('\n'):
        safe_send(f"insert into user_lot values {user_id} {lot_id} 1000")
    return {"key": key}


def spend_money(user_id, lot_id, money):
    current_data = get_selected(f"select user_lot.quantity from user_lot where user_lot.user_id = {user_id} AND user_lot.lot_id = {lot_id}")
    current_money = current_data
    if not current_money:
        raise ValueError("wrong request")
    if float(current_money) < float(money):
        raise ValueError("not enough money")
    total_money = float(current_money) - float(money)
    safe_send(f"delete from user_lot where user_lot.user_id = {user_id} AND user_lot.lot_id = {lot_id}")
    safe_send(f"insert into user_lot values {user_id} {lot_id} {total_money}")


class Order:
    def __init__(self, id, user_id, pair_id, quantity, price, Type):
        if not id or not user_id or not pair_id or not quantity or not price or not Type:
            return None
        self.id = id
        self.user_id = user_id
        self.pair_id = pair_id
        self.quantity = quantity
        self.price = price
        self.Type = Type


def order_process(seller : Order, buyer : Order):
    if float(seller.price) > float(buyer.price):
        return
    if float(seller.quantity) == float(buyer.quantity):
        safe_send(f"delete from order where order.order_id = {seller.id}")
        safe_send(f"delete from order where order.order_id = {buyer.id}")
        new_closed = randint(0, 10000000000)
        safe_send(f"insert into order values {seller.id} {seller.user_id} {seller.pair_id} {seller.quantity} {seller.price} {seller.Type} {new_closed}")
        safe_send(f"insert into order values {buyer.id} {buyer.user_id} {buyer.pair_id} {buyer.quantity} {buyer.price} {buyer.Type} {new_closed}")
        pair = get_selected(f"select pair.first_lot_id pair.second_lot_id from pair where pair.pair_id = {seller.pair_id}")
        first_lot_name, second_lot_name = pair.strip().split(";")
        first_lot_id = int(get_selected(f"select lot.lot_id from lot where lot.name = {first_lot_name}"))
        second_lot_id = int(get_selected(f"select lot.lot_id from lot where lot.name = {second_lot_name}"))
        get_money(seller.user_id, second_lot_id, float(buyer.quantity) * float(buyer.price))
        get_money(buyer.user_id, first_lot_id, float(seller.quantity) * float(seller.price))
        return {}
    elif float(seller.quantity) > float(buyer.quantity):
        safe_send(f"delete from order where order.order_id = {seller.id}")
        safe_send(f"delete from order where order.order_id = {buyer.id}")
        new_closed = randint(0, 10000000000)
        safe_send(f"insert into order values {seller.id} {seller.user_id} {seller.pair_id} {buyer.quantity} {seller.price} {seller.Type} {new_closed}")
        safe_send(f"insert into order values {buyer.id} {buyer.user_id} {buyer.pair_id} {buyer.quantity} {buyer.price} {buyer.Type} {new_closed}")
        pair = get_selected(f"select pair.first_lot_id pair.second_lot_id from pair where pair.pair_id = {seller.pair_id}")
        first_lot_name, second_lot_name = pair.strip().split(";")
        first_lot_id = int(get_selected(f"select lot.lot_id from lot where lot.name = {first_lot_name}"))
        second_lot_id = int(get_selected(f"select lot.lot_id from lot where lot.name = {second_lot_name}"))
        get_money(seller.user_id, second_lot_id, float(buyer.quantity) * float(buyer.price))
        get_money(buyer.user_id, first_lot_id, float(seller.quantity) * float(seller.price))
        #!!!
        new_id = randint(0, 1000000000)
        safe_send(f"insert into order values {new_id} {seller.user_id} {seller.pair_id} {round(float(seller.quantity) - float(buyer.quantity),2)} {seller.price} {seller.Type} None")
        return Order(new_id, seller.user_id, seller.pair_id, round(float(seller.quantity) - float(buyer.quantity),2), seller.price, seller.Type)
    else:
        safe_send(f"delete from order where order.order_id = {seller.id}")
        safe_send(f"delete from order where order.order_id = {buyer.id}")
        new_closed = randint(0, 10000000000)
        safe_send(f"insert into order values {seller.id} {seller.user_id} {seller.pair_id} {seller.quantity} {seller.price} {seller.Type} {new_closed}")
        safe_send(f"insert into order values {buyer.id} {buyer.user_id} {buyer.pair_id} {seller.quantity} {buyer.price} {buyer.Type} {new_closed}")
        pair = get_selected(f"select pair.first_lot_id pair.second_lot_id from pair where pair.pair_id = {seller.pair_id}")
        first_lot_name, second_lot_name = pair.strip().split(";")
        first_lot_id = int(get_selected(f"select lot.lot_id from lot where lot.name = {first_lot_name}"))
        second_lot_id = int(get_selected(f"select lot.lot_id from lot where lot.name = {second_lot_name}"))
        get_money(seller.user_id, second_lot_id, float(buyer.quantity) * float(buyer.price))
        get_money(buyer.user_id, first_lot_id, float(seller.quantity) * float(seller.price))
        #!!!
        new_id = randint(0, 1000000000)
        safe_send(f"insert into order values {new_id} {buyer.user_id} {buyer.pair_id} {round(float(buyer.quantity) - float(seller.quantity),2)} {buyer.price} {buyer.Type} None")
        return Order(new_id, buyer.user_id, buyer.pair_id, round(float(buyer.quantity) - float(seller.quantity),2), buyer.price, buyer.Type)


def update(pair_id):
    input = get_selected(f"select order.order_id order.user_id order.pair_id order.quantity order.price order.type from order where order.pair_id = {pair_id} AND order.closed = None")
    if not input:
        return
    input = input.strip().split('\n')
    orders = []
    for record in input:
        id, user_id, pair_id, quantity, price, Type = record.split(';')
        orders.append(Order(id, user_id, pair_id, quantity, price, Type))

    for first_order in orders:
        for second_order in orders:
            if (first_order.Type != second_order.Type) and (first_order.pair_id == second_order.pair_id) and (first_order.user_id != second_order.user_id):
                if first_order.Type == "sell":
                    new_order = order_process(first_order, second_order)
                else:
                    new_order = order_process(second_order, first_order)
                orders.remove(first_order)
                orders.remove(second_order)
                if new_order:
                    orders.append(new_order)





def get_money(user_id, lot_id, money):
    if not user_id or not lot_id:
        raise ValueError("wrong request")
    current_data = get_selected(f"select user_lot.quantity from user_lot where user_lot.user_id = {user_id} AND user_lot.lot_id = {lot_id}")
    current_money = current_data
    if not current_money:
        raise ValueError("wrong request")
    if not is_number(money):
        raise ValueError("given money value isn't number")
    safe_send(f"delete from user_lot where user_lot.user_id = {user_id} AND user_lot.lot_id = {lot_id}")
    total_money = float(money) + float(current_money)
    safe_send(f"insert into user_lot values {user_id} {lot_id} {total_money}")


def new_order(key, pair_id, quantity, price, Type):
    if not key or not pair_id or not quantity or not price or not Type:
        raise ValueError("you forget send some data")
    if (not is_number(pair_id) or not is_number(quantity) or not is_number(price)):
        raise ValueError("wrong input")
    if (Type != "sell" and Type != "buy"):
        raise ValueError("wrong operation type")
    user_id = get_selected(f"select users.user_id from users where users.key = {key}")
    if not user_id:
        raise ValueError("wrong X-USER-KEY")
    pair = get_selected(f"select pair.first_lot_id pair.second_lot_id from pair where pair.pair_id = {pair_id}")
    first_lot_name, second_lot_name = pair.strip().split(";")
    first_lot_id = int(get_selected(f"select lot.lot_id from lot where lot.name = {first_lot_name}"))
    second_lot_id = int(get_selected(f"select lot.lot_id from lot where lot.name = {second_lot_name}"))
    if Type == "sell":
        spend_money(user_id, first_lot_id, float(quantity)*float(price))
    else:
        spend_money(user_id, second_lot_id, float(quantity)*float(price))
    new_order_id = randint(0, 1000000000)
    safe_send(f"insert into order values {new_order_id} {user_id} {pair_id} {quantity} {price} {Type} None")
    update(pair_id)
    return {"order_id": new_order_id}


def get_order():
    input = get_selected(f"select order.order_id order.user_id order.pair_id order.quantity order.price order.type order.closed from order")
    if not input:
        raise ValueError("there is zero orders")
    records = input.strip().split("\n")
    result = []
    for record in records:
        order_id, user_id, lot_id, quantity, price, Type, closed = record.split(";")
        result.append({
            "order_id": order_id,
            "user_id": user_id,
            "lot_id": lot_id,
            "quantity": quantity,
            "Type": Type,
            "price": price,
            "closed": closed
        })
    return result


def get_lot():
    input = get_selected(f"select lot.lot_id lot.name from lot")
    records = input.strip().split("\n")
    result = []
    for record in records:
        lot_id, name = record.split(";")
        result.append({
            "lot_id": lot_id,
            "name": name
        })
    return result


def get_id(mtx, word):
    for i, line in enumerate(mtx):
        if word in line:
            return i, line.index(word)



def get_pair():
    input = get_selected(f"select pair.pair_id pair.first_lot_id pair.second_lot_id from pair")
    lots = get_selected(f"select lot.lot_id lot.name from lot")
    lots = lots.strip().split("\n")
    lots = [lot.split(';') for lot in lots]
    records = input.strip().split("\n")
    result = []
    for record in records:
        lot_id, first, second = record.split(";")
        line1, index1 = get_id(lots, first)
        line2, index2 = get_id(lots, second)
        result.append({
            "pair_id": lot_id,
            "sale_lot_id": lots[line1][0],
            "buy_lot_id": lots[line2][0]
        })
    return result


def delete_order(user_key, order_id) -> None:
    if not user_key:
        raise ValueError("Please send X-USER-KEY header")
    user_id = get_selected(f"select users.user_id from users where users.key = {user_key}")
    if not user_id:
        raise ValueError("wrong X-USER-KEY")
    data = get_selected(f"select order.pair_id order.quantity order.price order.type from order where order.order_id = {order_id} AND order.user_id = {user_id}")
    if not data:
        raise ValueError("nothing to delete")
    pair_id, quantity, price, Type = data.strip().split(';')
    input = get_selected(f"select pair.first_lot_id pair.second_lot_id from pair where pair.pair_id = {pair_id}")
    first_lot_name, second_lot_name = input.strip().split(";")
    first_lot_id = int(get_selected(f"select lot.lot_id from lot where lot.name = {first_lot_name}"))
    second_lot_id = int(get_selected(f"select lot.lot_id from lot where lot.name = {second_lot_name}"))
    if Type == "sell":
        get_money(user_id, first_lot_id, float(quantity)*float(price))
    else:
        get_money(user_id, second_lot_id, float(quantity)*float(price))
    safe_send(f"delete from order where order.order_id = {order_id} AND order.user_id = {user_id}")



def get_balance(user_key):
    if not user_key:
        raise ValueError("Please send X-USER-KEY header")
    user_id = get_selected(f"select users.user_id from users where users.key = {user_key}")
    if not user_id:
        raise ValueError("wrong X-USER-KEY")
    data = get_selected(f"select user_lot.lot_id user_lot.quantity from user_lot where user_lot.user_id = {user_id}")
    records = data.strip().split("\n")
    result = []
    for record in records:
        lot_id, quantity = record.split(";")
        result.append({
            "lot_id": lot_id,
            "quantity": quantity
        })
    return result

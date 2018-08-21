# coding=utf-8
from pytg.sender import Sender
from pytg.receiver import Receiver
from pytg.utils import coroutine
from collections import deque
from time import time, sleep
from getopt import getopt
from datetime import datetime
from random import randint
import sys
import re
import _thread
import random
import pytz

# username игрового бота
bot_username = 'ChatWarsBot'

# ваш username или username человека, который может отправлять запросы этому скрипту
admin_username = ''

# username бота и/или человека, которые будут отправлять приказы
order_usernames = ''

# путь к сокет файлу
socket_path = ''

# хост чтоб слушать telegram-cli
host = 'localhost'

# порт по которому слушать
port = 1338


# имя группы
group_name = ''

opts, args = getopt(sys.argv[1:], 'a:o:c:s:h:p:g:b:l:n', ['admin=', 'order=', 'socket=', 'host=', 'port=', 'group_name='])

for opt, arg in opts:
    if opt in ('-a', '--admin'):
        admin_username = arg
    elif opt in ('-o', '--order'):
        order_usernames = arg.split(',')
    elif opt in ('-s', '--socket'):
        socket_path = arg
    elif opt in ('-h', '--host'):
        host = arg
    elif opt in ('-p', '--port'):
        port = int(arg)
    elif opt in ('-n', '--group_name'):
        group_name = arg


orders = {
    'corovan': '/go'
}



sender = Sender(sock=socket_path) if socket_path else Sender(host=host,port=port)
action_list = deque([])
log_list = deque([], maxlen=30)
lt_arena = 0
get_info_diff = 360
hero_message_id = 0

bot_enabled = True
corovan_enabled = True

arena_running = False
arena_delay = False
arena_delay_day = -1
tz = pytz.timezone('Europe/Moscow')

@coroutine
def work_with_message(receiver):
    while True:
        msg = (yield)
        try:
            if msg['event'] == 'message' and 'text' in msg and msg['peer'] is not None:
                # Проверяем наличие юзернейма, чтобы не вываливался Exception
                if 'username' in msg['sender']:
                    parse_text(msg['text'], msg['sender']['username'], msg['id'])
        except Exception as err:
            log('Ошибка coroutine: {0}'.format(err))


def queue_worker():
    global get_info_diff
    global arena_delay
    global arena_delay_day
    global tz
    lt_info = 0
    # гребаная магия
    print(sender.contacts_search(bot_username))
    sleep(3)


def parse_text(text, username, message_id):
    global lt_arena
    global hero_message_id
    global bot_enabled
    global arena_enabled
    global les_enabled
    global peshera_enabled
    global moovan_enabled
    global bereg_enabled
    global corovan_enabled
    global order_enabled
    global auto_def_enabled
    global donate_enabled
    global donate_buying
    global last_captcha_id
    global arena_delay
    global arena_delay_day
    global tz
    global arena_running
    global lvl_up
    global pref
    global msg_receiver
    global quest_fight_enabled
    if bot_enabled and username == bot_username:
               
           if corovan_enabled and text.find('пытается ограбить') != -1:
            sleep(randint(2, 40))
            action_list.append(orders['corovan'])

      
            # Вкл/выкл бота
            if text == '#enable_bot':
                bot_enabled = True
                send_msg(pref, msg_receiver, 'Бот успешно включен')
            if text == '#disable_bot':
                bot_enabled = False
                send_msg(pref, msg_receiver, 'Бот успешно выключен')

            # Вкл/выкл корована
            if text == '#enable_corovan':
                corovan_enabled = True
                send_msg(pref, msg_receiver, 'Корованы успешно включены')
            if text == '#disable_corovan':
                corovan_enabled = False
                send_msg(pref, msg_receiver, 'Корованы успешно выключены')

           
def send_msg(pref, to, message):
    sender.send_msg(pref + to, message)


def fwd(pref, to, message_id):
    sender.fwd(pref + to, message_id)


def update_order(order):
    current_order['order'] = order
    current_order['time'] = time()
    if order == castle:
        action_list.append(orders['cover'])
    else:
        action_list.append(orders['attack'])
    action_list.append(order)


def log(text):
    message = '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.now()) + ' ' + text
    print(message)
    log_list.append(message)


if __name__ == '__main__':
    receiver = Receiver(sock=socket_path) if socket_path else Receiver(port=port)
    receiver.start()  # start the Connector.
    _thread.start_new_thread(queue_worker, ())
    receiver.message(work_with_message(receiver))
    receiver.stop()

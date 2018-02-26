# coding=utf-8
from pytg.sender import Sender
from pytg.receiver import Receiver
from pytg.utils import coroutine
from collections import deque
from time import time, sleep
from getopt import getopt
from datetime import datetime
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

#group forwards
peresilka = 'fitem'

# имя замка
castle_name = 'blue'

captcha_bot = 'ChatWarsCaptchaBot'

# путь к сокет файлу
socket_path = ''

# хост чтоб слушать telegram-cli
host = 'localhost'

# порт по которому слушать
port = 1338

# скидывание денег покупкой/продажей шлемов
donate_buying = False

# включить прокачку при левелапе
lvl_up = 'lvl_off'

# имя группы
group_name = ''

opts, args = getopt(sys.argv[1:], 'a:o:c:s:h:p:g:b:l:n', ['admin=', 'order=', 'castle=', 'socket=', 'host=', 'port=',
                                                          'gold=', 'buy=', 'lvlup=', 'group_name='])

for opt, arg in opts:
    if opt in ('-a', '--admin'):
        admin_username = arg
    elif opt in ('-o', '--order'):
        order_usernames = arg.split(',')
    elif opt in ('-c', '--castle'):
        castle_name = arg
    elif opt in ('-s', '--socket'):
        socket_path = arg
    elif opt in ('-h', '--host'):
        host = arg
    elif opt in ('-p', '--port'):
        port = int(arg)
    elif opt in ('-g', '--gold'):
        gold_to_left = int(arg)
    elif opt in ('-b', '--buy'):
        donate_buying = bool(arg)
    elif opt in ('-l', '--lvlup'):
        lvl_up = arg
    elif opt in ('-n', '--group_name'):
        group_name = arg



orders = {
    'red': '🇮🇲',
    'black': '🇬🇵',
    'white': '🇨🇾',
    'yellow': '🇻🇦',
    'blue': '🇪🇺',
    'mint': '🇲🇴',
    'twilight': '🇰🇮',
    'lesnoi_fort': '🌲Лесной форт',
    'les': '🌲Лес',
    'gorni_fort': '⛰Горный форт',
    'gora': '⛰',
    'morskoi_fort': '⚓Морской форт',
    'morko': '⚓️',
    'cover': '🛡 Защита',
    'attack': '⚔ Атака',
    'cover_symbol': '🛡',
    'hero': '🏅Герой',
    'corovan': '/go',
    'peshera': '🕸Пещера',
    'moovan': '🐫ГРАБИТЬ КОРОВАНЫ',
    'bereg': '🏝Побережье',
    'quests': '🗺 Квесты',
    'castle_menu': '🏰Замок',
    'lavka': '🏚Лавка',
    'snaraga': 'Снаряжение',
    'shlem': 'Шлем',
    'sell': 'Скупка предметов',
    'lvl_def': '+1 🛡Защита',
    'lvl_atk': '+1 ⚔️Атака',
    'lvl_off': 'Выключен'
}

captcha_answers = {
    # блядь, кольцов, ну и хуйню же ты придумал
    'watermelon_n_cherry': '🍉🍒',
    'bread_n_cheese': '🍞🧀',
    'cheese': '🧀',
    'pizza': '🍕',
    'hotdog': '🌭',
    'eggplant_n_carrot': '🍆🥕',
    'dog': '🐕',
    'horse': '🐎',
    'goat': '🐐',
    'cat': '🐈',
    'pig': '🐖',
    'squirrel': '🐿'
}

arena_cover = ['🛡головы', '🛡корпуса', '🛡ног']
arena_attack = ['🗡в голову', '🗡по корпусу', '🗡по ногам']
# поменять blue на red, black, white, yellow в зависимости от вашего замка
castle = orders[castle_name]
# текущий приказ на атаку/защиту, по умолчанию всегда защита, трогать не нужно
current_order = {'time': 0, 'order': castle}
# задаем получателя ответов бота: админ или группа
if group_name =='':
    pref = '@'
    msg_receiver = admin_username
else:
    pref = ''
    msg_receiver = group_name

sender = Sender(sock=socket_path) if socket_path else Sender(host=host,port=port)
action_list = deque([])
log_list = deque([], maxlen=30)
lt_arena = 0
get_info_diff = 360
hero_message_id = 0
last_captcha_id = 0
gold_to_left = 0

bot_enabled = True
arena_enabled = False
les_enabled = True
peshera_enabled = False
moovan_enabled = False
bereg_enabled = False
corovan_enabled = True
order_enabled = True
auto_def_enabled = False
donate_enabled = False
quest_fight_enabled = True

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
    print(sender.contacts_search(captcha_bot))
    print(sender.contacts_search(peresilka))
    sleep(3)
    while True:
        try:
            if time() - lt_info > get_info_diff:
                if arena_delay and arena_delay_day != datetime.now(tz).day:
                    arena_delay = False
                lt_info = time()
                curhour = datetime.now(tz).hour
                if 9 <= curhour <= 23:
                    get_info_diff = random.randint(1200, 1800)
                else:
                    get_info_diff = random.randint(10000, 11000)
                if bot_enabled:
                    send_msg('@', bot_username, orders['hero'])
                continue

            if len(action_list):
                log('Отправляем ' + action_list[0])
                send_msg('@', bot_username, action_list.popleft())
            sleep_time = random.randint(2, 5)
            sleep(sleep_time)
        except Exception as err:
            log('Ошибка очереди: {0}'.format(err))


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
        log('Получили сообщение от бота. Проверяем условия')

        if text.find('🌟Поздравляем! Новый уровень!') != -1 and lvl_up != 'lvl_off':
            log('получили уровень - {0}'.format(orders[lvl_up]))
            action_list.append('/level_up')
            action_list.append(orders[lvl_up])

        elif "Ты встретил несколько больных" in text:
            send_msg('@', peresilka, "**Поймал капчу, беги к врачу**")
            action_list.clear()
            bot_enabled = False

        elif 'Выносливость не возвращается' in text or 'Пора попариться' in text:
            send_msg('@', peresilka, "**Поймал капчу, беги к врачу**")
            bot_enabled = False

        elif 'На сегодня ты уже своё отвоевал. Приходи завтра.' in text:
            arena_delay = True
            arena_delay_day = datetime.now(tz).day
            log("Отдыхаем денек от арены")
            arena_running = False

        elif corovan_enabled and text.find(' /go') != -1:
            action_list.append(orders['corovan'])

        elif text.find('Битва семи замков через') != -1:
            hero_message_id = message_id
            m = re.search('Битва семи замков через(?: ([0-9]+)ч){0,1}(?: ([0-9]+)){0,1}', text)
            if not m.group(1):
                if m.group(2) and int(m.group(2)) <= 59:
                    state = re.search('Состояние:\n(.*)', text).group(1)
                    if auto_def_enabled and time() - current_order['time'] > 3600 and 'Отдых' in state:
                        if donate_enabled:
                            gold = int(re.search('💰([0-9]+)', text).group(1))
                            inv = re.search('🎒Рюкзак: ([0-9]+)/([0-9]+)', text)
                            log('Рюкзак: {0} / {1}'.format(inv.group(1),inv.group(2)))
                            if int(inv.group(1)) == int(inv.group(2)):
                                log('Полный рюкзак - Донат в лавку отключен')
                                donate_buying = False          
                            if gold > gold_to_left:
                                if donate_buying:
                                    log('Донат {0} золота в лавку'.format(gold-gold_to_left))
                                    action_list.append(orders['castle_menu'])
                                    action_list.append(orders['lavka'])
                                    action_list.append(orders['shlem'])
                                    while (gold-gold_to_left) >= 35:
                                        gold -= 35
                                        action_list.append('/buy_helmet2')
                                    while (gold-gold_to_left) > 0:
                                        gold -= 1
                                        action_list.append('/buy_helmet1')
                                        action_list.append('/sell_206')
                                else:
                                    log('Донат {0} золота в казну замка'.format(gold-gold_to_left))
                                    action_list.append('/donate {0}'.format(gold-gold_to_left))
                        update_order(castle)
                    return
            log('Времени достаточно')
            gold = int(re.search('💰([0-9]+)', text).group(1))
            endurance = int(re.search('Выносливость: ([0-9]+)', text).group(1))
            log('Золото: {0}, выносливость: {1}'.format(gold, endurance))
            inv = re.search('🎒Рюкзак: ([0-9]+)/([0-9]+)', text)
            log('Рюкзак: {0} / {1}'.format(inv.group(1),inv.group(2)))
            if peshera_enabled and endurance >= 2 and text.find('🛌Отдых') != -1:
                if les_enabled:
                    action_list.append(orders['quests'])
                    action_list.append(random.choice([orders['peshera'], orders['les']]))
                else:
                    action_list.append(orders['quests'])
                    action_list.append(orders['peshera'])

            elif les_enabled and not peshera_enabled and not moovan_enabled and endurance >= 1 and orders['les'] not in action_list and text.find('🛌Отдых') != -1:
                action_list.append(orders['quests'])
                action_list.append(orders['les'])
                
            elif moovan_enabled and not peshera_enabled and not les_enabled and not bereg_enabled and endurance >= 2 and orders['moovan'] not in action_list and text.find('🛌Отдых') != -1:
                action_list.append(orders['quests'])
                action_list.append(orders['moovan']) 
                
            elif bereg_enabled and endurance >= 1 and orders['bereg'] not in action_list and text.find('🛌Отдых') != -1:
                action_list.append(orders['quests'])
                action_list.append(orders['bereg'])
                
            elif arena_enabled and not arena_delay and gold >= 5 and not arena_running and text.find('🛌Отдых') != -1:
                curhour = datetime.now(tz).hour
                if 9 <= curhour <= 23:
                    log('Включаем флаг - арена запущена')
                    arena_running = True
                    action_list.append(orders['castle_menu'])
                    action_list.append('📯Арена')
                    action_list.append('🔎Поиск соперника')
                    log('Топаем на арену')
                else:
                    log('По часам не проходим на арену. Сейчас ' + str(curhour) + ' часов')

        elif arena_enabled and text.find('выбери точку атаки и точку защиты') != -1:
            arena_running = True #на случай, если арена запущена руками
            lt_arena = time()
            attack_chosen = arena_attack[random.randint(0, 2)]
            cover_chosen = arena_cover[random.randint(0, 2)]
            log('Атака: {0}, Защита: {1}'.format(attack_chosen, cover_chosen))
            action_list.append(attack_chosen)
            action_list.append(cover_chosen)

        elif text.find('Победил воин') != -1 or text.find('Ничья') != -1:
            log('Выключаем флаг - арена закончилась')
            arena_running = False

        elif quest_fight_enabled and text.find('/fight') != -1:
            c = re.search('(\/fight.*)', text).group(1)
            action_list.append(c)
            fwd('@', peresilka, message_id)

    elif username == 'ChatWarsCaptchaBot':
        if len(text) <= 4 and text in captcha_answers.values():
            sleep(3)
            action_list.append(text)
            bot_enabled = True

    else:
        if bot_enabled and order_enabled and username in order_usernames:
            if text.find(orders['red']) != -1:
                update_order(orders['red'])
            elif text.find(orders['black']) != -1:
                update_order(orders['black'])
            elif text.find(orders['white']) != -1:
                update_order(orders['white'])
            elif text.find(orders['yellow']) != -1:
                update_order(orders['yellow'])
            elif text.find(orders['blue']) != -1:
                update_order(orders['blue'])
            elif text.find(orders['mint']) != -1:
                update_order(orders['mint'])
            elif text.find(orders['twilight']) != -1:
                update_order(orders['twilight'])
            elif text.find('🌲') != -1:
                update_order(orders['lesnoi_fort'])
            elif text.find('⛰') != -1:
                update_order(orders['gorni_fort'])
            elif text.find('⚓️') != -1:
                update_order(orders['morskoi_fort'])
            elif text.find('🛡') != -1:
                update_order(castle)

        # send_msg(pref, admin_username, 'Получили команду ' + current_order['order'] + ' от ' + username)
        if username == admin_username:
            if text == '#help':
                send_msg(pref, msg_receiver, '\n'.join([
                    '#enable_bot - Включить бота',
                    '#disable_bot - Выключить бота',
                    '#enable_arena - Включить арену',
                    '#disable_arena - Выключить арену',
                    '#enable_les - Включить лес',
                    '#disable_les - Выключить лес',
                    '#enable_peshera - Включить пещеры',
                    '#disable_peshera - Выключить пещеры',
                    '#enable_corovan - Включить корован',
                    '#disable_corovan - Выключить корован',
                    '#enable_moovan - Включить moovan',
                    '#disable_moovan - Выключить moovan',
                    '#enable_bereg - Включить побережье',
                    '#disable_bereg - Выключить побережье',
                    '#enable_order - Включить приказы',
                    '#disable_order - Выключить приказы',
                    '#enable_auto_def - Включить авто деф',
                    '#disable_auto_def - Выключить авто деф',
                    '#enable_donate - Включить донат',
                    '#disable_donate - Выключить донат',
                    '#enable_quest_fight - Включить битву во время квестов',
                    '#disable_quest_fight - Выключить битву во время квестов',
                    '#enable_buy - Включить донат в лавку вместо казны',
                    '#disable_buy - Вылючить донат в лавку вместо казны',
                    "#lvl_atk - качать атаку",
                    "#lvl_def - качать защиту",
                    "#lvl_off - ничего не качать",
                    '#status - Получить статус',
                    '#hero - Получить информацию о герое',
                    '#push_order - Добавить приказ ({0})'.format(','.join(orders)),
                    '#order - Дебаг, последняя команда защиты/атаки замка',
                    '#log - Дебаг, последние 30 сообщений из лога',
                    '#time - Дебаг, текущее время',
                    '#lt_arena - Дебаг, последняя битва на арене',
                    '#get_info_diff - Дебаг, последняя разница между запросами информации о герое',
                    '#ping - Дебаг, проверить жив ли бот',
                ]))

            # Вкл/выкл бота
            elif text == '#enable_bot':
                bot_enabled = True
                send_msg(pref, msg_receiver, 'Бот успешно включен')
            elif text == '#disable_bot':
                bot_enabled = False
                send_msg(pref, msg_receiver, 'Бот успешно выключен')

            # Вкл/выкл арены
            elif text == '#enable_arena':
                arena_enabled = True
                send_msg(pref, msg_receiver, 'Арена успешно включена')
            elif text == '#disable_arena':
                arena_enabled = False
                send_msg(pref, msg_receiver, 'Арена успешно выключена')

            # Вкл/выкл леса
            elif text == '#enable_les':
                les_enabled = True
                send_msg(pref, msg_receiver, 'Лес успешно включен')
            elif text == '#disable_les':
                les_enabled = False
                send_msg(pref, msg_receiver, 'Лес успешно выключен')

            # Вкл/выкл пещеры
            elif text == '#enable_peshera':
                peshera_enabled = True
                send_msg(pref, msg_receiver, 'Пещеры успешно включены')
            elif text == '#disable_peshera':
                peshera_enabled = False
                send_msg(pref, msg_receiver, 'Пещеры успешно выключены')

            # Вкл/выкл корована
            elif text == '#enable_corovan':
                corovan_enabled = True
                send_msg(pref, msg_receiver, 'Корованы успешно включены')
            elif text == '#disable_corovan':
                corovan_enabled = False
                send_msg(pref, msg_receiver, 'Корованы успешно выключены')
                
            # Вкл/выкл moovan
            elif text == '#enable_moovan':
                moovan_enabled = True
                send_msg(pref, msg_receiver, 'Moovan успешно включен')
            elif text == '#disable_moovan':
                moovan_enabled = False
                send_msg(pref, msg_receiver, 'Moovan успешно выключены')
                
            # Вкл/выкл bereg
            elif text == '#enable_bereg':
                bereg_enabled = True
                send_msg(pref, msg_receiver, 'Побережье успешно включено')
            elif text == '#disable_bereg':
                bereg_enabled = False
                send_msg(pref, msg_receiver, 'Побережье успешно выключено')                

            # Вкл/выкл команд
            elif text == '#enable_order':
                order_enabled = True
                send_msg(pref, msg_receiver, 'Приказы успешно включены')
            elif text == '#disable_order':
                order_enabled = False
                send_msg(pref, msg_receiver, 'Приказы успешно выключены')

            # Вкл/выкл авто деф
            elif text == '#enable_auto_def':
                auto_def_enabled = True
                send_msg(pref, msg_receiver, 'Авто деф успешно включен')
            elif text == '#disable_auto_def':
                auto_def_enabled = False
                send_msg(pref, msg_receiver, 'Авто деф успешно выключен')

            # Вкл/выкл авто донат
            elif text == '#enable_donate':
                donate_enabled = True
                send_msg(pref, msg_receiver, 'Донат успешно включен')
            elif text == '#disable_donate':
                donate_enabled = False
                send_msg(pref, msg_receiver, 'Донат успешно выключен')

            # Вкл/выкл донат в лавку
            elif text == '#enable_buy':
                donate_buying = True
                send_msg(pref, msg_receiver, 'Донат в лавку успешно включен')
            elif text == '#disable_buy':
                donate_buying = False
                send_msg(pref, msg_receiver, 'Донат в лавку успешно выключен')

            # Вкл/выкл битву по время квеста
            elif text == '#enable_quest_fight':
                quest_fight_enabled = True
                send_msg(pref, msg_receiver, 'Битва включена')
            elif text == '#disable_quest_fight':
                quest_fight_enabled = False
                send_msg(pref, msg_receiver, 'Битва отключена')

            # что качать при левелапе
            elif text == '#lvl_atk':
                lvl_up = 'lvl_atk'
                send_msg(pref, msg_receiver, 'Качаем атаку')
            elif text == '#lvl_def':
                lvl_up = 'lvl_def'
                send_msg(pref, msg_receiver, 'Качаем защиту')
            elif text == '#lvl_off':
                lvl_up = 'lvl_off'
                send_msg(pref, msg_receiver, 'Не качаем ничего')

            # Получить статус
            elif text == '#status':
                send_msg(pref, msg_receiver, '\n'.join([
                    '🤖Бот включен: {0}',
                    '📯Арена включена: {1}',
                    '🔎Сейчас на арене: {2}',
                    '🌲Лес включен: {3}',
                    '🕸Пещеры включены: {4}',
                    '🏝Побережье включено: {5}',
                    '🐫Корованы включены: {6}',
                    '🤠Грабим корованы: {7}',
                    '🇪🇺Приказы включены: {8}',
                    '🛡Авто деф включен: {9}',
                    '💰Донат включен: {10}',
                    '🏚Донат в лавку вместо казны: {11}',
                    '🌟Левелап: {12}',
                ]).format(bot_enabled, arena_enabled, arena_running, les_enabled, peshera_enabled, bereg_enabled, corovan_enabled, moovan_enabled, order_enabled, 
                          auto_def_enabled, donate_enabled, donate_buying,orders[lvl_up]))

            # Информация о герое
            elif text == '#hero':
                if hero_message_id == 0:
                    send_msg(pref, msg_receiver, 'Информация о герое пока еще недоступна')
                else:
                    fwd(pref, msg_receiver, hero_message_id)

            # Получить лог
            elif text == '#log':
                send_msg(pref, msg_receiver, '\n'.join(log_list))
                log_list.clear()

            elif text == '#lt_arena':
                send_msg(pref, msg_receiver, str(lt_arena))

            elif text == '#order':
                text_date = datetime.fromtimestamp(current_order['time']).strftime('%Y-%m-%d %H:%M:%S')
                send_msg(pref, msg_receiver, current_order['order'] + ' ' + text_date)

            elif text == '#time':
                text_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                send_msg(pref, msg_receiver, text_date)

            elif text == '#ping':
                send_msg(pref, msg_receiver, '#pong')

            elif text == '#get_info_diff':
                send_msg(pref, msg_receiver, str(get_info_diff))

            elif text.startswith('#push_order'):
                command = text.split(' ')[1]
                if command in orders:
                    update_order(orders[command])
                    send_msg(pref, msg_receiver, 'Команда ' + command + ' применена')
                else:
                    send_msg(pref, msg_receiver, 'Команда ' + command + ' не распознана')

            elif text.startswith('#captcha'):
                command = text.split(' ')[1]
                if command in captcha_answers:
                    action_list.append(captcha_answers[command])
                    bot_enabled = True
                    send_msg('@', admin_username, 'Команда ' + command + ' применена')
                else:
                    send_msg('@', admin_username, 'Команда ' + command + ' не распознана')


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

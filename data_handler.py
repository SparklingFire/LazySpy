import re
import sys
import json
import time


def json_error():
    sys.exit('файл с предварительными настройками должен иметь следующий вид: '
             '\n{"user_names" : ["имя", "имя", "имя", "имя", "имя"],'
             '\n"number_of_channels": число,'
             '\n"refresh_rate": число'
             '\n}')


def create_default_json():
    file = open('settings.txt', 'a')
    file.write('{"user_names" : ["user_1", "user_2", "user_3"], "number_of_channels": 500, "refresh_rate": 60}')
    return file


def get_usernames(user_name=None):
    user_list = ''
    while len(user_list) == 0:
        if user_name is None:
            print('Пожалуйста, введите имя искомых пользователей через запятую')
            user_name = str(input())
        if re.match('^([\w\s\.\[\]]+,?\s?)+$|^[\w\s\[\]]+$', user_name):
            user_list = user_name
        else:
            print('Некорректно введенные данные. Пожалуйста, повторите попытку')
    print('Искомые пользователи: {0}'.format(user_list))
    user_list = [x for x in [username.lower().strip() for username in user_list.split(',')] if len(x) != 0]
    return user_list


def get_number_of_channels(number_of_channels=None):
    if not isinstance(number_of_channels, int):
        return json_error()
    print('Пожалуйста, введите количество отслеживаемых каналов GoodGame.')
    print('Лимит отслеживаемых каналов: 1000')
    print('При вводе пустых значений или 0 будет выставлен стандартный лимит в 50 каналов')
    result = 0
    while result == 0:
        if number_of_channels is None:
            number_of_channels = int(input())
        if int(number_of_channels) == 0:
            result = 50
        else:
            if number_of_channels >= 1000:
                result = 1000
            else:
                result = number_of_channels
    print('Количество отслеживаемых каналов: {0}'.format(result))
    return result


def get_refresh_rate(refresh_rate=None):
    if not isinstance(refresh_rate, int):
        return json_error()
    print('Пожалуйста, укажите частоту обновления (в секундах) списка активных каналов GoodGame')
    if refresh_rate is None:
        refresh_rate = int(input())
    if refresh_rate >= 1:
        result = refresh_rate
    else:
        result = 30
    print('Частота обновления отслеживаемых каналов: один раз в {0} секунд'.format(result))
    return result


def settings_reader():
    json_loader = open('settings.txt').read()

    try:
        result = json.loads(json_loader)
        data = [get_usernames(', '.join(result['user_names'])),
                get_number_of_channels(result['number_of_channels']),
                get_refresh_rate(result['refresh_rate'])
                ]
    except (KeyError, FileNotFoundError, json.JSONDecodeError):
        return json_error()
    return data

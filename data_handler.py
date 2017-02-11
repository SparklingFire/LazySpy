import re


def get_usernames():

    user_list = ''
    while len(user_list) == 0:
        print('Пожалуйста, введите имя искомых пользователей через запятую')
        user_name = str(input())
        if re.match('^([\w\s\.\[\]]+,?\s?)+$|^[\w\s\[\]]+$', user_name):
            user_list = user_name
        else:
            print('Некорректно введенные данные. Пожалуйста, повторите попытку')
    print('Искомые пользователи: {0}'.format(user_list))
    user_list = [x for x in [username.lower().strip() for username in user_list.split(',')] if len(x) != 0]
    return user_list


def get_number_of_channels():
    print('Пожалуйста, введите количество отслеживаемых каналов GoodGame.')
    print('Лимит отслеживаемых каналов: 1000')
    print('При вводе пустых значений или 0 будет выставлен стандартный лимит в 50 каналов')
    result = 0
    while result == 0:
        number_of_channels = str(input())
        if int(number_of_channels) == 0:
            result = 50
        else:
            if int(number_of_channels) >= 1000:
                result = 1000
            else:
                result = int(number_of_channels)
    return result


def get_refresh_rate():
    print('Пожалуйста, укажите временной промежуток (в секундах) для обновления списка активных каналов GoodGame')
    refresh_timer = int(input())
    return refresh_timer if refresh_timer >= 1 else 0

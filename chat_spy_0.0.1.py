import asyncio
from ws4py.manager import WebSocketManager
import peka2tv
import goodgame

CHANNELS_COUNT = 0
REFRESH_TIMER = 0


manager = WebSocketManager()
ws_fs = 'ws://chat.funstream.tv/?EIO=3&transport=websocket'
ws_gg = 'ws://chat.goodgame.ru:8081/chat/websocket'


async def goodgame_channel_set(goodgame_connection):
    while not goodgame_connection.terminated:
        await goodgame_connection.get_channels_list()
        await asyncio.sleep(REFRESH_TIMER)
    print('connection to goodgame is terminated')


async def peka2tv_ping(peka2_connection):
    while not peka2_connection.terminated:
        peka2_connection.send('2')
        await asyncio.sleep(10)
    print('connection to peka2tv is terminated')


def task_manager(peka2_connection, goodgame_connection):
    loop = asyncio.get_event_loop()
    tasks = [
        asyncio.ensure_future(peka2tv_ping(peka2_connection)),
        asyncio.ensure_future(goodgame_channel_set(goodgame_connection)),
    ]
    try:
        loop.run_until_complete(asyncio.wait(tasks))
    except KeyboardInterrupt:
        manager.close_all()
        loop.stop()


def entry_point(user_names):
    user_names = [x.strip().lower() for x in user_names.split(',')]
    manager.start()
    peka2_connection = peka2tv.Peka2TVWSConnector(ws_fs, user_names, manager)
    peka2_connection.connect()
    goodgame_connection = goodgame.GoodGameWSEntry(ws_gg, user_names, manager, CHANNELS_COUNT)
    goodgame_connection.connect()
    task_manager(peka2_connection, goodgame_connection)


if __name__ == '__main__':
    print("Please, enter user's names to search")
    user_names = ''
    while len(user_names) == 0:
        user_names = str(input())
    print('Searching: {0}'.format(user_names))
    print('Enter number of channels')
    print('Warning. Max limit: 500 channels')

    channels_counter = False
    while not channels_counter:
        try:
            CHANNELS_COUNT = int(input())
            if CHANNELS_COUNT <= 500:
                channels_counter = True
                if CHANNELS_COUNT == 0 or CHANNELS_COUNT is None:
                    CHANNELS_COUNT = 50
            else:
                print('Warning. Max limit: 500 channels')
        except ValueError:
            pass
    print('Enter the refresh timer')
    REFRESH_TIMER = int(input())
    entry_point(user_names)

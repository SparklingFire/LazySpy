import asyncio
from ws4py.manager import WebSocketManager
import re
import peka2tv
import goodgame
import faulthandler


class MainGate(object):
    def __init__(self, *args, **kwargs):
        self.peka2tv_ws = 'ws://chat.funstream.tv/?EIO=3&transport=websocket'
        self.goodgame_ws = 'ws://chat.goodgame.ru:8081/chat/websocket'
        self.username_list = None
        self.goodgame_channels_limit = None
        self.refresh_timer = None
        self.peka2_connection = None
        self.goodgame_connection = None
        self.loop = None
        self.manager = WebSocketManager()
        self.tasks = []
        self.manager.start()

    def get_usernames(self):
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
        self.username_list = user_list
        return self.username_list

    def get_goodgame_channels_limit(self):
        print('Пожалуйста, введите количество отслеживаемых каналов GoodGame.')
        print('Лимит отслеживаемых каналов: 500')
        print('При вводе пустых значений или 0 будет выставлен стандартный лимит в 50 каналов')
        result = 0
        while result == 0:
            number_of_channels = str(input())
            if int(number_of_channels) == 0:
                result = 50
            else:
                if int(number_of_channels) >= 500:
                    result = 500
                else:
                    result = int(number_of_channels)
        self.goodgame_channels_limit = result
        return self.goodgame_channels_limit

    def get_refresh_timer(self):
        print('Пожалуйста, временной промежуток (в секундах), для обновления списка активных каналов GoodGame')
        refresh_timer = int(input())
        if refresh_timer <= 0:
            self.refresh_timer = 0
        else:
            self.refresh_timer = refresh_timer
        return self.refresh_timer

    def loop_starter(self):
        self.loop = asyncio.get_event_loop()
        self._peka2tv_starter()
        self._goodgame_starter()

        tasks = asyncio.gather(self._ping_peka2tv(), self._goodgame_refresher())

        try:
            self.loop.run_until_complete(tasks)
        except KeyboardInterrupt as e:
            self.manager.close_all()
            self.manager.stop()
            self.manager.join()

            print("\nCaught keyboard interrupt. Canceling tasks...")
            tasks.cancel()
            faulthandler.enable()

            self.loop.run_forever()
            tasks.exception()
        finally:
            self.loop.close()

    def terminate_everything(self):
        tasks = asyncio.gather(*asyncio.Task.all_tasks(loop=self.loop), loop=self.loop, return_exceptions=True)
        tasks.add_done_callback(lambda t: self.loop.stop())
        tasks.cancel()

    def _peka2tv_starter(self):
        self.peka2_connection = peka2tv.Peka2TVWSConnector(self.peka2tv_ws,
                                                           self.username_list,
                                                           self.manager)
        self.peka2_connection.connect()
        return

    def _goodgame_starter(self):
        self.goodgame_connection = goodgame.GoodGameWSEntry(self.goodgame_ws,
                                                            self.username_list,
                                                            self.manager,
                                                            self.goodgame_channels_limit)
        self.goodgame_connection.connect()
        return

    async def _ping_peka2tv(self):
        while not self.peka2_connection.terminated:
            self.peka2_connection.send('2')
            await asyncio.sleep(10)
        print('connection to peka2.tv is terminated')

    async def _goodgame_refresher(self):
        while not self.goodgame_connection.terminated:
            await self.goodgame_connection.get_channels_list()
            await asyncio.sleep(self.refresh_timer)
        print('connection to goodgame is terminated')


if __name__ == '__main__':
    main_gate = MainGate()
    main_gate.get_usernames()
    main_gate.get_goodgame_channels_limit()
    main_gate.get_refresh_timer()
    main_gate.loop_starter()

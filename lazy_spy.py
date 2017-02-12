import asyncio
import ws4py
from socket import error as socket_error

import requests

import data_handler
from goodgame import goodgame_entry_websocket
from peka2tv import peka2tv_websocket


class MainConnector(object):
    def __init__(self, usernames, number_of_channels, refresh_rate):
        self.peka2tv_ws = 'wss://chat.funstream.tv/?EIO=3&transport=websocket'
        self.goodgame_ws = 'ws://chat.goodgame.ru:8081/chat/websocket'
        self.usernames = usernames
        self.goodgame_connection = None
        self.peka2tv_connection = None
        self.gg_noc = number_of_channels
        self.gg_rr = refresh_rate

        self.peka2tv_url = 'http://peka2.tv'
        self.goodgame_url = 'http://goodgame.ru'

    def _peka2tv_connection(self):
        return peka2tv_websocket.Peka2TvWebSocket(self.peka2tv_ws,
                                                  self.usernames)

    def _goodgame_connection(self):
        return goodgame_entry_websocket.GoodGameWebSocket(self.goodgame_ws,
                                                          self.usernames,
                                                          self.gg_noc
                                                          )

    async def connection_maintainer(self):
        self.goodgame_connection = self._goodgame_connection()
        self.peka2tv_connection = self._peka2tv_connection()
        peka2tv_connection_task = loop.create_task(self._connector(self.peka2tv_url, self.peka2tv_connection))
        await peka2tv_connection_task
        goodgame_connection_task = loop.create_task(self._connector(self.goodgame_url, self.goodgame_connection))
        await goodgame_connection_task
        await self._cycled_processes()

    async def _connector(self, url, ws):
        connected = False
        while connected is False:
            try:
                requests.get(url)
                try:
                    print('Подключаюсь к вебсокету {0}'.format(ws.__str__()))
                    ws.connect()
                except (ConnectionResetError, socket_error):
                    pass
                except (TypeError, ws4py.exc.HandshakeError):
                    break
                connected = True
                print('Подключение к {0} установлено'.format(ws.__str__()))
            except requests.ConnectionError:
                print('Не удается подключиться к {0}...'.format(url))
                await asyncio.sleep(5)

    async def _cycled_processes(self):
        peka2tv_task = loop.create_task(self.peka2tv_send_ping())
        goodgame_task = loop.create_task(self.goodgame_refresh_channels())
        await peka2tv_task
        await goodgame_task

    async def peka2tv_send_ping(self):
        while True:
            try:
                self.peka2tv_connection.send('2')
            except (AttributeError, BrokenPipeError, RuntimeError):
                try:
                    self.peka2tv_connection.terminate()
                except AttributeError:
                    pass
                while self.peka2tv_connection.terminated:
                    self.peka2tv_connection = self._peka2tv_connection()
                    await self._connector(self.peka2tv_url, self.peka2tv_connection)
                    await asyncio.sleep(5)
            await asyncio.sleep(10)

    async def goodgame_refresh_channels(self):
        while True:
            try:
                requests.get(self.goodgame_url)
                await self.goodgame_connection.refresh_connections()
                await asyncio.sleep(self.gg_rr)
            except:
                if self.goodgame_connection is None or self.goodgame_connection.terminated:
                    self.goodgame_connection = self._goodgame_connection()
                await self._connector(self.goodgame_url, self.goodgame_connection)

if __name__ == '__main__':
    try:
        open('settings.txt')
    except FileNotFoundError:
        data_handler.create_default_json()
    answer = input(str('Желаете ввести данные из текстового файла? [Y/n]'))
    if answer in 'Yy':
        settings = data_handler.settings_reader()
        try:
            main_connect = MainConnector(settings[0],
                                         settings[1],
                                         settings[2]
                                         )
        except ValueError:
            pass
    else:
        main_connect = MainConnector(data_handler.get_usernames(),
                                     data_handler.get_number_of_channels(),
                                     data_handler.get_refresh_rate())
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(main_connect.connection_maintainer())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pending = asyncio.Task.all_tasks()
        loop.stop()
        loop.run_until_complete(asyncio.gather(*pending))

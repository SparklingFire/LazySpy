from ws4py.client.threadedclient import WebSocketClient
import json
import asyncio
import sys
from goodgame.goodgame_child_websockets import GoodGameChildWebSocket
from socket import error as socket_error


class GoodGameWebSocket(WebSocketClient):

    def __init__(self, ws, usernames, number_of_channels):
        self.ws = ws
        self.usernames = usernames
        self.number_of_channels = number_of_channels
        self.channels_list = {}
        self.current_connections = {}
        super(self.__class__, self).__init__(self.ws, protocols=['websocket'], heartbeat_freq=30)

    def __str__(self):
        return 'GoodGame WebSocket'

    def received_message(self, message):
        message = json.loads(str(message))
        if message.get('type') == 'welcome':
            return
        try:
            for x in message.get('data').get('channels'):
                self.channels_list.update({x.get('channel_id'): x.get('channel_name')})
        except:
            print('Таинственная ошибка...')
            raise
        return

    def close(self, code=1000, reason=''):
        print(code, reason)

    async def refresh_connections(self):
        print('Загружаю список чат-каналов GoodGame.ru...')
        start = 0
        counter = self.number_of_channels
        while len(self.channels_list) < self.number_of_channels and counter > 0:
            channel_list_request = json.dumps({'type': 'get_channels_list',
                                               'data': {'start': start, 'count': counter}
                                               })
            self.send(channel_list_request)
            await asyncio.sleep(1)
            start += 50
            counter -= 50
        await self._connections_manager()

    async def _connections_manager(self):
        await self._expel_offline_channels()

        print('Подключаюсь к чат-каналам...')

        for new_channel in self.channels_list:
            if not self.current_connections.get(new_channel):
                new_connection = GoodGameChildWebSocket(self.ws, new_channel,
                                                        self.usernames,
                                                        self.channels_list.get(new_channel))
                try:
                    await asyncio.sleep(0.2)
                    new_connection.connect()
                    self.current_connections.update({new_connection.__str__(): new_connection})
                    sys.stdout.flush()
                    sys.stdout.write(
                        '\rПодключился к {0}/{1} каналам'.format(len(self.current_connections), self.number_of_channels))
                except (ConnectionResetError, socket_error) as e:
                    print('\nЧто-то пошло не так. Ожидаю переподключения...')
                    print(e)
                    break
        if len(self.current_connections) != 0:
            print('\nПодглядываю за {0} чат-каналами GoodGame.ru'.format(len(self.current_connections)))

        self.channels_list.clear()

    async def _expel_offline_channels(self):
        if len(self.current_connections) == 0:
            return
        print('Обновляю список каналов...')
        connections_to_remove = []
        for channel in self.current_connections:
            if not self.channels_list.get(channel):
                connections_to_remove.append(channel)
        for connection in connections_to_remove:
            try:
                self.current_connections.pop(connection).close()
                await asyncio.sleep(0.1)
            except (ConnectionResetError, socket_error):
                pass
        sys.stdout.flush()
        sys.stdout.write('\rОбновлено {0} каналов'.format(self.number_of_channels - len(self.current_connections)))
        return print('\nОбновление списка каналов завершено!')

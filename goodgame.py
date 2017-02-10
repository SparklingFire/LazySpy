from ws4py.client.threadedclient import WebSocketClient
from ws4py.client.threadedclient import WebSocketBaseClient
import json
import datetime
import asyncio
import sys


class GoodGameWSChat(WebSocketBaseClient):
    def __init__(self, ws, id, usernames, channel_name, manager):
        super(self.__class__, self).__init__(ws, protocols=['websocket'], heartbeat_freq=30)
        self.id = id
        self.channel_name = channel_name
        self.usernames = usernames
        self.manager = manager

    def __str__(self):
        return '{0}'.format(self.id)

    def handshake_ok(self):
        self.manager.add(self)

    def opened(self):
        join_channel_request = json.dumps({'type': 'join',
                                           'data': {'channel_id': self.id, 'hidden': 'true'}
                                           }, sort_keys=False
                                          )
        self.send(str(join_channel_request))

    def received_message(self, mes):
        received_message = json.loads(str(mes))
        if received_message.get('type') == 'message':
            if received_message.get('data').get('user_name').lower() in self.usernames:
                return self._generate_message(received_message.get('data'))

    def unhandled_error(self, error):
        print(error)

    def _generate_message(self, received_message):
        username = received_message.get('user_name')
        timestamp = datetime.datetime.fromtimestamp(received_message.get('timestamp')).strftime('%Y-%m-%d %H:%M:%S')
        text = received_message.get('text')
        message = 'GoodGame {0} Название канала:{1} От:{2} Сообщение:{3}'\
            .format(timestamp, self.channel_name, username, text)
        print('')
        print(message)
        print('')
        return self._write_result(message)

    def _write_result(self, message):
        with open('monitor_results.txt', 'a') as w:
            w.write(message + '\n')
            w.close()


class GoodGameWSEntry(WebSocketClient):
    def __init__(self, ws, usernames, m, channels_count):
        self.ws = ws
        self.m = m
        self.usernames = usernames
        self.channels_list = {}
        self.current_connections = {}
        self.channels_count = channels_count
        super(self.__class__, self).__init__(self.ws, protocols=['websocket'], heartbeat_freq=30)

    def handshake_ok(self):
        print('Goodgame is connected')
        self.m.add(self)

    def received_message(self, message):
        message = json.loads(str(message))
        if message.get('type') == 'welcome':
            return
        try:
            for x in message.get('data').get('channels'):
                self.channels_list.update({x.get('channel_id'): x.get('channel_name')})
        except:
            print('Unknown Error')
            raise
        return

    async def get_channels_list(self):
        print('Loading channel list...')
        start = 0
        counter = self.channels_count
        while len(self.channels_list) < self.channels_count and counter > 0:
            channel_list_request = json.dumps({'type': 'get_channels_list',
                                               'data': {'start': start, 'count': counter}
                                              })

            self.send(channel_list_request)
            try:
                await asyncio.sleep(1)
            except KeyboardInterrupt:
                pass
            start += 50
            counter -= 50
        return await self._connections_manager()

    async def _connections_manager(self):
        await self._expel_offline_channels()

        print('Connecting to GoodGame channels...')

        for new_channel in self.channels_list:
            if not self.current_connections.get(new_channel):
                new_connection = GoodGameWSChat(self.ws, new_channel,
                                                self.usernames,
                                                self.channels_list.get(new_channel),
                                                self.m)
                new_connection.connect()
                self.current_connections.update({new_connection.__str__(): new_connection})
                sys.stdout.flush()
                sys.stdout.write('\rConnected {0}/{1}'.format(len(self.current_connections), self.channels_count))

                while len(self.m.websockets) != len(self.current_connections) + 2:
                    await asyncio.sleep(0.5)
                await asyncio.sleep(0.01)

        print('\nConnection is complete. Monitoring {0} GoodGame channels'.format(len(self.current_connections)))

        self.channels_list.clear()

    async def _expel_offline_channels(self):
        if len(self.current_connections) == 0:
            return
        print('Proceeding refresh...')
        connections_to_remove = []
        for channel in self.current_connections:
            if not self.channels_list.get(channel):
                connections_to_remove.append(channel)
        for connection in connections_to_remove:
            self.current_connections.pop(connection).close()
            await asyncio.sleep(0.1)
        return print('Refresh is complete.')

from ws4py.client.threadedclient import WebSocketClient
import json
import datetime
from socket import error as socket_error


class GoodGameChildWebSocket(WebSocketClient):
    def __init__(self, ws, id, usernames, channel_name):
        self.id = id
        self.channel_name = channel_name
        self.usernames = usernames
        super(self.__class__, self).__init__(ws, protocols=['websocket'], heartbeat_freq=30)

    def __str__(self):
        return '{0}'.format(self.id)

    def opened(self):
        join_channel_request = json.dumps({'type': 'join',
                                           'data': {'channel_id': self.id, 'hidden': 'true'}}, sort_keys=False)
        self.send(str(join_channel_request))

    def unhandled_error(self, error):
        print(error)

    def received_message(self, mes):
        received_message = json.loads(str(mes))
        if received_message.get('type') == 'message':
            if received_message.get('data').get('user_name').lower() in self.usernames:
                return self._generate_message(received_message.get('data'))

    def _generate_message(self, received_message):
        username = received_message.get('user_name')
        timestamp = datetime.datetime.fromtimestamp(received_message.get('timestamp')).strftime('%Y-%m-%d %H:%M:%S')
        text = received_message.get('text')
        message = 'GoodGame {0} Название канала:{1} От:{2} Сообщение:{3}' \
            .format(timestamp, self.channel_name, username, text)
        print('')
        print(message)
        print('')
        return self._write_result(message)

    def _write_result(self, message):
        with open('monitor_results.txt', 'a') as w:
            w.write(message + '\n')
            w.close()

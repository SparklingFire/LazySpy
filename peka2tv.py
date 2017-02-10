from ws4py.client.threadedclient import WebSocketClient
import json
import re
import requests
import datetime


class Peka2TVWSConnector(WebSocketClient):

    def __init__(self, ws, usernames, manager, **kwargs):
        super(self.__class__, self).__init__(ws, protocols=kwargs.get('protocols', None))
        self.usernames = usernames
        self.iter = 0
        self.manager = manager

    def handshake_ok(self):
        print('peka2tv is connected')
        self.manager.add(self)

    def opened(self):
        iter_sio = "42" + str(self.iter)

        payload = [
            '/chat/join',
            {
                'channel': 'all'
            }
        ]
        self.send('{0}{1}'.format(iter_sio, json.dumps(payload)))

    def closed(self, code, reason=None):
        print(reason)
        print(code)

    def received_message(self, mes):
        if not str(mes).startswith('42['):
            return

        message = ''.join(str(x) for x in str(mes)[2:])
        jsoned = json.loads(message)
        if jsoned[1]['from'].get('name').lower() in self.usernames:
            return self._generate_message(jsoned[1])

    def unhandled_error(self, error):
        print('error!')
        print(error)

    def _generate_message(self, message):
        channel_nickname = None
        message_time = datetime.datetime.fromtimestamp(message.get('time')).strftime('%Y-%m-%d %H:%M:%S')
        target_author = None
        try:
            target_author = message['to'].get('name')
        except:
            pass
        if message.get('channel') != 'main':
            channel_id = int(message.get('channel').split('/')[1])
            payload = {
                           'id': channel_id,
                           'name': None
                        }

            request = requests.post("http://funstream.tv/api/user", data=json.dumps(payload), timeout=5)
            if request.status_code == 200:
                channel_nickname = json.loads(re.findall('{.*}', request.text)[0])['name']
            else:
                error_message = request.json()
                print(error_message)
        else:
            channel_nickname = 'Main'

        result = 'PEKA2TV {0} Название канала: {1} От: {2} Для: {3} Сообщение: {4}'\
            .format(message_time,
                    channel_nickname,
                    message['from'].get('name'),
                    target_author,
                    message['text'])
        print('')
        print(result)
        print('')
        return self._write_result(result)

    def _write_result(self, result):
        with open('monitor_results.txt', 'a') as w:
            w.write(result + '\n')
            w.close()

import asyncio
import datetime
import json
import time
import logging
import csv
import websockets

from Data.CONSTANT_OF_PROJECT import WS_RPC_URL, SERUM_PROGRAM_ID
class Scanner_V2():

    def __init__(self):
        # Адресс для подключения
        self.url = WS_RPC_URL
        # Переменная для вебсокета
        self.websocket = None
        # Переменная для отслеживания активен сокет или нет
        self.run_websocket = False

        self.log_file = 'Scanner_V2.log'
        self.logger = logging.getLogger('Scanner_V2')
        self.logger.setLevel(logging.ERROR)

        # Создаем файл, если он не существует
        open(self.log_file, 'a').close()

        # Проверяем, не добавлен ли уже файловый хендлер
        if not self.logger.handlers:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.ERROR)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            # Добавляем обработчик потока, который выводит сообщения в консоль
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.ERROR)
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

    def disable_stream_handler(self):
        '''
            Метод выключает логинг в консоль
        '''
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                self.logger.removeHandler(handler)

    async def subscribe_programm(self, program_id='srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX',
                                 send_ping: bool = True):
        '''
        Функция которая прослушиват логи переданной программы(пула) в сети
        :param program_id: id программы
        :return:
        '''
        while self.run_websocket:
            try:
                # Данные для установления соединения
                data = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "blockSubscribe",
                    "params": [
                        {"mentionsAccountOrProgram": program_id},
                        {"commitment": "confirmed", "maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"}
                    ]
                }

                # Переменная для хранения номера соединения
                log_socket = 0
                # Открываем асинхронный вебсокет
                async with websockets.connect(self.url) as ws:
                    # Отправляем запрос на подключение
                    await ws.send(json.dumps(data))
                    ping_i = 0
                    # Получаем первое сообщение с индентификатором
                    first_msg = await ws.recv()
                    # Сохраняем идентификатор подписки
                    log_socket = json.loads(first_msg)['result']

                    # Входим в бесконечный цикл прослушивания вебсокета
                    while self.run_websocket:
                        try:
                            # Получаем ответ
                            response = await ws.recv()
                            # Переводим в JSON
                            data_recv = json.loads(response)
                            # Проверяем есть ли поле с нужными нам данными
                            if 'params' in data_recv:
                                # Вызываем функцию которая парсит данные
                                coin_new = await self.parser_logs_programm(data_recv)

                                if coin_new is not None:
                                    self.run_websocket = False
                                    return coin_new

                            # Блок который отправляет ping принудительно каждые 1000 итераций, если переменная True
                            if send_ping:
                                ping_i += 1
                                if ping_i == 1000:  # Если счетчик равен 1000
                                    print(f'Send ping!')
                                    await ws.send('ping')
                                    ping_i = 0

                        except Exception as e:
                            # Данные для разрыва соединения
                            disconnect = {
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "blockUnsubscribe",
                                "params": [log_socket]
                            }
                            await ws.send(json.dumps(disconnect))
                            self.logger.error(
                                f'[{datetime.datetime.now()}] Ошибка в функции subscribe_programm : {e} \nПринудительный разрыв соединения')

            except Exception as e:
                self.logger.error(f'[{datetime.datetime.now()}] Ошибка в функции subscribe_programm : {e}')
    async def test_subs(self,program_id='srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX',
                                 send_ping: bool = True):
        '''

        :param program_id:
        :param send_ping:
        :return:
        '''

        while self.run_websocket:
            try:
                # Данные для установления соединения
                data = \
                    {
                        "jsonrpc": '2.0',
                        "id": 1,
                        "method": 'blockSubscribe',
                        "params": [
                            {"mentionsAccountOrProgram": "srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX"},
                                 {
                                    "commitment": "finalized",
                                    "maxSupportedTransactionVersion": 0,
                                    "encoding": "jsonParsed"
                                 }]
                    }
                #     {
                #     "jsonrpc": "2.0",
                #     "id": 1,
                #     "method": "blockSubscribe",
                #     #"params": ["all"]
                #     "params": [
                #         {
                #             "mentionsAccountOrProgram": "srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX"#"LieKvPRE8XeX3Y2xVNHjKlpAScD12lYySBVQ4HqoJ5op"
                #         },
                #
                #         {
                #             "commitment": "finalized",
                #             "maxSupportedTransactionVersion": 0,
                #             "encoding": "jsonParsed",
                #             "transactionDetails": "full"
                #         }
                #     ]
                # }
                async with websockets.connect(self.url) as ws:
                    # Отправляем запрос на подключение
                    await ws.send(json.dumps(data))
                    ping_i = 0
                    # Получаем первое сообщение с индентификатором
                    first_msg = await ws.recv()
                    print(first_msg)

            except Exception as e :
                print(f'err = {e}')


if __name__ == '__main__':
    async def mstar():
        sc = Scanner_V2()
        sc.run_websocket=True
        await sc.test_subs()

    asyncio.run(mstar())


'''
{"jsonrpc":"2.0","result":1836577,"id":1}
{"jsonrpc":"2.0","result":966247,"id":1}
{"jsonrpc":"2.0","result":1707969,"id":1}
{"jsonrpc":"2.0","result":966251,"id":1}
'''
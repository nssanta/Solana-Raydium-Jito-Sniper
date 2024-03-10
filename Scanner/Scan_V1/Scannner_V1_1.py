import asyncio
import datetime
import json
import re
import time
import logging
import csv
import websockets

from Data.CONSTANT_OF_PROJECT import WS_RPC_URL, RAY_V4, LAMPORTS_PER_SOL
from Scanner.Handle.RootHandler import do_get_all_data
from Tools.GetPrice import get_price_of_data

# Лимитка.
LIMIT_FOR_BUY = 2900 * LAMPORTS_PER_SOL

class Scanner_V1_1():

    def __init__(self):
        # Адресс для подключения
        self.url = WS_RPC_URL
        # Переменная для вебсокета
        self.websocket = None
        # Переменная для отслеживания активен сокет или нет
        self.run_websocket = False

        self.log_file = 'Scanner_V1.log'
        self.logger = logging.getLogger('Scanner_V1')
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

    def parsing_time(self, serv_time):
        '''

        :param serv_time:
        :return:
        '''
        try:
            # Получаем текущее время
            main_datetime = datetime.datetime.now()
            # Преобразование строк в объекты datetime
            serv_datetime = datetime.datetime.strptime(str(serv_time), "%Y-%m-%d %H:%M:%S")
            #main_datetime = datetime.datetime.strptime(main_time, "%Y-%m-%d %H:%M:%S.%f")

            # Вычисление разницы в секундах
            time_difference = (serv_datetime - main_datetime).total_seconds()
            # Округляем время
            rounded_difference = round(time_difference)

            return rounded_difference

        except Exception as e:
            self.logger.error(f'[{datetime.datetime.now()}] ошибка в функции parsing_time: {e}')


    def parser_item_logs(self, item):
        '''
        Функция из строки с данными возвращает, словарь с данными.
        :param item:
        :return:
        '''
        # Используем регулярное выражение для извлечения части строки, содержащей JSON
        json_data_str = re.search(r'{.*}', item).group(0)
        # Добавляем двойные кавычки к ключам JSON
        json_data_str = re.sub(r'(\w+):', r'"\1":', json_data_str)
        # Преобразуем JSON-строку в словарь
        data_dict = json.loads(json_data_str)
        return data_dict

    def draw_spacex_rocket(self):
        '''
        Функция рисует ракету.
        :return:
        '''
        rocket = """
            |
            |
           / \\
          /___\\
          |   |
         /|   |\\
        / |   | \\
       /__|___|__\\
        |  | |  |
        |  | |  |
        |__|_|__|
           / \\
          /___\\
        """
        print(rocket)
    def filters_listens_logs(self, data, filter_time, filter_sol):
        '''
        Функция фильтрует логи и вернет True или False
        :param data: данные логов
        :param filter_time: время для фильтра
        :param filter_sol: Сол в пуле для фильтра
        :return:
        '''
        try:
            # Данные для из лога
            dict_data = self.parser_item_logs(data)
            sol_pool = (dict_data['init_pc_amount'])/1000000000
            open_time = datetime.datetime.fromtimestamp(dict_data['open_time'])
            # Получаем разницу во времени между открытием и обнаружением.
            time_diff = self.parsing_time(open_time)

            t_d = datetime.datetime.now()
            print(f'● [{t_d}] Разница времени открытия и обнаружения: {time_diff} сек.')
            print(f'● [{t_d}] Время открытия пула: {open_time}')
            print(f'● [{t_d}] SOL в Пуле.: {sol_pool} ')

            # Проверяем ряд условий
            if (int(time_diff) >= int(filter_time)) and (sol_pool >= filter_sol): # Если время больше ()
                self.draw_spacex_rocket()
                return True
            else:
                return False

        except Exception as  e:
            self.logger.error(f'[{datetime.datetime.now()}] Ошибка в функции filters_listens_logs : {e}')
            return False


    async def parser_logs_programm(self, data):
        '''
        Функция для поиска в логах иницилизации нового монетного двора
        :param data: полученый ответ от прослушивания логов
        :return: возвращает хеш транзакции
        '''
        try:
            #st = time.perf_counter()
            if 'params' in data:  # Убрать потом
                _data = data['params']['result']['value']['logs']
                for item in _data:
                    if item.startswith(f'Program log: initialize2: InitializeInstruction2'):
                        #print(f'[{datetime.datetime.now()}] {item}')
                        # Проверяем данные по фильтру
                        if self.filters_listens_logs(data=item,filter_time=(-120),filter_sol=1):
                            # Сигнатура транзакции
                            data_sign = data['params']['result']['value']['signature']
                            print(f'[{datetime.datetime.now()}] Сигнатура транзакции иницилизации пула = https://solscan.io/tx/{data_sign}')

                            return data_sign


                return None
        except Exception as e:
            self.logger.error(f'[{datetime.datetime.now()}] Ошибка в функции parser_logs_programm : {e}')
            return None

        #print(f'{time.perf_counter() - st} всего код работал')
    async def subscribe_programm(self, program_id=RAY_V4, send_ping:bool = True):
        '''
        Функция которая прослушиват логи переданной программы(пула) в сети
        :param program_id: id программы
        :return:
        '''
        while self.run_websocket:
            try:
                # Данные для установления соединения
                data = {"jsonrpc": "2.0",
                                   "id": 1,
                                   "method": "logsSubscribe",
                                   "params": [
                                       {
                                           "mentions": [program_id]},  # "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"]},
                                       {
                                           "commitment": "processed" # processed confirmed finalized
                                           , "encoding": "jsonParsed"
                                       }
                                   ]
                                   }

                # Переменая для хранения номера соединения
                log_socket = 0
                # Открываем асинхронный вебсокет
                async with websockets.connect(self.url) as ws:
                    # Отправляем запрос на подключение
                    await ws.send(json.dumps(data))
                    ping_i = 0
                    # Получаем первое сообщение с индефикатором
                    first_msg = await ws.recv()
                    # Сохроняем индефикатор потока
                    log_socket = json.loads(first_msg)['result']

                    # Входим в бесконечный цикл прослушивания вебсокета
                    while self.run_websocket:

                        try:
                            # Получчаем ответ
                            response = await ws.recv()
                            # Переводим в json
                            data_recv = json.loads(response)
                            # Проверяем есть ли поле с нужными нам данными
                            if 'params' in data_recv: # ['params']['result']['value']['signature'])
                                # Вызываем функцию которая парсит данные
                                coin_new = await self.parser_logs_programm(data_recv)
                                # Условия когда мы будем возвращать токен, для покупки.
                                if coin_new != None:
                                    return coin_new

                                    # Получаем данные с пула.
                                    # data_of_trans = await do_get_all_data(coin_new)
                                    # # Вычисляем разницу во времени
                                    # time_dif = self.parsing_time(data_of_trans['openTime'])
                                    # # Проверяем чтобы время было больше 20 секунд до открытия
                                    # if (int(time_dif) > (-120) ): #(time_dif > 0) and
                                    #     print(data_of_trans)
                                    #     # Вычисляем Sol в пуле, по ликвидности.
                                    #     if data_of_trans['baseMint'] == 'So11111111111111111111111111111111111111112':
                                    #         sol_of_pool = data_of_trans['baseReserve']
                                    #     elif (data_of_trans['quoteMint'] == 'So11111111111111111111111111111111111111112'):
                                    #         sol_of_pool = data_of_trans['quoteReserve']
                                    #     print(f" SOL в пуле = {int(sol_of_pool)/1000000000}")
                                    #     #print(f'PRICE = {await get_price_of_data(data_ogf_trans)}')
                                    #     # Проверяем чтобы в пуле было больше 4500 SOL.
                                    #     if int(sol_of_pool) >= int(LIMIT_FOR_BUY):
                                    #         self.run_websocket = False
                                    #         return coin_new

                            # Блок который отправляет ping принудительно каждые 1000 итераций, если переменная True
                            if send_ping == True:
                                ping_i += 1
                                if ping_i == 1000: # Если счетчик равен 1000
                                    print(f'Send ping!')
                                    await ws.send('ping')
                                    ping_i = 0

                        except Exception as e:
                            # Данные для разрыва соединения
                            disconect = {
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "logsUnsubscribe",
                                "params": int(log_socket)
                            }
                            await ws.send(disconect)
                            self.logger.error(f'[{datetime.datetime.now()}] Ошибка в функции subscribe_programm : {e} \nПринудительный разрыв соединения')

            except Exception as e:
                # логируем ошибку
                self.logger.error(f'[{datetime.datetime.now()}] Ошибка в функции subscribe_programm : {e}')

    def append_to_csv(self, token, time_pool, time_my):

        file_name = 'data_parse.csv'
        # Открываем файл для дозаписи в режиме append ('a')
        with open(file_name, 'a', newline='') as csvfile:
            # Создаем объект writer, указываем разделитель ";"
            writer = csv.writer(csvfile, delimiter=';')
            # Записываем переданные строки в файл
            writer.writerow([token, time_pool, time_my])

    async def start(self, program_id):
        '''
        Функция запускает вебсокет
        :return:
        '''
        self.run_websocket = True
        #self.websocket = await asyncio.create_task(self.subscribe_programm(program_id))
        self.websocket = await asyncio.create_task(self.exsperement(program_id))

    # async def stop(self):
    #     '''
    #     Функция для остановки веб сокета.
    #     :return:
    #     '''
    #     print(f' призван стоп*******************************************************************************')
    #     self.run_websocket = False
    #     self.websocket.close()


if __name__ == '__main__':
    async def main():
        ss = Scanner_V1_1()
        ss.run_websocket=True
        #start_task = asyncio.create_task(ss.subscribe_programm())#('675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8'))
        start_task = asyncio.create_task(ss.subscribe_programm('675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8'))
        data = await start_task

        # print(data)
        # # Получаем данные о транзакции
        # data_of_transactions = await do_get_all_data(data)
        # print(data_of_transactions)
        # base_mint = data_of_transactions['baseMint']
        # quote_mint = data_of_transactions['quoteMint']
        # print(f'base = {base_mint} quote = {quote_mint}' )


    asyncio.run(main())



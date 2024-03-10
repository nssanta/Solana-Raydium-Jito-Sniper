import asyncio
import datetime
import json
import time
import logging
import csv
import websockets

from Data.CONSTANT_OF_PROJECT import WS_RPC_URL, RAY_V4, LAMPORTS_PER_SOL
from Scanner.Handle.RootHandler import do_get_all_data
from Tools.GetPrice import get_price_of_data

# Buy limit threshold (in Lamports)
LIMIT_FOR_BUY = 2900 * LAMPORTS_PER_SOL

class Scanner_V1():
    """
    Scanner class to monitor Solana blockchain logs via WebSockets.
    Detects new Raydium Liquidity Pools.
    """

    def __init__(self):
        self.url = WS_RPC_URL
        self.websocket = None
        self.run_websocket = False

        # Logging configuration
        self.log_file = 'Scanner_V1.log'
        self.logger = logging.getLogger('Scanner_V1')
        self.logger.setLevel(logging.ERROR)

        open(self.log_file, 'a').close()

        if not self.logger.handlers:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.ERROR)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.ERROR)
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

    def disable_stream_handler(self):
        """
        Disables console logging.
        """
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                self.logger.removeHandler(handler)

    def parsing_time(self, serv_time):
        """
        Calculates the time difference between server time and local time.
        :param serv_time: Server time string
        :return: Rounded difference in seconds
        """
        try:
            main_datetime = datetime.datetime.now()
            serv_datetime = datetime.datetime.strptime(serv_time, "%Y-%m-%d %H:%M:%S")
            
            time_difference = (serv_datetime - main_datetime).total_seconds()
            rounded_difference = round(time_difference)
            print("Rounded difference in seconds:", rounded_difference)

            return rounded_difference

        except Exception as e:
            self.logger.error(f'[{datetime.datetime.now()}] Error in parsing_time: {e}')

    async def parser_logs_programm(self, data):
        """
        Parses WebSocket response data to find 'initialize2' log instructions.
        :param data: JSON response from WebSocket
        :return: Transaction signature if found, else None
        """
        try:
            if 'params' in data:
                _data = data['params']['result']['value']['logs']
                for item in _data:
                    # Look for Raydium pool initialization log
                    if item.startswith(f'Program log: initialize2: InitializeInstruction2'):
                        print(f'[{datetime.datetime.now()}] {item}')
                        
                        data_sign = data['params']['result']['value']['signature']
                        print(f'[{datetime.datetime.now()}] Init Tx Signature = https://solscan.io/tx/{data_sign}')

                        return data_sign

                return None
        except Exception as e:
            self.logger.error(f'[{datetime.datetime.now()}] Error in parser_logs_programm: {e}')
            return None

    async def subscribe_programm(self, program_id=RAY_V4, send_ping:bool = True):
        """
        Main loop to subscribe to program logs via WebSocket.
        :param program_id: Program ID to monitor (e.g., Raydium V4)
        :param send_ping: Boolean to enable keep-alive pings
        :return: New coin data if conditions are met
        """
        while self.run_websocket:
            try:
                # WebSocket subscription payload
                data = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "logsSubscribe",
                    "params": [
                        {"mentions": [program_id]},
                        {"commitment": "processed", "encoding": "jsonParsed"}
                    ]
                }

                log_socket = 0
                
                async with websockets.connect(self.url) as ws:
                    await ws.send(json.dumps(data))
                    ping_i = 0
                    
                    first_msg = await ws.recv()
                    log_socket = json.loads(first_msg)['result']

                    while self.run_websocket:
                        try:
                            response = await ws.recv()
                            data_recv = json.loads(response)
                            
                            # Check if we received a notification
                            if 'params' in data_recv:
                                coin_new = await self.parser_logs_programm(data_recv)
                                
                                if coin_new != None:
                                    data_of_trans = await do_get_all_data(coin_new)
                                    time_dif = self.parsing_time(data_of_trans['openTime'])

                                    # Filter based on launch time
                                    if (int(time_dif) > (-120) ):
                                        print(data_of_trans)

                                        # Check liquidity amount
                                        sol_of_pool = 0
                                        if data_of_trans['baseMint'] == 'So11111111111111111111111111111111111111112':
                                            sol_of_pool = data_of_trans['baseReserve']
                                        elif (data_of_trans['quoteMint'] == 'So11111111111111111111111111111111111111112'):
                                            sol_of_pool = data_of_trans['quoteReserve']
                                        
                                        print(f" SOL in pool = {int(sol_of_pool)/1000000000}")

                                        # Buy if liquidity exceeds limit
                                        if int(sol_of_pool) >= int(LIMIT_FOR_BUY):
                                            self.run_websocket = False
                                            return coin_new

                            # Keep-alive ping mechanism
                            if send_ping == True:
                                ping_i += 1
                                if ping_i == 1000:
                                    print(f'Send ping!')
                                    await ws.send('ping')
                                    ping_i = 0

                        except Exception as e:
                            # Unsubscribe on error
                            disconect = {
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "logsUnsubscribe",
                                "params": int(log_socket)
                            }
                            await ws.send(disconect)
                            self.logger.error(f'[{datetime.datetime.now()}] Error in subscribe_programm: {e} \nForced disconnect')

            except Exception as e:
                self.logger.error(f'[{datetime.datetime.now()}] Error in subscribe_programm: {e}')

    def append_to_csv(self, token, time_pool, time_my):
        """
        Helper to log found tokens to CSV.
        """
        file_name = 'data_parse.csv'
        with open(file_name, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow([token, time_pool, time_my])

    async def start(self, program_id):
        """
        Starts the WebSocket listener task.
        """
        self.run_websocket = True
        self.websocket = await asyncio.create_task(self.subscribe_programm(program_id))

if __name__ == '__main__':
    async def main():
        ss = Scanner_V1()
        ss.run_websocket=True
        start_task = asyncio.create_task(ss.subscribe_programm('675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8'))
        data = await start_task

    asyncio.run(main())
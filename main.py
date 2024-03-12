import asyncio
import time
import os
from dotenv import load_dotenv

import base58
from solders.keypair import Keypair

from SWAP.BuyRaydium import buy_of_raydium
from SWAP.SellRaydium import sell_of_raydium, sell_of_data
from SWAP.Tools.HandlerSwap import data_for_sell
from Scanner.Scan_V1.Scanner_V1 import Scanner_V1
from Scanner.Scan_V1.Scannner_V1_1 import Scanner_V1_1
from Scanner.Handle.RootHandler import do_get_all_data
from solana.rpc.api import Client
from Data.CONSTANT_OF_PROJECT import RPC_URL
from solana.rpc.commitment import Commitment
from Tools.GetPrice import get_price_of_data

load_dotenv()

# Секретный ключ.
s_key = os.getenv('PRIVATE_KEY')
# Готовый формат кошелька для подписи
m_payer = Keypair.from_bytes(base58.b58decode(s_key))

# Создаем экземпляр клиента
ctx = Client(RPC_URL, commitment=Commitment(
    "confirmed"), timeout=45, blockhash_cache=True)


async def start_snipe():
    '''

    :return:
    '''
    # 1.
    # Создаем сокет и ждем отлова нужных данных
    ss = Scanner_V1_1()
    ss.run_websocket = True
    on_log = await ss.subscribe_programm('675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8')
    # Если лог равен None выходим из функции возвращая None
    if on_log == None:
        return None

    # 2.
    # Получаем данные о транзакции
    data_of_transactions = await do_get_all_data(on_log)
    print(f'data_of_transactions = {data_of_transactions}')
    # Получаем ид пула монетной пары
    time_pool = data_of_transactions['openTime']
    pool_id = data_of_transactions['poolId']
    print(f'ID Пула = {pool_id}')

    # 3.
    # Получаем монету
    base_mint = data_of_transactions['baseMint']
    quote_mint = data_of_transactions['quoteMint']
    # Проверяем, что является нашим токеном
    # if base_mint=='So11111111111111111111111111111111111111112':
    #     print(f'PRICE = {get_token_price(quote_mint)}')
    # elif(quote_mint=='So11111111111111111111111111111111111111112'):
    #     print(f'PRICE = {get_token_price(base_mint)}')

    # 4.
    # Совершаем покупку токена
    buy = await buy_of_raydium(ctx=ctx, pairs=pool_id, payer=m_payer, amount=0.007)
    print(f'\nBUY = {buy}')

    # 5.
    # Следим за ценой.
    start_price = await get_price_of_data(data_of_transactions)
    print(f' Start Price = {start_price:.20f}')
    end_price = start_price*9

    #!!! Готовим данные к продажи
    data_sell = await data_for_sell(ctx=ctx, token_swap=pool_id, payer=m_payer)


    sleep_price = True
    while sleep_price:

        temp_price = await get_price_of_data(data_of_transactions)
        if temp_price != None:
            if float(temp_price) >= float(end_price):
                print(f'\rЦена сейчас: {temp_price:.20f}', end='')
                sleep_price = False
                break
            print(f'\rЦена сейчас: {temp_price:.20f}', end='')
            time.sleep(0.5)


    try:
        # Создание списка корутин
        sell_coroutines = [
            sell_of_data(data_sell),
            sell_of_data(data_sell),
            sell_of_data(data_sell)
        ]

        s_1, s_2, s_3 = await asyncio.gather(*sell_coroutines)

        print(f'sell= {s_1}, {s_2}, {s_3}')
    except Exception as e:
        # Совершаем продажу
        print(f' ОШИБКА ПРОДАЖИ !!!!')
        sell = await sell_of_raydium(ctx=ctx, token_swap=base_mint, payer=m_payer)
        print(f'sell= {sell}')



if __name__ == '__main__':

    asyncio.run(start_snipe())




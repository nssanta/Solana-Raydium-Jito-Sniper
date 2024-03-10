import asyncio
import datetime

from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

from Data.CONSTANT_OF_PROJECT import RPC_URL, RAY_V4
from SWAP.Tools.layouts import MARKET_LAYOUT


async def get_full_keys_of_serum(key):
    '''
    Функция вычисляет недостоющие ключи, а так же получает нужные посредством своего ключа.
    :param key:
    :return:
    '''
    try:
        # Создаем клиент для подключения
        ctx = AsyncClient(RPC_URL, commitment="confirmed")
        # Делаем формат публичного ключа
        market_id = Pubkey.from_string(key)
        # Получаем ключи связаные с аккаунтом рынка
        market_info = (await ctx.get_account_info_json_parsed(market_id)).value.data
        # Декодируем данные и получаем ключи
        market_decoded = MARKET_LAYOUT.parse(market_info)

        # Получаем id Пула.
        # Байты seed
        seed = b'amm_associated_seed'
        RAY4_BYTES = bytes(RAY_V4)
        MARKET_BYTES = bytes(market_id)

        print(RAY4_BYTES, MARKET_BYTES )


        # Формируем ид пула.
        amm_id = Pubkey.find_program_address([RAY4_BYTES, MARKET_BYTES, seed], RAY_V4) # Передаем семена и Ключ Программы Рей!

        print(amm_id)

    except Exception as e:
        print(f'[{datetime.datetime.now()}] ошибка в функции get_full_keys_of_serum: {e}')




async def parse_acc_key(keys):
    '''

    :param keys:
    :return:
    '''
    # Создаем клиент.
    ctx = AsyncClient(RPC_URL, commitment="confirmed")
    # Инициализируем переменную для хранения идентификатора маркета
    market_id = None

    # Перебор всех ключей аккаунтов
    for key in keys:
        print(key)

        pb = Pubkey.from_string(str(key))
        amm_data = (await ctx.get_account_info_json_parsed(pb))

        print(len(amm_data.value.data))


if __name__ =="__main__":

    # async def mmm():
    #     key = ['5f8TYsiZ1jTZHVZ3chzNsfmhMsbVeSAyjc96oWunmLeC']
    #     await parse_acc_key(key)
    #     program_address = Pubkey.find_program_address()
    # asyncio.run(mmm())

    async def g_test():
        #key = '5f8TYsiZ1jTZHVZ3chzNsfmhMsbVeSAyjc96oWunmLeC'
        key = 'AE2Hq6zPwfnrCKodytaoRN5VzC6yZkmyrBDCYPMWde9r'

        await get_full_keys_of_serum(key)

        # G6nfBmVxNNWbDbcPNqFncwKZgbZfwS6hQ8dgzqDKmboy
        # G6nfBmVxNNWbDbcPNqFncwKZgbZfwS6hQ8dgzqDKmboy



    asyncio.run(g_test())

'''
key = 5f8TYsiZ1jTZHVZ3chzNsfmhMsbVeSAyjc96oWunmLeC

trans = https://solscan.io/tx/rm64AFdomZ8gUHPbUDMK92mcRyKeuvxVbfpgjWsBwFqF3kQZP6JJ5KPutVFEoFB3kow7CX9C4h1R8xTB63icwgS


'''



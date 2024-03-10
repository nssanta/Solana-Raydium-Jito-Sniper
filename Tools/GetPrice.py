import asyncio
import datetime
import time
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from Data.CONSTANT_OF_PROJECT import RPC_URL


import httpx


def get_token_price(token: str) -> dict:
    """
    Функция для получения информации о токене с помощью запроса к API dexscreener.com.

    :param token: Строка с символьным идентификатором токена.
    :type token: str
    :return: Словарь с данными о токене
    :rtype: dict
    """
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token}"
    try:
        # Выполняем GET запрос к API
        response = httpx.get(url)
        response.raise_for_status()  # Проверяем наличие ошибок

        # Парсим ответ в формате JSON и возвращаем его
        data = response.json()

        # Проверяем есть ли данные на дексскринере
        if data['pairs'] is None or data['pairs'] == None:
            return None
        # Парсим данные, чтобы найти радиум
        for item in data['pairs']:
            if item['dexId'] == 'raydium':
                dict_p = {
                    'sol_price':item['priceNative'],
                    'usd_price':item['priceUsd']
                }

                return dict_p

        return None

    except httpx.HTTPError as e:
        # В случае возникновения ошибки HTTP выводим ее
        print(f"Ошибка в функции get_token_info: {e}")
        return None


async def get_price_of_data(data):
    '''
    Функция получает цену пула, на основе переданого пакета данных.
    :param data:
    :return:
    '''
    # Создаем клиент для подключения
    ctx = AsyncClient(RPC_URL)

    # Получаем токены
    base_mint = data['baseMint']
    quote_mint = data['quoteMint']

    # Проверяем, какой из токенов является SOL
    if base_mint == 'So11111111111111111111111111111111111111112':
        price = await price_calculate_of_pool(ctx=ctx,sol_vault=data['baseVault'], token_vault=data['quoteVault'])
    elif (quote_mint == 'So11111111111111111111111111111111111111112'):
        price = await price_calculate_of_pool(ctx=ctx, sol_vault=data['quoteVault'], token_vault=data['baseVault'])

    return price


async def price_calculate_of_pool(ctx, sol_vault, token_vault):
    '''
    Функция формирует цену на токен, путем деления токенов. Которые получает из пула
    :param ctx:
    :param sol_vault:
    :param token_vault:
    :return:
    '''
    try:
        # Делаем ключи из строк
        sol_key = Pubkey.from_string(sol_vault)
        tok_key = Pubkey.from_string(token_vault)
        # Запрашиваем данные
        a_task = ctx.get_token_account_balance(sol_key)
        b_task = ctx.get_token_account_balance(tok_key)
        sol_balance, tok_balance = await asyncio.gather(a_task, b_task)

        return sol_balance.value.ui_amount / tok_balance.value.ui_amount

    except Exception as e:
        print(f'[{datetime.datetime.now()}] ощибка в функции price_calculate: {e}')

if __name__ == '__main__':

    async def main():

        st = time.time()
        data = {'poolId': '39MLXw7kgTWLfHytCiUVkTPZPiqK1AWnX6HY5RJuHKny', 'baseMint': 'FZ2FNQKY84oHx2y3vGe9cq9YymFSTzFFjqBatyN6bDpP', 'baseVault': 'C2e2LGfhWooR1UwhfS5rb2WcpFFWKEPsZ2BmKDdvYkhn', 'quoteMint': 'So11111111111111111111111111111111111111112', 'quoteVault': 'AHTxsnRz1TaeGRrijtCMxV22fgiiQjL3V55qfajiEhef', 'lpMint': '2dec6ARb6PNsa2nVg5j6sjY1kRH9NHEyYQdYdLvDoNAV', 'marketProgramId': 'srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX', 'marketId': 'DKHCmDMM7zwKsYrHBn2ZF5rYbbSLtnhJLu6SGByp6WaL', 'marketVersion': 3, 'withdrawQueue': '11111111111111111111111111111111', 'programId': '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8', 'version': 4, 'authority': '5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1', 'openOrders': 'BNeV4fJBNvvww1d6XXJL8dQAyQVF1Eggv5gpujvewQko', 'targetOrders': '9DCxsMizn3H1hprZ7xWe6LDzeUeZBksYFpBWBtSf1PQX', 'lpDecimals': 9, 'lpVault': '9Y3K4oPj2J1GcMyevxeB3UV34eBvsQxMxg7Tei5xEBUr', 'lpReserve': '10907712114635', 'baseReserve': '70000000000000000', 'quoteReserve': '1700000000', 'openTime': '2024-04-18 21:21:34', 'baseDecimals': 9, 'quoteDecimals': 9}

        gg = await get_price_of_data(data)
        end = time.time()
        print(f'time = {end - st}')

        print(f'{gg:.20f}')

        # a = (await ctx.get_token_account_balance(Pubkey.from_string('4Fb5Vhbha1N1Ezub1u4NBWCGWdKgABbAy5qcRofkAZMr'))).value.ui_amount
        # print(a)

    asyncio.run(main())


    # # Делает запрос.
    # st = time.time()
    # # Пример использования функции
    # token_info = get_token_price("8EV6CQa8ndVcHnhV98L4zmGzmiTKP5pm5sShS1FdLjUa")
    # print(token_info)
    # # if token_info:
    # #     print(token_info)
    # # else:
    # #     print("Не удалось получить информацию о токене.")
    # end = time.time()
    # print(f'time = {end-st}')


'''
# price in sol
async def price_calculate(ctx, sol_vault, token_vault):
     while True:
        try:
            a = (await ctx.get_token_account_balance(sol_vault)).value.ui_amount
            b = (await ctx.get_token_account_balance(token_vault)).value.ui_amount
            return a / b
        except:
             pass
'''


'''
{'poolId': '6JLMkGguY1Ko6V6hV1m3RmnCoADct1x6c84ahUQ4hKd', 'baseMint': 'FtyNZuCTRxaq1JTqcTf1BpdXrnak6VJCa4s7WK3c1yBF', 'baseVault': '4Fb5Vhbha1N1Ezub1u4NBWCGWdKgABbAy5qcRofkAZMr', 'quoteMint': 'So11111111111111111111111111111111111111112', 'quoteVault': '7VEEbr2Cm8USsHEMBEgLvxLqRuPfNEDKgeN4krutdAA9', 'lpMint': 'CgtYWFvURkhMNLDSHT48TTwAcWLGjwFCiHQfoRrzRX9M', 'marketProgramId': 'srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX', 'marketId': 'HwsXSopLuBUg7epH88bUAtBGY7xMDVN4ZwBVcJsqeXCo', 'marketVersion': 3, 'withdrawQueue': '11111111111111111111111111111111', 'programId': '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8', 'version': 4, 'authority': '5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1', 'openOrders': '2nzfhGdrNn1KhcdhNSk6qur6vEkAsziq1UPzMDmCiXd9', 'targetOrders': '9DCxsMizn3H1hprZ7xWe6LDzeUeZBksYFpBWBtSf1PQX', 'lpDecimals': 9, 'lpVault': '5LEH8GHFuvu7EYX1UxVjsUS6K4JGcMbF1ZtgfCLBX1yw', 'lpReserve': '23451078799117', 'baseReserve': '110000000000000000', 'quoteReserve': '5000000000', 'openTime': '2024-04-18 20:17:23', 'baseDecimals': 9, 'quoteDecimals': 9}
'''
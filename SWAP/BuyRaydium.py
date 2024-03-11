import asyncio
import datetime
import time
import os
from dotenv import load_dotenv

import base58
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.api import Client
from Data.CONSTANT_OF_PROJECT import GAS_PRICE, GAS_LIMIT, LAMPORTS_PER_SOL, RPC_URL
from SWAP.Tools.HandlerSwap import get_pool_keys_for_trans, get_token_account, make_swap_instruction, \
    execute_tx, data_for_buy
from spl.token.core import _TokenCore
from spl.token.client import Token
from solana.rpc.commitment import Commitment
from spl.token.instructions import CloseAccountParams, close_account
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from solders.system_program import TransferParams, transfer



async def buy_of_data(data):
    '''
    Функция для покупки
    :param data:
    :return:
    '''

    tx = await execute_tx(data['swap_tx'], data['payer'], data['Wsol_account_keyPair'], data['signers'])
    return tx

async def buy_of_raydium(ctx, pairs, payer, amount):

    '''
    Функция для покупки токенов на Радиум
    :param pairs: Монетная пару , в обмене которой будет покупка
    :param amount: кол-во . сол для покупки
    :param payer: объект кошелька, с ключами для подписи
    :return:
    '''

    # Делаем переменую видимой в остальном коде.
    global mint
    #  Делаем публичный ключ из строки , (строки id пула монетной пары)
    pair_or_mint = Pubkey.from_string(pairs)

    # Получаем ключи для обмена
    pool_keys = await get_pool_keys_for_trans(rpc=RPC_URL, token=pair_or_mint)#(token=str(pair_or_mint))

    # Если данные есть, берем котируемую монету
    if pool_keys== None:
        print(f'[{datetime.datetime.now()}]Ошибка в функции buy_of_raydium, pool_keys РАВЕН None')
        return 'failed'
    else:
        if str(pool_keys['base_mint']) != "So11111111111111111111111111111111111111112":
            mint = pool_keys['base_mint']
        else:
            mint = pool_keys['quote_mint']

    # Приводим кол-во сол для покупки к нужному виду
    amount_in = int(amount * LAMPORTS_PER_SOL)

    # 1. Здесь мы получаем информацию об аккаунте и извлекает id программы
    accountProgramId = ctx.get_account_info_json_parsed(mint)
    TOKEN_PROGRAM_ID = accountProgramId.value.owner
    #print(f'TOKEN ID = {TOKEN_PROGRAM_ID}')

    # 2. Создаем учетную запись токена
    swap_associated_token_address, swap_token_account_Instructions = get_token_account(ctx, payer.pubkey(),
                                                                                          mint)
    # 3.
    # Получаем минимальную сумму ренты
    balance_needed = Token.get_min_balance_rent_for_exempt_for_account(ctx)
    # Создаем обернутый SOL
    WSOL_token_account, swap_tx, payer, Wsol_account_keyPair, opts, = _TokenCore._create_wrapped_native_account_args(
        TOKEN_PROGRAM_ID, payer.pubkey(), payer, amount_in,
        False, balance_needed, Commitment("confirmed"))

    # 4. Создаем инструкцию для обмена токенов
    instructions_swap = make_swap_instruction(   amount_in,
                                                 WSOL_token_account,
                                                 swap_associated_token_address,
                                                 pool_keys,
                                                 mint,
                                                 ctx,  # SOLANA_CLIENT,
                                                 payer
                                                 )

    #print(f'payer.pubkey() ={payer.pubkey()}')
    # 5. Закрытие аккаунт, перед передачей токенов
    params = CloseAccountParams(account=WSOL_token_account, dest=payer.pubkey(),
                                owner=payer.pubkey(), program_id=TOKEN_PROGRAM_ID)
    closeAcc = (close_account(params))

    # 6. Добавляем инструкции к транзакции.
    swap_tx.add(set_compute_unit_limit(GAS_LIMIT))
    swap_tx.add(set_compute_unit_price(GAS_PRICE))

    if swap_token_account_Instructions != None:
        swap_tx.add(swap_token_account_Instructions)
    swap_tx.add(instructions_swap)
    swap_tx.add(closeAcc)

    
    
    tip_from_pubkey = payer.pubkey()  # Отправитель чаевых (обычно payer)
    tip_to_pubkey = Pubkey.from_string("3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT")  # Получатель чаевых
    tip_lamports = 1000  # Количество лампортов для перевода

    # Создание инструкции для перевода чаевых
    tip_transfer_instruction = transfer(TransferParams(from_pubkey=tip_from_pubkey, to_pubkey=tip_to_pubkey, lamports=tip_lamports))

    # Добавление инструкции перевода чаевых в транзакцию
    swap_tx.add(tip_transfer_instruction) 

    
    trans_run = True
    #while trans_run:
    # 7.  Вызываем функцию с отправкой транзакции в сеть. (Функция с циклом отправки)
    tx = await execute_tx(swap_tx, payer, Wsol_account_keyPair, None)
    return tx


if __name__ == '__main__':
    async def mainn():
        load_dotenv()
        # Секретный ключ.
        s_key = os.getenv('PRIVATE_KEY')
        # Готовый формат кошелька для подписи
        m_payer = Keypair.from_bytes(base58.b58decode(s_key))

        # Создаем экземпляр клиента
        ctx = Client(RPC_URL, commitment=Commitment(
            "confirmed"), timeout=50, blockhash_cache=True)

        pool_id = 'FRhB8L7Y9Qq41qZXYLtC2nw8An1RJfLLxRF2x9RwLLMo'

        st = time.time()

        print(f'Делаем данные')
        #data = await data_for_buy(ctx=ctx, pairs=pool_id, payer=m_payer, amount=0.007)
        #print(data)
        print('Отправляем покупку')
        #buy = await buy_of_data(data)
        buy = await buy_of_raydium(ctx=ctx, pairs=pool_id, payer=m_payer, amount=0.002)

        endt = time.time()
        print(f'TIME BUY = {endt-st}')

        #print(f'buy= {buy}')

    asyncio.run(mainn())


# def send_request_and_measure_time(token):
#     url = f"https://api.dexscreener.com/latest/dex/tokens/{token}"
#
#     start_time = time.time()
#     response = requests.get(url)
#     end_time = time.time()
#
#     if response.status_code == 200:
#         print("Запрос успешно выполнен.")
#         print("Время выполнения запроса:", end_time - start_time, "секунд")
#         return response.json()  # возвращаем результат запроса в формате JSON
#     else:
#         print("Ошибка при выполнении запроса. Код ошибки:", response.status_code)
#         return None
#
# # Пример использования функции:
#     token = "EP2ib6dYdEeqD8MfE2ezHCxX3kP3K2eLKkirfPm5eyMx"
#     response_data = send_request_and_measure_time(token)
#     if response_data:
#         print("Результат запроса:", response_data)
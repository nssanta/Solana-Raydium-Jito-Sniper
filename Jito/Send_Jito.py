import httpx
import asyncio
import datetime
import time
import os
from dotenv import load_dotenv

import base58
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solana.rpc.api import Client

from solders.transaction import Transaction
from solana.transaction import Transaction as SolTrans

from Data.CONSTANT_OF_PROJECT import GAS_PRICE, GAS_LIMIT, LAMPORTS_PER_SOL, RPC_URL
from SWAP.Tools.HandlerSwap import get_pool_keys_for_trans, get_token_account, make_swap_instruction, \
    execute_tx, data_for_buy
from spl.token.core import _TokenCore
from spl.token.client import Token
from solana.rpc.commitment import Commitment
from spl.token.instructions import CloseAccountParams, close_account
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from solders.system_program import TransferParams, transfer

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
    pool_keys = await get_pool_keys_for_trans(rpc=RPC_URL, token=pair_or_mint)  # (token=str(pair_or_mint))

    # Если данные есть, берем котируемую монету
    if pool_keys == None:
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
    # print(f'TOKEN ID = {TOKEN_PROGRAM_ID}')

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
    instructions_swap = make_swap_instruction(amount_in,
                                              WSOL_token_account,
                                              swap_associated_token_address,
                                              pool_keys,
                                              mint,
                                              ctx,  # SOLANA_CLIENT,
                                              payer
                                              )

    # print(f'payer.pubkey() ={payer.pubkey()}')
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
    tip_lamports = 10000  # Количество лампортов для перевода

    # Создание инструкции для перевода чаевых
    tip_transfer_instruction = transfer(
        TransferParams(from_pubkey=tip_from_pubkey, to_pubkey=tip_to_pubkey, lamports=tip_lamports))

    # Добавление инструкции перевода чаевых в транзакцию
    swap_tx.add(tip_transfer_instruction)

    # print(f'base58.b58encode(swap_tx.serialize_message()) = {base58.b58encode(swap_tx.serialize_message())}')
    out = [base58.b58encode(swap_tx.serialize_message()),]
    return

def get_sender_coins(ctx,payer):

    ixs = []
    blockhash = ctx.get_latest_blockhash().value.blockhash
    tip_account = Pubkey.from_string('96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5')
    ixs.append(
        transfer(TransferParams(from_pubkey=payer.pubkey(), to_pubkey=tip_account, lamports=1000))
    )

    print(f'itx = {type(ixs)}')
    tx = Transaction.new_signed_with_payer(
        instructions=ixs, payer=payer.pubkey(), signing_keypairs=[payer], recent_blockhash=blockhash
    )

    out = base58.b58encode(bytes(tx))

    return out

def send_transaction_bund(transaction):

    print(f' transactions {type(transaction)}= {transaction}')

    # URL для отправки запроса
    url = "https://mainnet.block-engine.jito.wtf/api/v1/bundles"

    # Заголовки запроса
    headers = {"Content-Type": "application/json"}

    # Параметры запроса
    params = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "sendBundle",
        "params": [
            [transaction]  # Список транзакций
        ]
    }

    # Отправка POST запроса
    response = httpx.post(url, json=params, headers=headers)
    print(response)
    print(response.json())
    #return response.json()
    # # Проверка успешности запроса и возврат результата
    # if response.status_code == 200:
    #     return response.json()["result"]  # Возвращает bundle id
    # else:
    #     # Обработка ошибки при неудачном запросе
    #     print(f"Ошибка при отправке запроса: {response.status_code}")
    #     return None

if __name__ == '__main__':

    async def mainn():
        load_dotenv()
        # Секретный ключ.
        s_key = os.getenv('JITO_KEY')
        # Готовый формат кошелька для подписи
        m_payer = Keypair.from_bytes(base58.b58decode(s_key))

        # Создаем экземпляр клиента
        ctx = Client(RPC_URL, commitment=Commitment(
            "confirmed"), timeout=50, blockhash_cache=True)

        pool_id = 'FRhB8L7Y9Qq41qZXYLtC2nw8An1RJfLLxRF2x9RwLLMo'

        # Пример использования функции
        #transaction = await buy_of_raydium(ctx=ctx, pairs=pool_id, payer=m_payer, amount=0.002)
        transaction = get_sender_coins(ctx=ctx, payer=m_payer)
        bundle_id = send_transaction_bund(str(transaction))

        print(bundle_id)


    asyncio.run(mainn())

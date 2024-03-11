import asyncio
import datetime
import time
import os
from dotenv import load_dotenv

import base58

from Data.CONSTANT_OF_PROJECT import GAS_PRICE, GAS_LIMIT,RPC_URL, LAMPORTS_PER_SOL
from solders.pubkey import Pubkey
from solana.rpc.types import TokenAccountOpts
from spl.token.instructions import CloseAccountParams, close_account
from solana.transaction import Transaction
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from solders.keypair import Keypair
from solana.rpc.api import Client
from solana.rpc.commitment import Commitment

from SWAP.Tools.HandlerSwap import get_pool_keys_for_trans, sell_get_token_account, get_token_account, \
    make_swap_instruction, execute_tx, data_for_sell
from Tools.GetFee import get_fee_for_message


async def sell_of_data(data):
    '''
    Функция для Продажи
    :param data:
    :return:
    '''

    tx = await (execute_tx(data['swap_tx'], data['payer'], data['Wsol_account_keyPair'], data['signers']))
    return tx



async def sell_of_raydium(ctx, token_swap, payer):
    '''
    Функция для продажи токенов
    :param ctx: Клиент рпк
    :param token_swap: токен для продажи
    :param payer: объект кошелек
    :return:
    '''

    # Делаем объект ключ монеты и сол
    mint1 = Pubkey.from_string(token_swap)
    sol = Pubkey.from_string("So11111111111111111111111111111111111111112")

    # 1. Получаем ключи пула
    # Получаем ключи для обмена
    pool_keys = await get_pool_keys_for_trans(rpc=RPC_URL, token=mint1)

    # Если данные есть, берем котируемую монету
    if pool_keys == None:
        print(f'[{datetime.datetime.now()}]Ошибка в функции sell_of_raydium, pool_keys РАВЕН None')
        return 'failed'
    if str(pool_keys['base_mint']) != "So11111111111111111111111111111111111111112":
        mint = pool_keys['base_mint']
    else:
        mint = pool_keys['quote_mint']

    # Получаем адресс программы
    TOKEN_PROGRAM_ID = ctx.get_account_info_json_parsed(mint).value.owner

    # 2. Получаем баланс токена из кошелька
    balanceBool = True
    while balanceBool:
        tokenPk = mint
        accountProgramId = ctx.get_account_info_json_parsed(tokenPk)
        programid_of_token = accountProgramId.value.owner

        accounts = ctx.get_token_accounts_by_owner_json_parsed(payer.pubkey(), TokenAccountOpts(program_id=programid_of_token)).value
        for account in accounts:
            mint_in_acc = account.account.data.parsed['info']['mint']
            if mint_in_acc == str(mint):
                amount_in = int(account.account.data.parsed['info']['tokenAmount']['amount'])
                #print("3.1 Token Balance [Lamports]: ", amount_in)
                break
        if int(amount_in) > 0:
            balanceBool = False
        else:
            print("Баланс не получен перезапуск>")
            time.sleep(2)

    # 3. Получения информации о токенных аккаунтах
    swap_token_account = sell_get_token_account(ctx, payer.pubkey(), mint)
    WSOL_token_account, WSOL_token_account_Instructions = get_token_account(ctx, payer.pubkey(), sol)

    # 4. Создаем инструкцию для обмена
    if swap_token_account == None:
        print("swap_token_account - Не найден!")
        return "failed"
    else:
        #print("5. Create Swap Instructions...")
        instructions_swap = make_swap_instruction(amount_in,
                                                     swap_token_account,
                                                     WSOL_token_account,
                                                     pool_keys,
                                                     mint,
                                                     ctx,
                                                     payer
                                                     )

    # 5. Закрываем аккаунт ( монетное кол-во)
    params = CloseAccountParams(account=WSOL_token_account, dest=payer.pubkey(), owner=payer.pubkey(),
                                program_id=TOKEN_PROGRAM_ID)
    closeAcc = (close_account(params))

    # 6. Добавляем инструкции к транзакции
    swap_tx = Transaction(fee_payer=payer.pubkey())
    signers = [payer]
    swap_tx.add(set_compute_unit_limit(GAS_LIMIT))  # my default limit
    swap_tx.add(set_compute_unit_price(GAS_PRICE))
    if WSOL_token_account_Instructions != None:
        swap_tx.add(WSOL_token_account_Instructions)
    swap_tx.add(instructions_swap)
    swap_tx.add(closeAcc)

    tx = await (execute_tx(swap_tx, payer, None, signers))
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
            "confirmed"), timeout=45, blockhash_cache=True)

        pool_id='DHDxHs1RntgAgy4NEEz2qcN4xZQ9MT9johKnoXVsdkar'

        st = time.time()
        #sell = await sell_of_raydium(ctx=ctx, token_swap=pool_id, payer=m_payer)
        data = await data_for_sell(ctx=ctx, token_swap=pool_id, payer=m_payer)
        print(f'data={data}')

        sell = await sell_of_data(data)
        endt = time.time()
        print(f'TIME SELL = {endt - st}')

        print(f'sell= {sell}')

    asyncio.run(mainn())








import asyncio
import datetime
import time
import os
from dotenv import load_dotenv

import base58
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.types import TokenAccountOpts
from spl.token.instructions import get_associated_token_address, create_associated_token_account, CloseAccountParams, \
    close_account
from solana.transaction import AccountMeta
from solders.instruction import Instruction
from solana.rpc.commitment import Commitment
from solana.rpc.api import RPCException
from solana.rpc.api import Client
from solana.transaction import Transaction
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from spl.token.core import _TokenCore
from spl.token.client import Token




from SWAP.Tools.layouts import AMM_INFO_LAYOUT_V4_1, MARKET_LAYOUT, SWAP_LAYOUT
from Data.CONSTANT_OF_PROJECT import RAY_AUTHORITY_V4, SERUM_PROGRAM_ID, RAY_V4, RPC_URL, LAMPORTS_PER_SOL, GAS_LIMIT, GAS_PRICE

async def get_pool_keys_for_trans(rpc = "https://api.mainnet-beta.solana.com", token='2Hg4gsSQdadGYm1TprKrRTdCJXvAFHediogf8yH8wMhp'):
    '''
    Функция получает ключи , нужные для обмена.
    :param rpc: Узел для запроса
    :param token: ид монетной пары пула
    :return:
    '''

    try:
        ctx = AsyncClient(rpc, commitment="confirmed")  # Инициализация асинхронного клиента для взаимодействия с RPC-сервером
        amm_id = Pubkey.from_string(str(token))  # Получение публичного ключа монетной пары пула
        amm_data = (await ctx.get_account_info_json_parsed(amm_id)).value.data  # Получение информации о пуле AMM
        amm_data_decoded = AMM_INFO_LAYOUT_V4_1.parse(amm_data)  # Декодирование информации о пуле AMM

        OPEN_BOOK_PROGRAM = Pubkey.from_bytes(amm_data_decoded.serumProgramId)  # Программный ключ для биржи Serum
        marketId = Pubkey.from_bytes(amm_data_decoded.serumMarket)  # Идентификатор рынка

        marketInfo = (await ctx.get_account_info_json_parsed(marketId)).value.data  # Получение информации о рынке
        market_decoded = MARKET_LAYOUT.parse(marketInfo)  # Декодирование информации о рынке

        # Формирование словаря с ключами для обмена
        pool_keys = {
            "amm_id": amm_id,
            "authority": RAY_AUTHORITY_V4,
            "base_mint": Pubkey.from_bytes(market_decoded.base_mint),
            "base_decimals": amm_data_decoded.coinDecimals,
            "quote_mint": Pubkey.from_bytes(market_decoded.quote_mint),
            "quote_decimals": amm_data_decoded.pcDecimals,
            "lp_mint": Pubkey.from_bytes(amm_data_decoded.lpMintAddress),
            "open_orders": Pubkey.from_bytes(amm_data_decoded.ammOpenOrders),
            "target_orders": Pubkey.from_bytes(amm_data_decoded.ammTargetOrders),
            "base_vault": Pubkey.from_bytes(amm_data_decoded.poolCoinTokenAccount),
            "quote_vault": Pubkey.from_bytes(amm_data_decoded.poolPcTokenAccount),
            "market_id": marketId,
            "market_base_vault": Pubkey.from_bytes(market_decoded.base_vault),
            "market_quote_vault": Pubkey.from_bytes(market_decoded.quote_vault),
            "market_authority": Pubkey.create_program_address(
                [bytes(marketId)]
                + [bytes([market_decoded.vault_signer_nonce])]
                + [bytes(7)],
                OPEN_BOOK_PROGRAM,
            ),
            "bids": Pubkey.from_bytes(market_decoded.bids),
            "asks": Pubkey.from_bytes(market_decoded.asks),
            "event_queue": Pubkey.from_bytes(market_decoded.event_queue),
            "pool_open_time": amm_data_decoded.poolOpenTime,
        }

        return pool_keys  # Возвращаем словарь с ключами для обмена

    except Exception as e:
        print(f'[{datetime.datetime.now()}]Ошибка в функции get_pool_keys_for_trans {e}')  # Логирование ошибки
        return None  # В случае ошибки возвращаем None

# def get_token_account(ctx, owner: Pubkey.from_string, mint: Pubkey.from_string):
#     '''
#     Функция проверяет и если нету создает "Учетную запись токена"
#     :param ctx:
#     :param owner:
#     :param mint:
#     :return:
#     '''
#     # try:
#     #     # Получить информацию об учетной записи
#     #     account_data = ctx.get_token_accounts_by_owner(owner, TokenAccountOpts(mint))
#     #     account_pubkey = account_data.value[0].pubkey
#     #
#     #     # Проверить и обновить состояние учетной записи
#     #     account_state = ctx.get_account_state(account_pubkey)
#     #     if account_state.needs_update():
#     #         ctx.update_account_state(account_pubkey)
#     #
#     #     return account_pubkey, None
#     # except:
#     #     swap_associated_token_address = get_associated_token_address(owner, mint)
#     #     swap_token_account_Instructions = create_associated_token_account(owner, owner, mint)
#     #
#     #     return swap_associated_token_address, swap_token_account_Instructions
#
#     try:
#         account_data = ctx.get_token_accounts_by_owner(owner, TokenAccountOpts(mint))
#         return account_data.value[0].pubkey, None
#     except:
#         swap_associated_token_address = get_associated_token_address(owner, mint)
#         swap_token_account_Instructions = create_associated_token_account(owner, owner, mint)
#
#         return swap_associated_token_address, swap_token_account_Instructions




def make_swap_instruction(amount_in: int, token_account_in: Pubkey.from_string,
                          token_account_out: Pubkey.from_string,
                          accounts: dict, mint, ctx, owner) -> Instruction:
    '''
    Функция для создания инструкции по обмену на децентрализованной бирже.

    :param amount_in: Сумма токенов для обмена.
    :param token_account_in: Публичный ключ счета токенов, с которого будут производиться обмены.
    :param token_account_out: Публичный ключ счета токенов, на который будут производиться обмены.
    :param accounts: Словарь, содержащий различную информацию об учетных записях, необходимую для обмена.
    :param mint: Эмиссия токена, который будет обмениваться.
    :param ctx: Объект контекста, предоставляющий необходимые функциональности.
    :param owner: Публичный ключ владельца учетных записей, участвующих в обмене.
    :return: Объект инструкции, представляющий инструкцию по обмену.
    '''

    # Извлечение необходимой информации из контекста
    tokenPk = mint
    accountProgramId = ctx.get_account_info_json_parsed(tokenPk)
    TOKEN_PROGRAM_ID = accountProgramId.value.owner

    # Определение метаданных учетной записи, необходимых для инструкции по обмену
    keys = [
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["amm_id"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["authority"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["open_orders"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["target_orders"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["base_vault"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["quote_vault"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=SERUM_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["market_id"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["bids"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["asks"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["event_queue"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["market_base_vault"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["market_quote_vault"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["market_authority"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=token_account_in, is_signer=False, is_writable=True),  # UserSourceTokenAccount
        AccountMeta(pubkey=token_account_out, is_signer=False, is_writable=True),  # UserDestTokenAccount
        AccountMeta(pubkey=owner.pubkey(), is_signer=True, is_writable=False)  # UserOwner
    ]

    # Создание данных для инструкции по обмену
    data = SWAP_LAYOUT.build(
        dict(
            instruction=9,
            amount_in=int(amount_in),
            min_amount_out=0
        )
    )
    return Instruction(RAY_V4, data, keys)



async def execute_tx(swap_tx, payer, Wsol_account_keyPair, signers): #token_symbol
    '''
    Функция отправляет транзакцию в сеть в цикле.
    :param token_symbol: Символ токена, с которым связана транзакция.
    :param swap_tx: Транзакция обмена, которую необходимо выполнить.
    :param payer: Аккаунт, оплачивающий комиссию за транзакцию.
    :param Wsol_account_keyPair: Ключевая пара аккаунта Wsol (если есть), используемая для транзакции.
    :param signers: Подписчики транзакции (если не используется ключевая пара Wsol).
    :return: Возвращает идентификатор транзакции в случае успеха, иначе возвращает "failed".
    '''
    # Инициализация клиента Solana с указанными параметрами
    solana_client = AsyncClient(RPC_URL, commitment=Commitment("confirmed"), timeout=3, blockhash_cache=True)

    try:

        # Флаг для проверки статуса транзакции
        txnBool = True

        # Цикл выполнения транзакции
        while txnBool:
            try:
                # Вывод сообщения о начале выполнения транзакции
                print("7. Execute Transaction...")
                # Запуск таймера для отслеживания времени выполнения транзакции
                start_time = time.time()
                # Отправка транзакции в сеть Solana с указанными параметрами
                if Wsol_account_keyPair != None:
                    txn = await solana_client.send_transaction(swap_tx, payer, Wsol_account_keyPair)
                else:
                    txn = await solana_client.send_transaction(swap_tx, *signers)

                # Получение идентификатора транзакции
                txid_string_sig = txn.value
                # Вывод сообщения о подтверждении транзакции
                print(f"8.[{datetime.datetime.now()}] Confirm transaction...\n Trans = https://solscan.io/tx/{txid_string_sig}\n txn = {txn.to_json()}")

                # Флаг для проверки статуса транзакции
                checkTxn = True
                # Цикл ожидания подтверждения выполнения транзакции
                while checkTxn:
                    try:
                        
                        # Получение статуса транзакции
                        status = await solana_client.get_transaction(txid_string_sig, "json")
                        
                        # Проверка успешного выполнения транзакции
                        #if status.value.transaction.meta.err == None:
                        if status is not None and status.value is not None and status.value.transaction is not None:
                            if status.value.transaction.meta.err == None:
                                # Если транзакция выполнена успешно
                                execution_time = time.time() - start_time
                                print(f"[{datetime.datetime.now()}][TXN] Transaction Success", txn.value)
                                print(f"[{datetime.datetime.now()}] Execution time: {execution_time} seconds")

                                # Установка флагов завершения транзакции
                                txnBool = False
                                checkTxn = False
                                print(f"[{datetime.datetime.now()}]e|TXN Success", f"[Raydium] TXN Execution time: {execution_time}")
                                return txid_string_sig  # Возвращаем идентификатор транзакции

                            else:
                                # Если транзакция завершилась ошибкой
                                print(f"[{datetime.datetime.now()}] Transaction Failed")
                                execution_time = time.time() - start_time
                                print(f"[{datetime.datetime.now()}] Execution time: {execution_time} seconds")
                                checkTxn = False

                    except Exception as e:
                        print(f"[{datetime.datetime.now()}] Ошибка при подтверждении транзакции: ", e)  # Вывод ошибки для отладки
                        pass

            except RPCException as ee:
                # Обработка ошибок RPC
                print(f"[{datetime.datetime.now()}] _Error: [{ee.args[0].message}]...\nRetrying...")
                #print(f"e|TXN ERROR - {token_symbol}", f"[Raydium]: {e.args[0].data.logs}")

            except Exception as e:
                # Обработка других исключений
                #print(f"e|TXN Exception ERROR {token_symbol}", f"[Raydium]: {e.args[0].message}")
                print(f"[{datetime.datetime.now()}] Error: [{e}]...\nEnd...")
                txnBool = False
                return "failed"
    except:
        # Обработка исключений во внешнем цикле
        print(f"[{datetime.datetime.now()}] Main Swap error Raydium... retrying...")

def sell_get_token_account(ctx, owner: Pubkey.from_string, mint: Pubkey.from_string):
    '''
    Получения публичного ключа токенного аккаунта, принадлежащего указанному владельцу и связанного с указанной монетой
    :param ctx:
    :param owner:
    :param mint:
    :return:
    '''
    try:
        account_data = ctx.get_token_accounts_by_owner(owner, TokenAccountOpts(mint))
        return account_data.value[0].pubkey
    except:
        print("Mint Token Not found")
        return None

def get_token_account(ctx,
                      owner: Pubkey.from_string,
                      mint: Pubkey.from_string):
    try:
        account_data = ctx.get_token_accounts_by_owner(owner, TokenAccountOpts(mint))
        return account_data.value[0].pubkey, None
    except:
        swap_associated_token_address = get_associated_token_address(owner, mint)
        swap_token_account_Instructions = create_associated_token_account(owner, owner, mint)
        return swap_associated_token_address, swap_token_account_Instructions

async def data_for_sell(ctx, token_swap, payer, amount=0):
    '''
    Функция подготавливает данные для покупки, ( для отправки транзакции на продажу )
    :param ctx:
    :param pairs:
    :param payer:
    :param amount:
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

        accounts = ctx.get_token_accounts_by_owner_json_parsed(payer.pubkey(),
                                                               TokenAccountOpts(program_id=programid_of_token)).value
        for account in accounts:
            mint_in_acc = account.account.data.parsed['info']['mint']
            if mint_in_acc == str(mint):
                amount_in = int(account.account.data.parsed['info']['tokenAmount']['amount'])
                # print("3.1 Token Balance [Lamports]: ", amount_in)
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
        # print("5. Create Swap Instructions...")
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

    #print(f'[*******]  {(ctx.get_fee_for_message(swap_tx.compile_message()))}')

    output = {
        'swap_tx': swap_tx,
        'payer': payer,
        'Wsol_account_keyPair': None,
        'signers': signers
    }
    return output
async def data_for_buy(ctx, pairs, payer, amount):
    '''
        Функция подготавливает данные для покупки, ( для отправки транзакции на покупку )
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
    print(f'TOKEN ID = {TOKEN_PROGRAM_ID}')

    # 2. Создаем учетную запись токена
    swap_associated_token_address, swap_token_account_Instructions = get_token_account(ctx, payer.pubkey(),
                                                                                       mint)
    # 3.
    # Получаем минимальную сумму ренты
    balance_needed = Token.get_min_balance_rent_for_exempt_for_account(ctx)
    # Создаем обернутый SOL
    WSOL_token_account, swap_tx, payer, Wsol_account_keyPair, opts, = _TokenCore._create_wrapped_native_account_args(
        TOKEN_PROGRAM_ID, payer.
        pubkey(), payer, amount_in,
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

    print(f'payer.pubkey() ={payer.pubkey()}')
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

    output = {
        'swap_tx':swap_tx,
        'payer':payer,
        'Wsol_account_keyPair':Wsol_account_keyPair,
        'signers': None
    }

    return output
async def get_data_for_sell_and_buy(ctx, pairs, payer, amount):
    '''
    Функция запрашивает данные которые будут использоваться для покупки и продажи токенов.
    :param ctx:
    :param pairs:
    :param payer:
    :param amount:
    :return:
    '''
    start = time.time()

    # VARIANT 1
    # 20 ,
    buy_data = await data_for_buy(ctx, pairs, payer, amount)
    #sell_data = await data_for_sell(ctx, pairs, payer, amount=0)

    #
    #buy, sell = asyncio.gather()

    end = time.time()

    print(f'TOTAL TIME = {end-start}')


if __name__ == '__main__':
    # async def main():
    #
    #     # Секретный ключ.
    #     load_dotenv()
    #     s_key = os.getenv('PRIVATE_KEY')
    #     # Готовый формат кошелька для подписи
    #     m_payer = Keypair.from_bytes(base58.b58decode(s_key))
    #
    #     # Создаем экземпляр клиента
    #     ctx = Client(RPC_URL, commitment=Commitment(
    #         "confirmed"), timeout=45, blockhash_cache=True)
    #
    #     pool_id = '96q24zNu1WdoTd3gqjoJnmBJacxdUnrm6q9ubzn3n4xL'
    #     dd = await get_data_for_sell_and_buy(ctx=ctx, pairs=pool_id, payer=m_payer, amount=0.002)
    #
    # asyncio.run(main())
    async def qq():
        # data = await get_pool_keys_for_trans(token='6N69HeS7SxBejvzw6CBs5vwtjhYsfUsMoskAQxCaCtR6')
        # print(data)
        token='Fkht8ygvjqPkdvKmDbTvJ94WXKSyv9JjVNzEGGeHBCop'
        ctx = AsyncClient("https://api.mainnet-beta.solana.com",commitment="confirmed")  # Инициализация асинхронного клиента для взаимодействия с RPC-сервером
        amm_id = Pubkey.from_string(str(token))  # Получение публичного ключа монетной пары пула
        amm_data = (await ctx.get_account_info_json_parsed(amm_id)).value.data  # Получение информации о пуле AMM
        amm_data_decoded = AMM_INFO_LAYOUT_V4_1.parse(amm_data)  # Декодирование информации о пуле AMM
        print(f'amm_data_decoded = {amm_data_decoded}')

        OPEN_BOOK_PROGRAM = Pubkey.from_bytes(amm_data_decoded.serumProgramId)  # Программный ключ для биржи Serum
        marketId = Pubkey.from_bytes(amm_data_decoded.serumMarket)  # Идентификатор рынка
        print(f'SERUM = {marketId}')
        marketInfo = (await ctx.get_account_info_json_parsed(marketId)).value.data  # Получение информации о рынке
        market_decoded = MARKET_LAYOUT.parse(marketInfo)  # Декодирование информации о рынке
        print(f'market_decoded = {market_decoded}')

        # Формирование словаря с ключами для обмена
        pool_keys = {
            "amm_id": amm_id,
            "authority": RAY_AUTHORITY_V4,
            "base_mint": Pubkey.from_bytes(market_decoded.base_mint),
            "base_decimals": amm_data_decoded.coinDecimals,
            "quote_mint": Pubkey.from_bytes(market_decoded.quote_mint),
            "quote_decimals": amm_data_decoded.pcDecimals,
            "lp_mint": Pubkey.from_bytes(amm_data_decoded.lpMintAddress),
            "open_orders": Pubkey.from_bytes(amm_data_decoded.ammOpenOrders),
            "target_orders": Pubkey.from_bytes(amm_data_decoded.ammTargetOrders),
            "base_vault": Pubkey.from_bytes(amm_data_decoded.poolCoinTokenAccount),
            "quote_vault": Pubkey.from_bytes(amm_data_decoded.poolPcTokenAccount),
            "market_id": marketId,
            "market_base_vault": Pubkey.from_bytes(market_decoded.base_vault),
            "market_quote_vault": Pubkey.from_bytes(market_decoded.quote_vault),
            "market_authority": Pubkey.create_program_address(
                [bytes(marketId)]
                + [bytes([market_decoded.vault_signer_nonce])]
                + [bytes(7)],
                OPEN_BOOK_PROGRAM,
            ),
            "bids": Pubkey.from_bytes(market_decoded.bids),
            "asks": Pubkey.from_bytes(market_decoded.asks),
            "event_queue": Pubkey.from_bytes(market_decoded.event_queue),
            "pool_open_time": amm_data_decoded.poolOpenTime,
        }

        print(f'POOL = {pool_keys}')




    asyncio.run(qq())




# def get_token_account(ctx,
#                       owner: Pubkey.from_string,
#                       mint: Pubkey.from_string):
#     '''
#     Функция проверяет и если нету создает "Учетную запись токена"
#     :param ctx:
#     :param owner:
#     :param mint:
#     :return:
#     '''
#     try:
#         account_data = ctx.get_token_accounts_by_owner(owner, TokenAccountOpts(mint))
#         return account_data.value[0].pubkey, None
#     except:
#         swap_associated_token_address = get_associated_token_address(owner, mint)
#         swap_token_account_Instructions = create_associated_token_account(owner, owner, mint)
#
#         return swap_associated_token_address, swap_token_account_Instructions


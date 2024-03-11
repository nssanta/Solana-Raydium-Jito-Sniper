import time
from typing import List
import os
from dotenv import load_dotenv

import click
from solana.rpc.api import Client
from solana.rpc.commitment import Processed
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
#from solana.transaction import Transaction
from spl.memo.instructions import MemoParams, create_memo

from jito_searcher_client.convert import tx_to_protobuf_packet
from jito_searcher_client.generated.bundle_pb2 import Bundle
from jito_searcher_client.generated.searcher_pb2 import (
    ConnectedLeadersRequest,
    MempoolSubscription,
    NextScheduledLeaderRequest,
    NextScheduledLeaderResponse,
    ProgramSubscriptionV0,
    SendBundleRequest,
    WriteLockedAccountSubscriptionV0,
)
from jito_searcher_client.generated.searcher_pb2_grpc import SearcherServiceStub
from jito_searcher_client.searcher import get_searcher_client

from Data.CONSTANT_OF_PROJECT import RPC_URL

load_dotenv()
KP = Keypair.from_base58_string(os.getenv('JITO_KEY'))
BLOCK_ENGINE_URL = "frankfurt.mainnet.block-engine.jito.wtf"
client = get_searcher_client(BLOCK_ENGINE_URL, KP)

# Секретный ключ.
s_key = Keypair.from_base58_string(os.getenv('PRIVATE_KEY'))


import httpx
import asyncio
import datetime
import time

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


    swap_tx_t = []
    #6. Добавляем инструкции к транзакции.
    swap_tx_t.append(set_compute_unit_limit(GAS_LIMIT))
    swap_tx_t.append(set_compute_unit_price(GAS_PRICE))

    if swap_token_account_Instructions != None:
        swap_tx_t.append(swap_token_account_Instructions)
    swap_tx_t.append(instructions_swap)
    swap_tx_t.append(closeAcc)


    # 6. Добавляем инструкции к транзакции.
    #swap_tx.add(set_compute_unit_limit(GAS_LIMIT))
    #swap_tx.add(set_compute_unit_price(GAS_PRICE))
    #
    #if swap_token_account_Instructions != None:
        #swap_tx.add(swap_token_account_Instructions)
    #swap_tx.add(instructions_swap)
    #swap_tx.add(closeAcc)
    

    tip_from_pubkey = payer.pubkey()  # Отправитель чаевых (обычно payer)
    tip_to_pubkey = Pubkey.from_string("3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT")  # Получатель чаевых
    tip_lamports = 1000  # Количество лампортов для перевода
    # Создание инструкции для перевода чаевых
    tip_transfer_instruction = transfer(TransferParams(from_pubkey=tip_from_pubkey, to_pubkey=tip_to_pubkey, lamports=tip_lamports))
    # Добавление инструкции перевода чаевых в транзакцию
    swap_tx_t.append(tip_transfer_instruction)

    blockhash = ctx.get_latest_blockhash().value.blockhash
    tx = Transaction.new_signed_with_payer(
        instructions=swap_tx_t, payer=KP.pubkey(), signing_keypairs=[KP], recent_blockhash=blockhash
    )

    #tx = await execute_tx(swap_tx, payer, Wsol_account_keyPair, None)
    return tx

    # print(f'\n {swap_tx_t} \n')
    # return swap_tx_t
    #return swap_tx_t #.serialize_message() #base58.b58encode(swap_txt.serialize_message())


def send_bundle(
    client: SearcherServiceStub,
    rpc_url: str,
    payer: str,
    message,#: str,
    num_txs: int,
    lamports: int,
    tip_account: str,
):
    """
    Send a bundle!
    """
    #with open(payer) as kp_path:
    payer_kp = Keypair.from_base58_string(payer)
    tip_account = Pubkey.from_string(tip_account)

    rpc_client = Client(rpc_url, commitment=Commitment("finalized"))
    balance = rpc_client.get_balance(payer_kp.pubkey()).value
    print(f"payer public key: {payer_kp.pubkey()} {balance=}")

    is_leader_slot = False
    print("waiting for jito leader...")
    while not is_leader_slot:
        time.sleep(0.5)
        next_leader: NextScheduledLeaderResponse = client.GetNextScheduledLeader(NextScheduledLeaderRequest())
        num_slots_to_leader = next_leader.next_leader_slot - next_leader.current_slot
        print(f"waiting {num_slots_to_leader} slots to jito leader")
        is_leader_slot = num_slots_to_leader <= 2

    blockhash = rpc_client.get_latest_blockhash().value.blockhash
    block_height = rpc_client.get_block_height(Processed).value
    print(f'block_height = {block_height}')

    # Build bundle
    txs: List[Transaction] = []
    for idx in range(num_txs):
        ixs = [
            # create_memo(
            #     MemoParams(
            #         program_id=Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"),
            #         signer=payer_kp.pubkey(),
            #         message=bytes(f"jito bundle {idx}: {message}", "utf-8"),
            #     )
            # )
        ]
        if idx == num_txs - 1:
            # Adds searcher tip on last tx
            
            #for xtr in message:
               # ixs.append(xtr)
                
            ixs.append(
                transfer(TransferParams(from_pubkey=payer_kp.pubkey(), to_pubkey=tip_account, lamports=lamports))
            )


        print(f'itx = {type(ixs)}')
        tx = Transaction.new_signed_with_payer(
            instructions=message, payer=payer_kp.pubkey(), signing_keypairs=[payer_kp], recent_blockhash=blockhash
        )

        
        
        
        # tx= Transaction.new_signed_with_payer(
        #     instructions=message, payer=payer_kp.pubkey(), signing_keypairs=[payer_kp], recent_blockhash=blockhash
        # )
        print(tx)
        #tx.append(ttx)


        print(f"{idx=} signature={tx.signatures[0]}")
        txs.append(tx)

    packets = [tx_to_protobuf_packet(tx) for tx in txs]

    uuid_response = client.SendBundle(SendBundleRequest(bundle=Bundle(header=None, packets=packets)))
    print(f"bundle uuid: {uuid_response.uuid}")

    for tx in txs:
        print(
            rpc_client.confirm_transaction(
                tx.signatures[0], Processed, sleep_seconds=1, last_valid_block_height=block_height + 10
            )
        )

if __name__ == '__main__':
    async def gg ():
        # Секретный ключ.
        s_key = os.getenv('PRIVATE_KEY')
        # Готовый формат кошелька для подписи
        m_payer = Keypair.from_bytes(base58.b58decode(s_key))

        # Создаем экземпляр клиента
        ctx = Client(RPC_URL, commitment=Commitment(
            "finalized"), timeout=50, blockhash_cache=True)

        pool_id = 'FRhB8L7Y9Qq41qZXYLtC2nw8An1RJfLLxRF2x9RwLLMo'

        # Пример использования функции
        transaction = await buy_of_raydium(ctx=ctx, pairs=pool_id, payer=KP, amount=0.002)

        # bb = send_bundle(client= client,rpc_url='https://rpc.shyft.to?api_key=ooAcuBUUvuKkflvP',
        #                  payer=os.getenv('JITO_KEY'),
        #                  message=transaction,num_txs=1,lamports=10000,tip_account='96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5')

    asyncio.run(gg())



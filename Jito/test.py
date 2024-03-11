import asyncio
import os
from dotenv import load_dotenv

from jito_searcher_client import get_async_searcher_client
from jito_searcher_client.generated.searcher_pb2 import ConnectedLeadersRequest, GetTipAccountsRequest, \
    NextScheduledLeaderRequest

from solders.keypair import Keypair

load_dotenv()

# KEYPAIR_PATH = "/path/to/authenticated/keypair.json"
# BLOCK_ENGINE_URL = "frankfurt.mainnet.block-engine.jito.wtf"

kp = Keypair.from_base58_string(os.getenv('JITO_KEY'))
BLOCK_ENGINE_URL = "frankfurt.mainnet.block-engine.jito.wtf"

async def get_leaders():
    '''
    Получаем лидеров и блоки
    :return:
    '''
    client = await get_async_searcher_client(BLOCK_ENGINE_URL, kp)
    leaders = await client.GetConnectedLeaders(ConnectedLeadersRequest())
    print(f"{leaders=}")

    return leaders

async def get_tip():
    '''
    Получаем адресса для чаевых
    :return:
    '''
    client = await get_async_searcher_client(BLOCK_ENGINE_URL, kp)
    accounts = await client.GetTipAccounts(GetTipAccountsRequest())
    print(accounts)

    return accounts

async def next_scheduled_leader():
    '''
    Кто следующий заплонированый лидер
    :return:
    '''
    client = await get_async_searcher_client(BLOCK_ENGINE_URL, kp)
    n_leader = await client.GetNextScheduledLeader(NextScheduledLeaderRequest())
    print(n_leader)


if __name__ == '__main__':
    asyncio.run(next_scheduled_leader())

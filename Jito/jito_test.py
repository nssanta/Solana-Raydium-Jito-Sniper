import asyncio
import os
from dotenv import load_dotenv
from jito_searcher_client import get_async_searcher_client
from jito_searcher_client.generated.searcher_pb2 import ConnectedLeadersRequest
from solders.keypair import Keypair

load_dotenv()

KP = Keypair.from_base58_string(os.getenv('JITO_KEY'))


async def get_leaders(BLOCK_ENGINE_URL = "frankfurt.mainnet.block-engine.jito.wtf"):
    '''
    Функция возвращает
    :param BLOCK_ENGINE_URL:
    :return:
    '''
    client = await get_async_searcher_client(BLOCK_ENGINE_URL, KP)
    leaders = await client.GetConnectedLeaders(ConnectedLeadersRequest())
    print(f"{leaders=}")

if __name__=='__main__':
    asyncio.run(get_leaders())
import asyncio
import datetime
import time
import base58

from solana.rpc.commitment import Commitment
from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient

from SWAP.BuyRaydium import buy_of_raydium
from SWAP.SellRaydium import sell_of_raydium, sell_of_data
from SWAP.Tools.HandlerSwap import data_for_sell
from Scanner.Scan_V1.Scanner_V1 import Scanner_V1
from Scanner.Scan_V1.Scannner_V1_1 import Scanner_V1_1
from Scanner.Handle.RootHandler import do_get_all_data
from Data.CONSTANT_OF_PROJECT import RPC_URL
from Tools.GetPrice import get_price_of_data

async def log_listener(scanner, scanner_queue, semaphor):
    """
    Function to listen for new liquidity pool logs.
    :param scanner: Scanner object instance
    :param scanner_queue: Async queue for communicating transaction data
    :param semaphor: Semaphore to limit concurrent token tracking
    :return: None
    """
    while True:
        # Subscribe and wait for new pool data
        data = await scanner.subscribe_programm('675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8')
        print(f'data = {data}')
        
        if data is not None:
            # Fetch full transaction details
            data_of_trans = await do_get_all_data(data)

            # Check if we have reached the limit of concurrent tracked tokens
            if semaphor.locked():
                print(f"[{datetime.datetime.now()}] Max tracked tokens reached. Skipping.")
                continue
            else:
                # Add transaction data to the queue for the consumer
                await scanner_queue.put(data_of_trans)
                print(f'scanner_queue = {scanner_queue}')

async def dealer_token(scanner_queue, semaphor):
    """
    Consumer function that buys tokens, monitors price, and sells.
    :param scanner_queue: Queue containing new token data
    :param semaphor: Semaphore for concurrency control
    :return: None
    """
    async with semaphor:
        temp_list = []
        while True:
            # Retrieve data from the queue
            data = await scanner_queue.get()

            if data != None:
                temp_list.append(data)

            if temp_list:
                for item in temp_list:
                    start_price = await get_price_of_data(item)
                    print(start_price)
                    # Small delay between checks
                    await asyncio.sleep(0.1)
            
            await asyncio.sleep(0.5)

async def main():
    """
    Main entry point for the asynchronous sniper bot.
    Initializes the scanner, queue, and semaphore, then gathers tasks.
    :return: None
    """
    scanner = Scanner_V1_1()
    scanner.run_websocket = True
    
    # Initialize async queue and semaphore (limit 3 concurrent tokens)
    scanner_queue = asyncio.Queue()
    semaphor = asyncio.Semaphore(3)

    # Run producer (listener) and consumer (dealer) concurrently
    await asyncio.gather(
        log_listener(scanner, scanner_queue, semaphor),
        dealer_token(scanner_queue, semaphor)
    )

if __name__ == '__main__':
    asyncio.run(main())
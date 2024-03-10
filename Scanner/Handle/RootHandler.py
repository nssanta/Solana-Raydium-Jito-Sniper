import asyncio
import datetime
import time

from Data.CONSTANT_OF_PROJECT import RPC_URL
from Testing_Code.HandledData.getTransactions import get_transaction, save_json
from Testing_Code.HandledData.parserAccountInfo import get_programm_data
from Scanner.Handle.parserTransactions import find_instructio_by_programId

def merge_data(trans_data, program_data):
    '''
    Функция объеденияет данные и возвращает общие данные
    :param trans_data: Данные транзакции
    :param program_data: Данные программы
    :return:
    '''
    try:
        # Добавляемм данные в первый словарь где больше данных
        trans_data['marketBaseVault'] = program_data['base_vault']
        trans_data['marketQuoteVault'] = program_data['quote_vault']
        trans_data['marketBids'] = program_data['bids_']
        trans_data['marketAsks'] = program_data['asks_']
        trans_data['marketEventQueue'] = program_data['event_queue']
        # Возвращаем данные
        return trans_data
    except Exception as e:
        print(f'[{datetime.datetime.now()}] Ошибка в функции merge_data : {e}')
        return None




async def do_get_all_data(data_sign,rpc=RPC_URL):
    '''
    Функция выполняет комплект процедур и получает все данные иницилизации пула
    :param data_sign:
    :return:
    '''
    try:
        ll = True

        while ll:

            print(f'[{datetime.datetime.now()}] Запрашиваю транзакцию!')
            # Получаем данные транзакции
            transaction_data = await get_transaction(data_sign,rpc)
            if transaction_data['result'] != 'null' and transaction_data['result'] != None :
                ll = False
                break

        # Получаем информацию из транзакции
        data_of_trans = find_instructio_by_programId(transaction_data)

        all_data = data_of_trans
        #print(f'[{datetime.datetime.now()}] {data_of_trans}')

        # Получаем данные программы
        # prog_data = await get_programm_data(data_of_trans['marketId'])
        # # Объединяем данные
        # all_data = merge_data(trans_data= data_of_trans, program_data=prog_data)

        return all_data

    except Exception as e:
        print(f'[{datetime.datetime.now()}] Ошибка в функции do_get_all_data : {e}')
        return None


if __name__ == '__main__':
    pass
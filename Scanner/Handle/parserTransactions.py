import json
import re

import base58
import datetime

RPC_ENDPOINT = 'https://api.mainnet-beta.solana.com'
RAYDIUM_POOL_V4_PROGRAM_ID = '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8'
SERUM_OPENBOOK_PROGRAM_ID = 'srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX'
SOL_MINT = 'So11111111111111111111111111111111111111112'
SOL_DECIMALS = 9

def mainn():
    with open('../trans2.json', 'r') as file:
        data = json.load(file)
        return data

def find_base_mint(instructions, program_id):
    '''
    Получаем данные публичных ключей
    :param data:
    :return:
    '''
    try:
        # Ищем инструкцию где был создан токен с помощью переданного пула.
        for item in instructions:
            if ('programId' in item) and (item['programId'] == program_id):
                output = {
                    'poolId': item['accounts'][4],    # Это айди пула монет.
                    'baseMint': item['accounts'][8],  # Это публичный ключ (Public Key) монеты базового актива
                    'baseVault': item['accounts'][10],  # Это публичный ключ хранилища (Vault) для монеты базового актива
                    'quoteMint': item['accounts'][9],  # Это публичный ключ монеты котировки
                    'quoteVault': item['accounts'][11],  # Это публичный ключ хранилища для монеты котировки
                    'lpMint': item['accounts'][7],  # Это публичный ключ монеты ликвидности
                    'marketProgramId': item['accounts'][15],
                    'marketId': item['accounts'][16],
                    'marketVersion': 3,
                    'withdrawQueue': '11111111111111111111111111111111',
                    'programId': RAYDIUM_POOL_V4_PROGRAM_ID,
                    'version': 4,
                    'authority': item['accounts'][5],
                    'openOrders': item['accounts'][6],
                    'targetOrders': item['accounts'][13],

                }
                return output

        print(f'[{datetime.datetime.now()}] Функция find_base_mint : Данные не были найдены возвращенно None!')
        return None

    except Exception as e:
        print(f'[{datetime.datetime.now()}] Ошибка в функции find_base_mint : {e}')

def find_mint_inner_instructions_by_mintaddress(data, mint_address):
    '''
    Данные инструкци инициализации монеты (минта)
    :param data:
    :return:
    '''
    try:
        # Берем данные методанных для поиска нужной нам инструкции
        meta = data['result']['meta']['innerInstructions'][0]['instructions']
        # Цикл для поиска данных
        for item in meta:
            # Проверяем наличее ключей
            if('parsed' in item) and ('type' in item['parsed']) and ('info' in item['parsed']) and ('mint' in item['parsed']['info']):
                # Проверяем наша ли инструкция по монетному ключу
                if (item['parsed']['type']=='mintTo') and (item['parsed']['info']['mint'] == mint_address):
                    # Возвращаем данные
                    data = {
                        'lpVault': item['parsed']['info']['account'],
                        'lpReserve': item['parsed']['info']['amount']
                    }
                    return data

        print(f'[{datetime.datetime.now()}] Функция find_mint_inner_instructions_by_mintaddress : Данные не были найдены возвращенно None!')
        return None

    except Exception as e:
        print(f'[{datetime.datetime.now()}] Ошибка в функции find_mint_inner_instructions_by_mintaddress : {e}')

def find_initialize_mint_inner_instructions_by_mintaddress(data, mint_address):
    '''
    Данные инструкци инициализации монеты
    :param data:
    :return:
    '''
    try:
        # Берем данные методанных для поиска нужной нам инструкции
        meta = data['result']['meta']['innerInstructions'][0]['instructions']
        # Цикл для поиска данных
        for item in meta:
            # Проверяем наличее ключей
            if('parsed' in item) and ('type' in item['parsed']) and ('info' in item['parsed']) and ('mint' in item['parsed']['info']):
                # Проверяем наша ли инструкция по монетному ключу
                if (item['parsed']['type']=='initializeMint') and (item['parsed']['info']['mint'] == mint_address):
                    # Возвращаем инструкцию
                    return item['parsed']['info']['decimals']

        print(f'[{datetime.datetime.now()}] Функция find_initialize_mint_inner_instructions_by_mintaddress : Данные не были найдены возвращенно None!')
        return None

    except Exception as e:
        print(f'[{datetime.datetime.now()}] Ошибка в функции find_initialize_mint_inner_instructions_by_mintaddress : {e}')

def find_transfer_tnstruction_ininner_instructions_by_destination(data, account, program_id):
    '''
    Функция для поиска передачи токенов
    :param data:
    :param account: аккаунт передачи
    :param program_id: кому передал
    :return:
    '''
    try:
        meta = data['result']['meta']['innerInstructions'][0]['instructions']
        # Цикл для поиска данных
        for item in meta:
        # Проверяем наличее ключей
            if ('parsed' in item) and ('type' in item['parsed']) and ('info' in item['parsed']) and ('destination' in item['parsed']['info']):
                # Проверяем условие
                if (item['parsed']['type'] == 'transfer') and (item['parsed']['info']['destination'] == account):
                    if program_id != None:
                        if item['programId'] == program_id:
                            if 'amount' in item['parsed']['info']:
                                return item['parsed']['info']['amount']
                    else:
                        if 'amount' in item['parsed']['info']:
                            return item['parsed']['info']['amount']

        print(f'[{datetime.datetime.now()}] Функция find_transfer_tnstruction_ininner_instructions_by_destination : Данные не были найдены возвращенно None!')
        return None

    except Exception as e:
        print(f'[{datetime.datetime.now()}] Ошибка в функции find_transfer_tnstruction_ininner_instructions_by_destination : {e}')

def extract_lp_initialization_log_entry_info_from_log_entry(data, first_string = 'Program log: initialize2: InitializeInstruction2'):
    '''
    Функция ищет данные иницилизации из логов
    :param data:
    :param first_string:
    :return:
    '''
    try:
        # Получаем все логи (список)
        log_info = data['result']['meta']['logMessages']
        # Ищем по списку начало нашей строки
        for item in log_info:
            if item.startswith(first_string):

                # Используем регулярное выражение для извлечения данных в фигурных скобках
                data_string = re.search(r'{(.+?)}', item).group(1)
                # Удаляем лишние пробелы
                data_string = data_string.strip()
                # Разбиваем строку по запятым и создаем список пар ключ-значение
                key_value_pairs = [pair.strip().split(':') for pair in data_string.split(',')]
                # Создаем словарь из списка пар ключ-значение
                data_dict = {key.strip(): eval(value.strip()) for key, value in key_value_pairs}
                # Возвращаем полученный словарь
                return data_dict

        print(f'[{datetime.datetime.now()}] Функция extract_lp_initialization_log_entry_info_from_log_entry : Данные не были найдены возвращенно None!')
        return None

    except Exception as e:
        print(f'[{datetime.datetime.now()}] Ошибка в функции extract_lp_initialization_log_entry_info_from_log_entry : {e}')

def find_pre_balance_token(data, coin):
    '''
    Ищет предварительный баланс токена
    :param data: данные транзакции
    :param coin: монета
    :return:
    '''
    try:
        meta = data['result']['meta']['preTokenBalances']
        # Цикл для поиска данных
        for item in meta:
            # Проверяем наличее ключей
            if item['mint'] == coin:
                if 'uiTokenAmount' in item:
                    ui_token = item['uiTokenAmount']

                    return ui_token

        print(f'[{datetime.datetime.now()}] Функция find_pre_balance_token : Данные не были найдены возвращенно None!')
        return None

    except Exception as e:
        print(f'[{datetime.datetime.now()}] Ошибка в функции find_pre_balance_token : {e}')

def find_instructio_by_programId(data, program_id ='675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8'):
    '''
    Функция находит данные токена который был залистен
    :param data: данные
    :param program_id: ид программы , пула где он должен был появиться
    :return:
    '''
    try:
        # Данные для возвращения
        output = {}
        # Данные по которым нужно итерировать.
        instructions = data['result']['transaction']['message']['instructions']
        # Получаем данные публичных ключей монет
        output = find_base_mint(instructions, program_id)

        # # Сохраняем все данные в файл
        # with open('save_full_data.json', 'a') as file:
        #     json.dump(data, file, indent=4)
        #     file.write('\n')

        # Получаем и добавляем количество знаков
        inner = find_initialize_mint_inner_instructions_by_mintaddress(data, output['lpMint'])
        if inner!=None:
            output['lpDecimals'] = inner

        # Получаем и добавляем пул ликвидности и кол-во
        mint = find_mint_inner_instructions_by_mintaddress(data, output['lpMint'])
        if mint!=None:
            output.update(mint)

        # Получаем и добавляем даные перевода
        base_transfer_instruction = find_transfer_tnstruction_ininner_instructions_by_destination(data, output['baseVault'], None)
        quote_transfer_instruction = find_transfer_tnstruction_ininner_instructions_by_destination(data, output['quoteVault'], None)
        if base_transfer_instruction != None:
            output['baseReserve'] = base_transfer_instruction
        if quote_transfer_instruction != None:
            output['quoteReserve'] = quote_transfer_instruction

        # Получам данные с логов, время итд
        extract = extract_lp_initialization_log_entry_info_from_log_entry(data=data)
        if extract != None and 'open_time' in extract:
            data_time = datetime.datetime.fromtimestamp(int(extract['open_time']))
            str_time = data_time.strftime("%Y-%m-%d %H:%M:%S")
            output['openTime'] = str_time

        # Получаем данные которые должны быть кол-во знаков базовой монеты
        pre_balance_all = find_pre_balance_token(data, output['baseMint'])
        pre_balance = pre_balance_all['decimals']


        # Определяем количество десятичных знаков для базовой и котируемой монет
        base_and_quote = output['baseMint'] == SOL_MINT
        base_decimals = SOL_DECIMALS if base_and_quote else pre_balance
        quote_decimals = pre_balance if base_and_quote else SOL_DECIMALS
        output['baseDecimals'] = base_decimals
        output['quoteDecimals'] = quote_decimals

        return output
    except Exception as e:
        print(f'[{datetime.datetime.now()}] Ошибка в функции find_instructio_by_programId : {e}')


if __name__ == '__main__':
    a = mainn()
    aa = find_instructio_by_programId(data=a)
    print(aa)
    # pr = a['result']['meta']['innerInstructions'][0]['instructions']
    # for x in pr:
    #     print(x,'\n')
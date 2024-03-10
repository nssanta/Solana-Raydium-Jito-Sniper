import httpx
import base64
import json


# Определите метод для получения стоимости сообщения с использованием метода RPC getFeeForMessage
def get_fee_for_message(transaction, commitment='processed', min_context_slot=None):
    # Кодируйте транзакцию в base64
    transaction_base64 = base64.b64encode(transaction).decode('utf-8')

    # Подготовьте данные для запроса
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getFeeForMessage",
        "params": [
            transaction_base64,
            {
                "commitment": commitment
            }
        ]
    }

    # Включите minContextSlot, если он предоставлен
    if min_context_slot is not None:
        payload['params'][1]['minContextSlot'] = min_context_slot

    # Отправьте запрос к RPC-серверу Solana
    response = httpx.post('https://api.mainnet-beta.solana.com', json=payload)
    print(response)
    # Разберите ответ
    response_data = response.json()
    print(response_data)

    # Верните стоимость, если она доступна
    if 'result' in response_data and 'value' in response_data['result']:
        return response_data['result']['value']
    else:
        raise Exception("Не удалось получить стоимость сообщения")

if __name__ == '__main__':
    # Пример использования:
    # Предполагая, что `transaction_data` - это сырые данные транзакции
    transaction_data = b'...' # Замените на ваши данные транзакции
    fee = get_fee_for_message(transaction_data)
    print(f"Стоимость транзакции: {fee} лампортов")

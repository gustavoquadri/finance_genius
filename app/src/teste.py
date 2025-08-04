import requests
from collections import OrderedDict
from decimal import Decimal
import time


def get_all_crypto(currency='brl', max_per_batch=250):

    ids_url = "https://api.coingecko.com/api/v3/coins/list"
    ids_response = requests.get(ids_url)
    ids_response.raise_for_status()
    all_coins = ids_response.json()

    coin_ids = [coin['id'] for coin in all_coins]

    batches = [coin_ids[i:i + max_per_batch] for i in range(0, len(coin_ids), max_per_batch)]

    result = OrderedDict()
    for batch in batches:
        ids_batch = ','.join(batch)
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': ids_batch,
            'vs_currencies': currency,
            'include_market_cap': 'true',
            'include_24hr_vol': 'true',
            'include_24hr_change': 'true',
            'include_last_updated_at': 'true'
        }

        response = requests.get(url, params=params)
        if response.status_code == 429:
            print("Rate limit exceeded, sleeping...")
            time.sleep(10)
            continue

        response.raise_for_status()
        data = response.json()

        for crypto_id in data:

            valor_mercado = Decimal(str(data[crypto_id].get(f'{currency}_market_cap', 0)))
            valor_volume_24h = Decimal(str(data[crypto_id].get(f'{currency}_24h_vol', 0)))
            valor_variacao_percentual = Decimal(str(data[crypto_id].get(f'{currency}_24h_change', 0)))
            valor_ultima_att = Decimal(str(data[crypto_id].get('last_updated_at', 0)))

            result[crypto_id.capitalize()] = {
                'Valor Mercado': valor_mercado,
                'Valor 24h': valor_volume_24h,
                'Valor Variacao': valor_variacao_percentual,
                'Valor Ultima ATT': valor_ultima_att
            }

        time.sleep(1.2)

    return result


def get_selected_crypto(cryptos, currency='brl', max_per_batch=250):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': cryptos,
        'vs_currencies': currency,
        'include_market_cap': 'true',
        'include_24hr_vol': 'true',
        'include_24hr_change': 'true',
        'include_last_updated_at': 'true'
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    result = OrderedDict()

    for crypto_id in data:

        valor_mercado = Decimal(str(data[crypto_id].get(f'{currency}_market_cap', 0)))
        valor_volume_24h = Decimal(str(data[crypto_id].get(f'{currency}_24h_vol', 0)))
        valor_variacao_percentual = Decimal(str(data[crypto_id].get(f'{currency}_24h_change', 0)))
        valor_ultima_att = Decimal(str(data[crypto_id].get('last_updated_at', 0)))

        result[crypto_id.capitalize()] = {
            'Valor Mercado': valor_mercado,
            'Valor 24h': valor_volume_24h,
            'Valor Variacao': valor_variacao_percentual,
            'Valor Ultima ATT': valor_ultima_att
        }
    return result


if __name__ == '__main__':
    result_crypto = get_selected_crypto(cryptos=['bitcoin'])
    print(result_crypto)

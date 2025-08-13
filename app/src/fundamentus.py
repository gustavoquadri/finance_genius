import re
import urllib.request
import urllib.parse
import http.cookiejar
import requests
from lxml.html import fragment_fromstring
from lxml import html
from collections import OrderedDict
from decimal import Decimal


class FundamentusScraper:
    def __init__(self):
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))
        self.opener.addheaders = [
            ('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201'),
            ('Accept', 'text/html, text/plain, text/css, text/sgml, */*;q=0.01')
        ]


def get_stocks(*args, **kwargs):
    url_stocks = 'http://www.fundamentus.com.br/resultado.php'
    opener = FundamentusScraper()

    data = {
        'negociada': 'ON,PN',
        'ordem': '1'
    }

    with opener.opener.open(url_stocks, urllib.parse.urlencode(data).encode('UTF-8')) as link:
        content = link.read().decode('ISO-8859-1')

    pattern = re.compile('<table id="resultado".*</table>', re.DOTALL)
    content = re.findall(pattern, content)[0]
    page = fragment_fromstring(content)
    result = OrderedDict()

    for rows in page.xpath('tbody')[0].findall("tr"):
        result.update({rows.getchildren()[0][0].getchildren()[0].text: {'Papel': rows.getchildren()[0].text, 'Cotacao': todecimal(rows.getchildren()[1].text), 'Div.Yield': todecimal(rows.getchildren()[5].text), 'P/VP': todecimal(rows.getchildren()[3].text)}})

    return result


def get_reits(*args, **kwargs):

    url_reits = 'https://www.fundamentus.com.br/fii_resultado.php'
    opener = FundamentusScraper()

    data = {
        'ordem': '1'
    }

    with opener.opener.open(url_reits, urllib.parse.urlencode(data).encode('UTF-8')) as link:
        content = link.read().decode('ISO-8859-1')

    pattern = re.compile('<table id="tabelaResultado".*</table>', re.DOTALL)
    content = re.findall(pattern, content)[0]
    page = fragment_fromstring(content)
    result = OrderedDict()

    for rows in page.xpath('tbody')[0].findall("tr"):
        result.update({rows.getchildren()[0][0].getchildren()[0].text: {'Papel': rows.getchildren()[0].text, 'Cotacao': todecimal(rows.getchildren()[2].text), 'Div.Yield': todecimal(rows.getchildren()[4].text), 'P/VP': todecimal(rows.getchildren()[5].text)}})

    return result


def get_treasuries(*args, **kwargs):
    url = 'https://www.tesourodireto.com.br/json/br/com/b3/tesourodireto/service/api/treasurybondsinfo.json'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': 'https://www.tesourodireto.com.br/titulos/precos-e-taxas.htm'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    titulos = data['response']['TrsrBdTradgList']
    result = OrderedDict()

    for item in titulos:
        nome = item['TrsrBd']['nm']

        vencimento = str(item['TrsrBd'].get('mtrtyDt', 0))
        taxa_compra = Decimal(str(item['TrsrBd'].get('anulInvstmtRate', 0)))
        inv_minimo = Decimal(str(item['TrsrBd'].get('minInvstmtAmt', 0)))
        preco_unit = Decimal(str(item['TrsrBd'].get('untrInvstmtVal', 0)))
        pu_resgate = Decimal(str(item['TrsrBd'].get('untrRedVal', 0)))
        rent_anual = Decimal(str(item['TrsrBd'].get('anulRedRate', 0)))

        result[nome] = {
            'Vencimento': vencimento,
            'Taxa de Compra': taxa_compra,
            'Investimento Minimo': inv_minimo,
            'Preco Unitario': preco_unit,
            'Preco Venda Antes Da Hora': pu_resgate,
            'Rentabilidade Anual': rent_anual
        }

    return result


def todecimal(string):
    string = string.replace('.', '')
    string = string.replace(',', '.')

    if (string.endswith('%')):
        string = string[:-1]
        return Decimal(string) / 100
    else:
        return Decimal(string)


def get_stock_details(papel, *args, **kwarg):
    url = f'https://www.fundamentus.com.br/detalhes.php?papel={papel}'

    opener = FundamentusScraper()

    with opener.opener.open(url) as response:
        html_content = response.read().decode('ISO-8859-1')

    page = html.fromstring(html_content)
    details = {}

    try:
        tables = page.xpath('//table[@class="w728"]')
        if tables:
            table_info = tables[0]
            rows_table_info = table_info.findall('.//tr')
            details['Empresa'] = rows_table_info[2].findall('td')[1].text_content().strip()
            details['Setor'] = rows_table_info[3].findall('td')[1].text_content().strip()
            details['SubSetor'] = rows_table_info[4].findall('td')[1].text_content().strip()
            details['Min_52_Sem'] = rows_table_info[2].findall('td')[3].text_content().strip()
            details['Max_52_Sen'] = rows_table_info[3].findall('td')[3].text_content().strip()

            table_oscilacoes_indicadores = tables[2]
            rows_table_oscilacoes_indicadores = table_oscilacoes_indicadores.findall('.//tr')
            details['Var_Dia'] = rows_table_oscilacoes_indicadores[1].findall('td')[1].text_content().strip()
            details['Var_Mes'] = rows_table_oscilacoes_indicadores[2].findall('td')[1].text_content().strip()
            details['Var_30Dias'] = rows_table_oscilacoes_indicadores[3].findall('td')[1].text_content().strip()
            details['Var_12Mes'] = rows_table_oscilacoes_indicadores[4].findall('td')[1].text_content().strip()
            details['Var_Ano'] = rows_table_oscilacoes_indicadores[5].findall('td')[1].text_content().strip()

            details['P/L'] = rows_table_oscilacoes_indicadores[1].findall('td')[3].text_content().strip()
            details['P/VP'] = rows_table_oscilacoes_indicadores[2].findall('td')[3].text_content().strip()
            details['P/EBIT'] = rows_table_oscilacoes_indicadores[3].findall('td')[3].text_content().strip()
            details['PSR'] = rows_table_oscilacoes_indicadores[4].findall('td')[3].text_content().strip()
            details['P/Ativos'] = rows_table_oscilacoes_indicadores[5].findall('td')[3].text_content().strip()
            details['P/Cap. Giro'] = rows_table_oscilacoes_indicadores[6].findall('td')[3].text_content().strip()
            details['P/Ativ Cir Liq'] = rows_table_oscilacoes_indicadores[7].findall('td')[3].text_content().strip()
            details['Div. Yield'] = rows_table_oscilacoes_indicadores[8].findall('td')[3].text_content().strip()
            details['EV/EBITDA'] = rows_table_oscilacoes_indicadores[9].findall('td')[3].text_content().strip()
            details['EV/EBIT'] = rows_table_oscilacoes_indicadores[10].findall('td')[3].text_content().strip()

            details['LPA'] = rows_table_oscilacoes_indicadores[1].findall('td')[5].text_content().strip()
            details['VPA'] = rows_table_oscilacoes_indicadores[2].findall('td')[5].text_content().strip()
            details['Marg. Bruta'] = rows_table_oscilacoes_indicadores[3].findall('td')[5].text_content().strip()
            details['Marg. EBIT'] = rows_table_oscilacoes_indicadores[4].findall('td')[5].text_content().strip()
            details['Marg. Liquida'] = rows_table_oscilacoes_indicadores[5].findall('td')[5].text_content().strip()
            details['EBIT/Ativo'] = rows_table_oscilacoes_indicadores[6].findall('td')[5].text_content().strip()
            details['ROIC'] = rows_table_oscilacoes_indicadores[7].findall('td')[5].text_content().strip()
            details['ROE'] = rows_table_oscilacoes_indicadores[8].findall('td')[5].text_content().strip()
            details['Giro Ativos'] = rows_table_oscilacoes_indicadores[11].findall('td')[5].text_content().strip()

    except Exception as e:
        print(f'Erro ao extrair dados de {papel}: {e}')

    return details


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

    result_stocks = get_stocks()

    result_reits = get_reits()

    result_treasuries = get_treasuries()

    print(f"tesouro ipca+ com juros semestrais 2035: \n\
preco:  {result_treasuries['Tesouro IPCA+ com Juros Semestrais 2035']['Preco Unitario']}\n\
rentabilidade: {result_treasuries['Tesouro IPCA+ com Juros Semestrais 2035']['Rentabilidade Anual']}")
    print("\n")
    print(f"petrobras: \n\
papel: {result_stocks['PETR4']['Papel']}\n\
cotacao: {result_stocks['PETR4']['Cotacao']}\n\
div.yield: {result_stocks['PETR4']['Div.Yield']}\n\
dividendo: {(float(result_stocks['PETR4']['Div.Yield']) * float(result_stocks['PETR4']['Cotacao']))/12}\n\
p/vp: {result_stocks['PETR4']['P/VP']}")
    print("\n")
    print(f"kncr11: \n\
papel: {result_reits['KNCR11']['Papel']}\n\
cotacao: {result_reits['KNCR11']['Cotacao']}\n\
div.yield: {result_reits['KNCR11']['Div.Yield']}\n\
dividendo: {(float(result_reits['KNCR11']['Div.Yield']) * float(result_reits['KNCR11']['Cotacao']))/12}\n\
p/vp: {result_reits['KNCR11']['P/VP']}")

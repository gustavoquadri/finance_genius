import re
import urllib.request
import urllib.parse
import http.cookiejar
import requests
from lxml.html import fragment_fromstring
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
        result.update({rows.getchildren()[0][0].getchildren()[0].text: {'Cotacao': todecimal(rows.getchildren()[1].text), 'Div.Yield': todecimal(rows.getchildren()[5].text), 'P/VP': todecimal(rows.getchildren()[3].text)}})

    return result


def get_reits(*args, **kwargs):

    url_reits = 'https://www.fundamentus.com.br/fii_resultado.php'  # url para fii
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
        result.update({rows.getchildren()[0][0].getchildren()[0].text: {'Cotacao': todecimal(rows.getchildren()[2].text), 'Div.Yield': todecimal(rows.getchildren()[4].text), 'P/VP': todecimal(rows.getchildren()[5].text)}})

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


if __name__ == '__main__':

    result_stocks = get_stocks()

    result_reits = get_reits()

    result_treasuries = get_treasuries()

    print(f"tesouro ipca+ com juros semestrais 2035: \n\
preco:  {result_treasuries['Tesouro IPCA+ com Juros Semestrais 2035']['Preco Unitario']}\n\
rentabilidade: {result_treasuries['Tesouro IPCA+ com Juros Semestrais 2035']['Rentabilidade Anual']}")
    print("\n")
    print(f"petrobras: \n\
cotacao: {result_stocks['PETR4']['Cotacao']}\n\
div.yield: {result_stocks['PETR4']['Div.Yield']}\n\
dividendo: {(float(result_stocks['PETR4']['Div.Yield']) * float(result_stocks['PETR4']['Cotacao']))/12}\n\
p/vp: {result_stocks['PETR4']['P/VP']}")
    print("\n")
    print(f"kncr11: \n\
cotacao: {result_reits['KNCR11']['Cotacao']}\n\
div.yield: {result_reits['KNCR11']['Div.Yield']}\n\
dividendo: {(float(result_reits['KNCR11']['Div.Yield']) * float(result_reits['KNCR11']['Cotacao']))/12}\n\
p/vp: {result_reits['KNCR11']['P/VP']}")

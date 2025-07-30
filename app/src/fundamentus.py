import re
import urllib.request
import urllib.parse
import http.cookiejar
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
    url_stocks = 'http://www.fundamentus.com.br/resultado.php'  # url para ação
    opener = FundamentusScraper()  # simula um navegador, irá guardar os cookies do site

    # filtro para busca, não é 100% necessário, diminui o raio caso queira algo mais especifico
    data = {
        'negociada': 'ON,PN',  # inclui ações ordinárias e preferenciais
        'ordem': '1'           # mantém a ordem padrão
    }

    with opener.opener.open(url_stocks, urllib.parse.urlencode(data).encode('UTF-8')) as link:  # faz a conexão com o site
        content = link.read().decode('ISO-8859-1')  # guarda o resultado em uma variavel

    # compula um padrao de expressao regular, procura no HTML uma tabela id="resultado", pega qualquer caractere, até encontrar o final da tabela (</table>) e o re.DOTALL captura as quebras de linha
    pattern = re.compile('<table id="resultado".*</table>', re.DOTALL)
    # procura todas as ocorrencias do pattern no content
    content = re.findall(pattern, content)[0]
    # converte o html para uma string
    page = fragment_fromstring(content)
    # cria o dicionario que irá armazenar o conteudo final
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

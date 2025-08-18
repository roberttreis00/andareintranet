'''
SKUS e MARCAS

API Tiny que consulta PESQUISANDO e retorna todos os skus e produtos cadastrados

BASE:
Lista de MARCAS OK
LISTA de MARCAS com todos os skus para colocar na sugestão de compras mesmo não tendo
vendas naquele periodo desejado

Sugestão de Compras por Periodo de 1 a 3 Meses coloca-se os Produto Ativos
Já o Programada Semestral Ativos e Excluidos
'''
from pprint import pprint
import requests

Marcas = ['sem marca', 'actvitta', 'azaléia', 'beira rio', 'beira-rio', 'boaonda', 'bottero', 'br sport', 'cartago',
          'coca cola', 'comfortflex', 'dakota', 'democrata', 'fila', 'grendene', 'hidrolight', 'klin', 'kolosh', 'lupo',
          'modare', 'moleca', 'molekinha', 'molekinho', 'mormaii', 'new balance', 'olympikus', 'qix', 'ramarim',
          'rider', 'sua cia', 'supercap', 'terra e água', 'umbro', 'via marte', 'vizzano', 'west coast', 'zaxy',
          'zaxynina']

url_api = 'https://api.tiny.com.br/api2/produtos.pesquisa.php'
TOKEN = "4d907ba2ee45f9e572b9a774badf06f6abde0ae8869c594cb948040ffb4a0544"

# Pesquisa o número de paginas
def numero_paginas_atual(search_marca):
    params = {
        'token': TOKEN,
        'formato': 'json',
        'pesquisa': search_marca,
        'pagina': 1,
    }

    response = requests.get(url_api, params=params).json()['retorno']
    numero_paginas = response['numero_paginas']

    return numero_paginas


# Pesquisa na API do Tiny a MARCA e retorna todos os SKUS em uma lista/ Pega tanto sku pai quanto filho
def pesquisar_marca_get_all(search_marca):
    qtd_pgs = numero_paginas_atual(search_marca)
    data = []

    for pg in range(1, qtd_pgs + 1):
        params = {
            'token': TOKEN,
            'formato': 'json',
            'pesquisa': search_marca,
            'pagina': pg,
        }

        response = requests.get(url_api, params=params).json()['retorno']['produtos']
        for produto in response:
            sku_produto = produto['produto']['codigo']
            data.append(sku_produto)

    return data

# Testar e verificar se pega tudo de todas as marcas
pprint(pesquisar_marca_get_all(''))

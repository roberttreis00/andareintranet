import requests
import re

TOKEN = "4d907ba2ee45f9e572b9a774badf06f6abde0ae8869c594cb948040ffb4a0544"
url_api = 'https://api.tiny.com.br/api2/produtos.pesquisa.php'

# Pesquisa o número de paginas
def numero_paginas_atual(search_marca):
    params = {
        'token': TOKEN,
        'formato': 'json',
        'pesquisa': search_marca,
        'pagina': 1,
    }

    response = requests.get(url_api, params=params).json()['retorno']
    try:
        numero_paginas = response['numero_paginas']
    except KeyError:
        print(f'A Marca "{search_marca}" não retornou nada')
        numero_paginas = 0
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

# Função que extrair o sku pai do sku filho passado
def extrair_sku_pai(sku_filho):
    """Extrai o agrupador do código do produto, removendo cor/tamanho."""
    opcao1 = re.match(r"^([A-Za-z0-9]*?)(C.*)?$", sku_filho)  # Separa por C
    opcao2 = re.match(r"^([A-Za-z0-9]+?)([A-Z]+.*)?$", sku_filho)  # Separa por NOME da COR
    opcao3 = re.match(r"^([A-Za]+[z0-9]+)", sku_filho)  # Separa por COR Abreviada

    retorno1 = opcao1.group(1) if opcao1 else sku_filho
    retorno2 = opcao2.group(1) if opcao2 else sku_filho
    retorno3 = opcao3.group(1) if opcao3 else sku_filho

    qtd_caracteres1, qtd_caracteres2, qtd_caracteres3 = len(retorno1), len(retorno2), len(retorno3)

    # Logica que atende os formatados dos SKUs
    if qtd_caracteres2 < qtd_caracteres1 and qtd_caracteres2 != 1 and qtd_caracteres2 == qtd_caracteres3:
        sku_agrupador = retorno1
    else:
        sku_agrupador = retorno2

    if qtd_caracteres1 == 0 and qtd_caracteres2 == 1:
        sku_agrupador = retorno3
    elif qtd_caracteres1 == qtd_caracteres2 and qtd_caracteres3 > qtd_caracteres2:
        sku_agrupador = retorno1

    # Skus que tem que ser a OPÇÂO 3 eliminando os casos da Umbro, Fila que começa com R
    if qtd_caracteres2 == 1 and qtd_caracteres3 < qtd_caracteres1 or qtd_caracteres2 == qtd_caracteres3:
        if retorno3.startswith('R'):
            sku_agrupador = retorno1
        else:
            sku_agrupador = retorno3

    return sku_agrupador
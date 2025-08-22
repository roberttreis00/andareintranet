import re

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

# Nova forma de extrair agrupador dos skus:
"""
Temos esses tipos de SKU:
4841103 4841103CINZA34 = SKU PAI | COR ESCRITA "CINZA" | TAMANHO
ARMPC224 ARMPC224ARAMIS38 = SKUS PAI | MARCA | TAMANHO
18530 R18530CAE037T33E34 = LETRA R | SKU PAI | COR LETRAS E NÚMEROS | A LETRA T E TAMANHO
1319 R1319258C003T35E36 = LETRA R | SKU PAI | CODIGO | COR C003 | A LETRA T TAMANHO
"""

print(extrair_sku_pai(''))

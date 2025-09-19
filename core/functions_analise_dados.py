from .models import ProdutosCadastradosTiny, ProdutosAtivosTiny, Pedidos, Marca
from time import sleep
from django.db import IntegrityError
from celery import shared_task
import requests
from datetime import datetime
from .functions_uso_geral import extrair_sku_pai
from collections import Counter
from collections import defaultdict

token = "4d907ba2ee45f9e572b9a774badf06f6abde0ae8869c594cb948040ffb4a0544"
tempo_espera_get = 2  # Tempo de espera até realizar outra requisição ideal da 30 por minuto


# São 120 Consultados por minutos então uma consulta a cada 0.5 segundos parece que isso na teoria

def descobrir_marca_sku(sku_filho):
    try:
        marca = ProdutosAtivosTiny.objects.get(sku=sku_filho).marca
        return marca.lower()
    except ProdutosAtivosTiny.DoesNotExist:
        return None


# Salvar skus filho no banco de dados
@shared_task(bind=True)
def salvar_skus_filho(self):
    produtos = ProdutosCadastradosTiny.objects.get(Nome_Lista_Produtos='Produtos Ativos+Excluidos').Lista_Produtos
    for marca, sku_filho in produtos.items():
        for sku in sku_filho:
            try:
                instance = ProdutosAtivosTiny()
                instance.sku = sku
                instance.marca = marca
                instance.save()
            except IntegrityError:
                continue


# Função vai ter que usar primeiramente no ipython/ Criar uma tarefa que execute todos os dias para pegar os PDs do dia
# anterior e sempre manter atualizado o sistema
def obter_pedidos_do_dia(dia, mes, ano):  # Passe uma data essa função vai pegar todos os pedidos e return um dict
    url = "https://api.tiny.com.br/api2/pedidos.pesquisa.php"
    # Pesquisa pedidos

    params = {
        'formato': 'json',
        'token': token,
        'dataInicial': f'{dia}/{mes}/{ano}',
        'dataFinal': f'{dia}/{mes}/{ano}',
        'pagina': 1,
    }

    # Pesquisa o numero de paginas
    numero_paginas = requests.get(url, params=params).json()['retorno']['numero_paginas']

    pedidos_tiny = {
        "id": [],
        "data_pedido": [],
        "valor": [],
        "situacao": [],
    }
    # Pesquisa Loop pagina por pagina
    # Coloca todos os pedidos no DF

    for pagina in range(1, numero_paginas + 1):
        params = {
            'formato': 'json',
            'token': token,
            'dataInicial': f'{dia}/{mes}/{ano}',
            'dataFinal': f'{dia}/{mes}/{ano}',
            'pagina': pagina,
        }
        pedidos = requests.get(url, params=params)
        pedidos = pedidos.json()['retorno']['pedidos']

        # Adicionar no DICT
        for pedido in pedidos:
            pedido = pedido['pedido']
            pedidos_tiny['id'].append(pedido['id'])
            pedidos_tiny['data_pedido'].append(pedido['data_pedido'])
            pedidos_tiny['valor'].append(pedido['valor'])
            pedidos_tiny['situacao'].append(pedido['situacao'])

        sleep(tempo_espera_get)

    return pedidos_tiny


def obter_informacoes_pedido(aid):
    url = "https://api.tiny.com.br/api2/pedido.obter.php"

    params = {
        'token': token,
        'formato': 'json',
        'id': int(aid),
    }

    # Se caso a requisição der erro aguarda um momento
    response = requests.get(url, params=params)

    # Encontrar uma forma de caso a API não responder esperar X tempo ou dar um tempo até ela voltar ?
    # while response.status_code != 200:
    #     response = requests.get(url, params=params)
    #     sleep(5)
    #     # Fica eternamente tentando
    response = response.json()['retorno']['pedido']
    skus_vendidos = [venda['item']['codigo'] for venda in response['itens']]
    marketplace = response['ecommerce']['nomeEcommerce']
    valores_unicos = [venda['item']['valor_unitario'] for venda in response['itens']]

    return marketplace, skus_vendidos, valores_unicos


def descobrir_marca_sku_por_api(sku_produto):
    aid_produto = 'não encontrado'

    for situacao in ['E', 'A', 'I']:
        # Obter o aid_produto
        url1 = 'https://api.tiny.com.br/api2/produtos.pesquisa.php'
        params1 = {
            'token': token,
            'formato': 'json',
            'pesquisa': sku_produto,
            'situacao': situacao
        }
        response1 = requests.get(url1, params=params1)
        if response1.status_code == 200:
            try:
                aid_produto = response1.json()['retorno']['produtos'][0]['produto']['id']
                break
            except KeyError:
                continue

        sleep(tempo_espera_get)

    if aid_produto == 'não encontrado':
        return ""

    # Obter a marca do sku obtendo as informações desse sku
    url2 = 'https://api.tiny.com.br/api2/produto.obter.php'
    params2 = {
        'token': token,
        'formato': 'json',
        'id': aid_produto
    }
    response2 = requests.get(url2, params=params2)
    marca_produto = response2.json()['retorno']['produto']['marca']
    ean = response2.json()['retorno']['produto']['gtin']
    return marca_produto.lower(), ean


def atualizar_pedidos_do_dia(dia, mes, ano):  # executar todos os dias pega pedidos do dia anterior
    # # Obter pedidos
    # data_atual = datetime.now()
    # data_atual_menos_1day = data_atual - timedelta(days=1)  # Diminui um dia do dia atual
    # data_atual_menos_1day = data_atual_menos_1day.strftime("%d %m %y").split(" ")
    #
    # dia = data_atual_menos_1day[0]
    # mes = data_atual_menos_1day[1]
    # ano = data_atual_menos_1day[2]

    pedidos = obter_pedidos_do_dia(dia, mes, ano)  # obtem os pedidos do dia desejado
    pedidos_do_dia_zip = zip(pedidos["id"], pedidos["data_pedido"], pedidos["valor"], pedidos["situacao"])
    print('Quantidade de pedidos', len(pedidos["id"]))
    for aid, data_pedido, valor, situacao in pedidos_do_dia_zip:
        # Verificar se o pedido já tem no banco de dados
        if Pedidos.objects.filter(id_tiny=aid):  # Aqui quer dizer que já tem
            continue

        try:
            skus_mkts = obter_informacoes_pedido(aid)  # Pega o marketplace e os skus vendidos
            for sku, valor_venda in zip(skus_mkts[1], skus_mkts[2]):
                instance = Pedidos()

                instance.id_tiny = aid
                if len(skus_mkts) > 1:
                    instance.valor_total = float(valor_venda)
                else:
                    instance.valor_total = valor
                instance.situacao = situacao
                instance.data_pedido = datetime.strptime(data_pedido, "%d/%m/%Y").date()
                # Consultar SKUS Vendidos e Marketplace do PD

                sleep(tempo_espera_get)
                instance.marketplace = skus_mkts[0]
                instance.save()

                # Verificar se o SKU se está no banco de dados se não estiver salvar, só depois continuar
                for sku_vendido in skus_mkts[1]:
                    if not ProdutosAtivosTiny.objects.filter(sku=sku_vendido).exists():
                        dados_pedido = descobrir_marca_sku_por_api(sku_vendido)
                        ProdutosAtivosTiny.objects.create(
                            sku=sku_vendido,
                            marca=dados_pedido[0],
                            ean=dados_pedido[1],
                        )

                # Adiciona os SKUS
                instance.marca = Marca.objects.filter(nome_marca=descobrir_marca_sku(sku)).first()
                instance.sku_vendido = ProdutosAtivosTiny.objects.filter(sku=sku).first()
                instance.save()
        except KeyError:
            continue  # Quando o pedido não é de nenhum ecommerce
        # Salvar no banco de dados, com todas as informações em mãos


def atualizar_situacao_pedidos(dia, mes, ano):
    # # Obter pedidos
    # data_atual = datetime.now()
    # data_atual_menos_1day = data_atual - timedelta(days=1)  # Diminui um dia do dia atual
    # data_atual_menos_1day = data_atual_menos_1day.strftime("%d %m %y").split(" ")
    #
    # dia = data_atual_menos_1day[0]
    # mes = data_atual_menos_1day[1]
    # ano = data_atual_menos_1day[2]

    pedidos_do_dia = obter_pedidos_do_dia(dia, mes, ano)
    pedidos_do_dia_zip = zip(pedidos_do_dia['id'], pedidos_do_dia['situacao'])

    for aid, situacao in pedidos_do_dia_zip:
        # Verificar se o pedido já tem no banco de dados
        try:
            pd = Pedidos.objects.filter(id_tiny=aid)  # Aqui quer dizer que já tem
            for pedido in pd:
                pedido.situacao = situacao
                pedido.save()
                print(pedido.id_tiny, 'atualizado')
        except Pedidos.DoesNotExist:
            pass


# Agora filtrar fazer os CRUD no banco de dados
def objeto_filtrado(data_inicio, data_fim, marca):
    pedidos_do_dia = Pedidos.objects.filter(
        data_pedido__range=(data_inicio, data_fim),
    ).exclude(situacao__in=['Cancelado', 'Dados incompletos'])
    if marca == "Todas":
        return pedidos_do_dia
    else:
        marca_especifica = Marca.objects.get(nome_marca=marca)
        pedidos_do_dia_por_marca = pedidos_do_dia.filter(marca=marca_especifica)
    return pedidos_do_dia_por_marca


def quantidade_vendas_do_periodo(data_inicio, data_fim, marca):
    pedidos_do_dia = objeto_filtrado(data_inicio, data_fim, marca).distinct('id_tiny')  # Pegar os pedidos unicos para somar
    return len(pedidos_do_dia)


def faturamento_total(data_inicio, data_fim, marca):
    pedidos_do_dia = objeto_filtrado(data_inicio, data_fim, marca)

    if marca == "Todas":
        faturamento = sum([pedido.valor_total for pedido in pedidos_do_dia])
        return round(faturamento, 2)
    else:
        faturamento = sum([pedido.valor_total for pedido in pedidos_do_dia])
        return round(faturamento, 2)


def faturamento_por_marketplace(data_inicio, data_fim, marca):
    pedidos_do_dia = objeto_filtrado(data_inicio, data_fim, marca)

    # Somar cada pedido no seu respectivo MKT
    vendas_por_mkt = defaultdict(float)
    for pedido in pedidos_do_dia:
        vendas_por_mkt[pedido.marketplace] += float(pedido.valor_total)

    return dict(
        sorted(vendas_por_mkt.items(), key=lambda item: item[1], reverse=True))  # Aqui coloca do maior para menor


def skus_mais_vendido(data_inicio, data_fim, marca):
    pedidos_do_dia = objeto_filtrado(data_inicio, data_fim, marca)

    # Cria uma lista de SKUs PAI
    skus_pai = [extrair_sku_pai(str(pedido.sku_vendido)) for pedido in pedidos_do_dia]

    if marca == "aramis":
        skus_pai = [str(pedido.sku_vendido) for pedido in pedidos_do_dia]

    # Conta os SKUs
    contagem = Counter(skus_pai)

    # Pega os 10 mais vendidos
    top10 = dict(contagem.most_common(5))
    return top10

def curva_abc(data_inicio, data_fim, marca, limite_a=0.7, limite_b=0.9):
    pedidos_do_dia = objeto_filtrado(data_inicio, data_fim, marca)

    vendas = defaultdict(float)
    for pedido in pedidos_do_dia:
        vendas[extrair_sku_pai(str(pedido.sku_vendido))] += float(pedido.valor_total)

    vendas_abc = dict(sorted(vendas.items(), key=lambda x:x[1], reverse=True))
#-----------------------------------------------------------------------------------------------------------------------
    total = sum(vendas.values())
    acumulado = 0

    grupos = {
        "A": {"total": 0, "skus": {}},
        "B": {"total": 0, "skus": {}},
        "C": {"total": 0, "skus": {}},
    }

    for sku, valor in vendas_abc.items():
        acumulado += valor / total

        if acumulado <= limite_a:
            grupo = "A"
        elif acumulado <= limite_b:
            grupo = "B"
        else:
            grupo = "C"

        grupos[grupo]["skus"][sku] = valor
        grupos[grupo]["total"] += valor

    return grupos
#-----------------------------------------------------------------------------------------------------------------------
# descobrir o EAN do sku do produto
def descobrir_ean_sku(sku_produto):
    ean = None

    url = 'https://api.tiny.com.br/api2/produtos.pesquisa.php'
    for situacao in ['E', 'A', 'I']:
        params = {
            'token': token,
            'formato': 'json',
            'pesquisa': sku_produto,
            'situacao': situacao
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            try:
                ean = response.json()['retorno']['produtos'][0]['produto']['gtin']
            except KeyError:
                continue

        sleep(2)

    return ean


# Pesquisa o SKU e pega seu respectivo EAN/ Isso pode ser feito por planilha
def atualizar_eans_dos_skus():
    for sku_produto in ProdutosAtivosTiny.objects.all():
        if not sku_produto.ean:
            ean_produto = descobrir_ean_sku(sku_produto.sku)
            sku_produto.ean = ean_produto
            sku_produto.save()
            sleep(2)

def top10_marcas_que_mais_fatura():
    ...

# Será que tem algum pedido com marca em maiúsculo e ta dando erro?
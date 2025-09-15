from .models import ProdutosCadastradosTiny, ProdutosAtivosTiny, Pedidos, Marca
from time import sleep
from django.db import IntegrityError
from celery import shared_task
import requests
from datetime import datetime, timedelta

token = "4d907ba2ee45f9e572b9a774badf06f6abde0ae8869c594cb948040ffb4a0544"
tempo_espera_get = 2  # Tempo de espera até realizar outra requisição


# São 120 Consultados por minutos então uma consulta a cada 0.5 segundos parece que isso na teoria

def descobrir_marca_sku(sku_filho):
    produtos = ProdutosCadastradosTiny.objects.get(Nome_Lista_Produtos='Produtos Ativos').Lista_Produtos
    for marca, skus in produtos.items():
        if sku_filho in skus:
            return marca

    return None


# Salvar skus filho no banco de dados
@shared_task(bind=True)
def salvar_skus_filho(self):
    produtos = ProdutosCadastradosTiny.objects.get(Nome_Lista_Produtos='Produtos Ativos').Lista_Produtos
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
    aid_produto = [venda['item']['id_produto'] for venda in response['itens']]
    valores_unicos = [venda['item']['valor_unitario'] for venda in response['itens']]

    return marketplace, skus_vendidos, aid_produto, valores_unicos


def descobrir_marca_sku_por_api(aid_produto):
    # Obter a marca do sku obtendo as informações desse sku
    url2 = 'https://api.tiny.com.br/api2/produto.obter.php'
    params2 = {
        'token': token,
        'formato': 'json',
        'id': aid_produto
    }
    response2 = requests.get(url2, params=params2)
    marca_produto = response2.json()['retorno']['produto']['marca']
    sku_produto = response2.json()['retorno']['produto']['codigo']
    return sku_produto, marca_produto


def atualizar_pedidos_do_dia(dia, mes, ano):  # executar todos os dias pega pedidos do dia anterior
    # # Obter pedidos
    # data_atual = datetime.now()
    # data_atual_menos_1day = data_atual - timedelta(days=1)  # Diminui um dia do dia atual
    # data_atual_menos_1day = data_atual_menos_1day.strftime("%d %m %y").split(" ")
    #
    # dia = data_atual_menos_1day[0]
    # mes = data_atual_menos_1day[1]
    # ano = data_atual_menos_1day[2]

    pedidos = obter_pedidos_do_dia(dia, mes, ano)
    pedidos_do_dia_zip = zip(pedidos["id"], pedidos["data_pedido"], pedidos["valor"], pedidos["situacao"])

    for aid, data_pedido, valor, situacao in pedidos_do_dia_zip:
        # Verificar se o pedido já tem no banco de dados
        try:
            Pedidos.objects.get(id_tiny=aid)  # Aqui quer dizer que já tem
            continue
        except Pedidos.DoesNotExist:
            pass

        try:
            skus_mkts = obter_informacoes_pedido(aid)  # Pega o marketplace e os skus vendidos

            instance = Pedidos()

            instance.id_tiny = aid
            instance.valor_total = valor
            instance.situacao = situacao
            instance.data_pedido = datetime.strptime(data_pedido, "%d/%m/%Y").date()
            # Consultar SKUS Vendidos e Marketplace do PD

            sleep(tempo_espera_get)
            instance.marketplace = skus_mkts[0]
            # Adiciona os valores unicos dos pedidos
            instance.valores = skus_mkts[3]
            instance.save()

            # Verificar se o SKU se está no banco de dados se não estiver salvar, só depois continuar
            for sku_vendido, aid_produto in zip(skus_mkts[1], skus_mkts[2]):
                try:
                    ProdutosAtivosTiny.objects.get(sku=sku_vendido)
                except ProdutosAtivosTiny.DoesNotExist:
                    instance2 = ProdutosAtivosTiny()
                    dados_pedido = descobrir_marca_sku_por_api(aid_produto)

                    instance2.sku = dados_pedido[0]
                    instance2.marca = dados_pedido[1]
                    instance2.save()

            # Adiciona os SKUS
            produtos = ProdutosAtivosTiny.objects.filter(sku__in=skus_mkts[1])
            instance.skus_vendidos.add(*produtos)  # Dessa forma adiciona todos skus
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
            pd = Pedidos.objects.get(id_tiny=aid)  # Aqui quer dizer que já tem
            pd.situacao = situacao
            pd.save()
            print(pd.id_tiny, 'atualizado')
        except Pedidos.DoesNotExist:
            pass


# Agora filtrar fazer os CRUD no banco de dados
def objeto_filtrado(data_inicio, data_fim):
    pedidos_do_dia = Pedidos.objects.filter(
        data_pedido__range=(data_inicio, data_fim),
    ).exclude(situacao__in=['Cancelado', 'Dados incompletos'])
    return pedidos_do_dia


def filtrar_pedidos_por_marca(data_inicio, data_fim, marca):
    pedidos_do_dia = objeto_filtrado(data_inicio, data_fim)
    marcas = {marca.nome_marca: [] for marca in Marca.objects.all()}
    # Pega pedido por pedido descobre a marca colocar na lista

    descobrir_marca_sku()


def quantidade_vendas_do_periodo(data_inicio, data_fim, marca):
    pedidos_do_dia = objeto_filtrado(data_inicio, data_fim, marca)
    return len(pedidos_do_dia)


def faturamento_total(data_inicio, data_fim):
    pedidos_do_dia = objeto_filtrado(data_inicio, data_fim)
    faturamento = sum([pedidos.valor_total for pedidos in pedidos_do_dia])
    return round(faturamento, 2)


def faturamento_por_marketplace(data_inicio, data_fim):
    pedidos_do_dia = objeto_filtrado(data_inicio, data_fim)
    # Somar cada pedido no seu respectivo MKT
    vendas_por_mkt = {}
    for pedido in pedidos_do_dia:
        try:
            vendas_por_mkt[pedido.marketplace] += float(pedido.valor_total)
        except KeyError:
            vendas_por_mkt[pedido.marketplace] = float(pedido.valor_total)

    return dict(
        sorted(vendas_por_mkt.items(), key=lambda item: item[1], reverse=True))  # Aqui coloca do maior para menor


def sku_mais_vendido():
    ...

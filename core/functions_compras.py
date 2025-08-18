import xlrd
import pandas as pd
from core.models import Marca, ProdutosCadastradosTiny
from core.functions_uso_geral import extrair_sku_pai
from core.tasks import atualizar_lista_produtos

# Função que detecta se tem alguma nova marca no relatorio de vendas para ser adicionada no BD
def verificar_relatorio_vendas_marca_nova(relatorio_vendas):
    # Pegar todas as marcas da planilha e do banco de dados
    workbook_vendas = xlrd.open_workbook(file_contents=relatorio_vendas.read(), ignore_workbook_corruption=True)
    workbook_vendas_pandas = pd.read_excel(workbook_vendas)

    # Pega todas as marcas da Coluna 1 do relatorio de vendas filtrando os campos vazios ' nan' do tipo float
    marcas_relatorio = [marca.lower() for marca in workbook_vendas_pandas.iloc[:, 0] if not isinstance(marca, float)]
    marca_banco = list(Marca.objects.values_list('nome_marca', flat=True))

    # Verifica se existe alguma marca nova
    marcas_novas = []
    for marca in marcas_relatorio:
        marca = marca.replace('-',' ')

        if marca not in marca_banco:
            marcas_novas.append(marca)

    # Se existir alguma marca nova adiciona no banco de dados
    if marcas_novas:
        for marca_nova in marcas_novas:
            m = Marca(nome_marca=marca_nova)
            m.save()

        print('Marcas novos adicionadas: ', marcas_novas)

        atualizar_lista_produtos.delay()  # Mada para fila a tarefa de atualizar o sistema de skus, pois agora tem uma nova
        # marca para adicionar os skus filhos

# Função que pega os dados de estoque geral, full, comprado e calculo uma sugestão de compras com base no periodo
# desejado, e retorna uma planilha com todos esses dados
def gerar_sugestao_compras(estoque_full, saldo_tiny, relatorio_vendas, ordens_compra, marca_giro, periodo):
    path_estoque_full = estoque_full
    path_saldo_tiny = saldo_tiny
    path_relatorio_vendas = relatorio_vendas
    marca_giro = str(marca_giro)
    periodo = str(periodo)
# ----------------------------------------------------------------------------------------------------------------------
    # GET Dados saldo estoque disponível do Tiny
    df_estoque_tiny = xlrd.open_workbook(file_contents=path_saldo_tiny.read(), ignore_workbook_corruption=True)
    df_estoque_tiny_pd = pd.read_excel(df_estoque_tiny)
    coluna_sku1 = df_estoque_tiny_pd.iloc[0:, 0]
    coluna_estoque_disponivel = df_estoque_tiny_pd.iloc[0:, 4]
    saldo_estoque_disponivel = dict()

    for x, y in zip(coluna_sku1, coluna_estoque_disponivel):
        saldo_estoque_disponivel[x] = y
# ----------------------------------------------------------------------------------------------------------------------
    # GET Dados saldo estoque Full
    df_estoque_full = pd.read_excel(path_estoque_full)

    coluna_sku2 = df_estoque_full.iloc[14:, 3]
    coluna_saldo_estoque_full = df_estoque_full.iloc[14:, 20]
    saldo_estoque_full = dict()

    for x, y in zip(coluna_sku2, coluna_saldo_estoque_full):
        saldo_estoque_full[x] = y
# ----------------------------------------------------------------------------------------------------------------------
    # Dados de Ordem de Compra
    if ordens_compra is not None:
        path_ordens_compra = ordens_compra
        ordem_compra = xlrd.open_workbook(file_contents=path_ordens_compra.read(), ignore_workbook_corruption=True)
        ordem_compra_df = pd.read_excel(ordem_compra)

        coluna_sku3 = ordem_compra_df.iloc[0:,12]
        coluna_estoque_comprado = ordem_compra_df.iloc[0:,9]
        estoque_comprado_previsto = {}

        for z, h in zip(coluna_sku3, coluna_estoque_comprado):
            estoque_comprado_previsto[z] = h
# ----------------------------------------------------------------------------------------------------------------------
    # Cria Dict Pasta 1 Que contem os produtos que atendem ao filtro e Pasta 2 que não atendem ao filtro
    work_new_compras_sem_filtro = {
        'SKU_Seller': [],  # A
        'Estoque Geral': [],  # B
        'Estoque Full': [],  # C
        'Estoque Comprado': [],  # D
        'Saídas Periodo': [],  # E
        'Sugestão de Compras': [],  # F
        'Ajuste Comprador': [],  # G
    }
    work_new_compras_filtro_win = {
        'SKU_Seller': [],  # A
        'Estoque Geral': [],  # B
        'Estoque Full': [],  # C
        'Estoque Comprado': [],  # D
        'Saídas Periodo': [],  # E
        'Sugestão de Compras': [],  # F
        'Ajuste Comprador': [],  # G
    }
    work_new_compras_filtro_loser = {
        'SKU_Seller': [],  # A
        'Estoque Geral': [],  # B
        'Estoque Full': [],  # C
        'Estoque Comprado': [],  # D
        'Saídas Periodo': [],  # E
        'Sugestão de Compras': [],  # F
        'Ajuste Comprador': [],  # G
    }
# ----------------------------------------------------------------------------------------------------------------------
    # Filtrar as saídas agrupando por Marca ficando Marca[SKU: Qtd Vendida] podendo acessar a marca que quiser
    df_relatorio = xlrd.open_workbook(file_contents=path_relatorio_vendas.read(), ignore_workbook_corruption=True)
    df_relatorio_pd = pd.read_excel(df_relatorio)

    marcas_disponiveis = df_relatorio_pd.iloc[0:, 0]  # A
    sku_produto = df_relatorio_pd.iloc[0:, 2]  # C
    qtd_vendida = df_relatorio_pd.iloc[0:, 3]  # D
    titulo_produto = df_relatorio_pd.iloc[0:, 1]  # E

    relatorio_por_marca = dict()

    for marca, sku, qtd, des in zip(marcas_disponiveis, sku_produto, qtd_vendida, titulo_produto):
        if str(marca) != 'nan':
            marca_atual = marca.lower()
            relatorio_por_marca[marca_atual] = list()
        if str(marca) == 'nan':
            if des != 'ENVIO FULL':
                relatorio_por_marca[marca_atual].append([sku, qtd])
# ----------------------------------------------------------------------------------------------------------------------
    # Agora todos os dados em mãos juntar tudo no dict
    for sku, qtd_saida in relatorio_por_marca[marca_giro]:
        estoque_tiny = saldo_estoque_disponivel.get(sku, 0)
        estoque_full = saldo_estoque_full.get(sku, 0)

        if ordens_compra is not None:
            estoque_comprado = estoque_comprado_previsto.get(sku, 0)
        else:
            estoque_comprado = 0

        # Ponto crucial aqui que é feito a sugestão de compras/ Caso saida tem sido negativa contabiliza também
        sugestao_compras = qtd_saida - (estoque_tiny + estoque_full + estoque_comprado)

        work_new_compras_sem_filtro['SKU_Seller'].append(sku)
        work_new_compras_sem_filtro['Estoque Geral'].append(estoque_tiny)
        work_new_compras_sem_filtro['Estoque Full'].append(estoque_full)
        work_new_compras_sem_filtro['Estoque Comprado'].append(estoque_comprado)
        work_new_compras_sem_filtro['Saídas Periodo'].append(qtd_saida)
        work_new_compras_sem_filtro['Sugestão de Compras'].append(sugestao_compras)
        work_new_compras_sem_filtro['Ajuste Comprador'].append('')
# ----------------------------------------------------------------------------------------------------------------------
    # Agora adiciona os SKUs que não teve vendas no período
    produtos_ativos = ProdutosCadastradosTiny.objects.get(Nome_Lista_Produtos='Produtos Ativos').Lista_Produtos
    for skus_cadastrados in produtos_ativos[marca_giro]:
        if skus_cadastrados not in work_new_compras_sem_filtro['SKU_Seller']:
            estoque_tiny = saldo_estoque_disponivel.get(skus_cadastrados, 0)
            estoque_full = saldo_estoque_full.get(skus_cadastrados, 0)

            if ordens_compra is not None:
                estoque_comprado = estoque_comprado_previsto.get(skus_cadastrados, 0)
            else:
                estoque_comprado = 0

            saida_periodo = 0  # Saida é zero, pois não contém no relatorio de vendas

            sugestao_compras = saida_periodo - (estoque_tiny + estoque_full + estoque_comprado)

            work_new_compras_sem_filtro['SKU_Seller'].append(skus_cadastrados)
            work_new_compras_sem_filtro['Estoque Geral'].append(estoque_tiny)
            work_new_compras_sem_filtro['Estoque Full'].append(estoque_full)
            work_new_compras_sem_filtro['Estoque Comprado'].append(estoque_comprado)
            work_new_compras_sem_filtro['Saídas Periodo'].append(saida_periodo)
            work_new_compras_sem_filtro['Sugestão de Compras'].append(sugestao_compras)
            work_new_compras_sem_filtro['Ajuste Comprador'].append('')
# ----------------------------------------------------------------------------------------------------------------------
    # Agora filtrar os SKUs que teve a quantidade vendas por período atingida e não atingida
    wncsf = work_new_compras_sem_filtro
    # Agrupar por SKU pai contabilizando assim quanto cada SKU PAI teve de vendas
    vendas_por_sku_pai = {}
    for sku_filho, qtd_saida in zip(wncsf['SKU_Seller'], wncsf['Saídas Periodo']):
        sku_pai_agrupador = extrair_sku_pai(sku_filho)
        try:
            vendas_por_sku_pai[sku_pai_agrupador]
        except KeyError:
            vendas_por_sku_pai[sku_pai_agrupador] = 0

        vendas_por_sku_pai[sku_pai_agrupador] += qtd_saida

    match periodo:
        case '1':
            limite = 30
        case '2':
            limite = 60
        case '3':
            limite = 120
    # Agora as quantidades vendas por sku pai separar as atingidas e não atingidas
    w = work_new_compras_sem_filtro
    listas_w = (w['SKU_Seller'], w['Estoque Geral'], w['Estoque Full'], w['Estoque Comprado'], w['Saídas Periodo'],
                w['Sugestão de Compras'], w['Ajuste Comprador'])
    for a, b, c, d, e, f, g in zip(*listas_w):
        sku_pai = extrair_sku_pai(a)  # Extrai o sku pai do sku filho atual
        qtd_vendas_periodo = vendas_por_sku_pai[sku_pai]  # Verifica a quantidade vendida no período para validar se
        # esse sku atingiu a quantidade de vendas desejada no período

        if qtd_vendas_periodo > limite:
            work_new_compras_filtro_win['SKU_Seller'].append(a)
            work_new_compras_filtro_win['Estoque Geral'].append(b)
            work_new_compras_filtro_win['Estoque Full'].append(c)
            work_new_compras_filtro_win['Estoque Comprado'].append(d)
            work_new_compras_filtro_win['Saídas Periodo'].append(e)
            work_new_compras_filtro_win['Sugestão de Compras'].append(f)
            work_new_compras_filtro_win['Ajuste Comprador'].append(g)
        else:
            work_new_compras_filtro_loser['SKU_Seller'].append(a)
            work_new_compras_filtro_loser['Estoque Geral'].append(b)
            work_new_compras_filtro_loser['Estoque Full'].append(c)
            work_new_compras_filtro_loser['Estoque Comprado'].append(d)
            work_new_compras_filtro_loser['Saídas Periodo'].append(e)
            work_new_compras_filtro_loser['Sugestão de Compras'].append(f)
            work_new_compras_filtro_loser['Ajuste Comprador'].append(g)

    work_new_compras_filtro_win = pd.DataFrame(work_new_compras_filtro_win).sort_values(by='SKU_Seller', ascending=True)
    work_new_compras_filtro_loser = pd.DataFrame(work_new_compras_filtro_loser).sort_values(by='SKU_Seller', ascending=True)

    return work_new_compras_filtro_win, work_new_compras_filtro_loser

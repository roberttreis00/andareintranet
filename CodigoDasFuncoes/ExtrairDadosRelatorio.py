def agrupar_vendas_por_marca_lista_vendas(relatorio, marca):
    """
    Input = Relatorio de Vendas
    Output = Dict MARCA: [[SKU, QTD], [SKU, QTD]]
    """

    df_relatorio = xlrd.open_workbook(file_contents=relatorio.read(), ignore_workbook_corruption=True)
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
            if des == 'ENVIO FULL' or des == 'FULL SBS':
                continue
            else:
                relatorio_por_marca[marca_atual].append([sku, qtd])

    return relatorio_por_marca[marca]
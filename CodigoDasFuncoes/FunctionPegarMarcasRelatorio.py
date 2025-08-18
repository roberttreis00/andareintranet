"""
Funçãoo que pega todas as marcas do relatorio de vendas

SE Tiver uma marca nova no relatorio indica uma nova marca para adicionada nas opções
de Giro

* Esse código util ser usado no Shell do Django os arquivos ser colocados na pasta media
"""
import xlrd
import pandas as pd
# from core.models import Marca

workbook_vendas = xlrd.open_workbook('relatorio-de-vendas_13-08-2025-18-53-37.xls', ignore_workbook_corruption=True)
workbook_vendas_pandas = pd.read_excel(workbook_vendas)

# Pega todas as marcas da Coluna 1 do relatorio de vendas filtrando os campos vazios ' nan' do tipo float
marcas = [marca.lower() for marca in workbook_vendas_pandas.iloc[:,0] if not isinstance(marca, float)]
print(marcas)
# # Salva no banco de dados o nome da marca
# for marca in marcas:
#     x = Marca(nome_marca=marca)
#     x.save()

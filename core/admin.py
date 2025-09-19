from django.contrib import admin
from . import models

@admin.register(models.Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ['nome_marca', ]


@admin.register(models.ProdutosCadastradosTiny)
class ProdutosCadastradosAdmin(admin.ModelAdmin):
    list_display = ['Nome_Lista_Produtos', 'Data_ultima_atualizacao']

@admin.register(models.ArquivosProcessados)
class ArquivosProcessadosAdmin(admin.ModelAdmin):
    list_display = ['Workbook', 'output_file', 'status']

@admin.register(models.ProdutosAtivosTiny)
class ProdutosAtivosTiny(admin.ModelAdmin):
    list_display = ['sku', 'marca', 'ean', 'custo']
    search_fields = ['sku', 'marca', 'ean']

@admin.register(models.Pedidos)
class PedidosAdmin(admin.ModelAdmin):
    list_display = ['id_tiny', 'valor_total', 'situacao', 'sku_vendido', 'marca', 'marketplace', 'data_pedido']
    search_fields = ['id_tiny', 'valor_total', 'situacao', 'marketplace', 'data_pedido', 'sku_vendido__sku', 'marca__nome_marca']

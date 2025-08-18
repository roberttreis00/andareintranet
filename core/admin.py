from django.contrib import admin
from . import models

@admin.register(models.Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ['nome_marca', ]


@admin.register(models.ProdutosCadastradosTiny)
class ProdutosCadastradosAdmin(admin.ModelAdmin):
    list_display = ['Nome_Lista_Produtos', 'Data_ultima_atualizacao']
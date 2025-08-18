from django.urls import path
from . import views

urlpatterns = [
    path('', views.GerarSugestaoCompras.as_view(), name='gerar-sugestao-de-compras'),
    path('gerar-sugestao-programada', views.GerarSugestaoProgramada.as_view(), name='gerar-sugestao-programada'),
    path('gerar-ordem-de-compra-tiny', views.GerarOrdemComprasTiny.as_view(), name='gerar-ordem-de-compra-tiny'),
]

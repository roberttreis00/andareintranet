from django.urls import path
from . import views

urlpatterns = [
    path('', views.GerarSugestaoCompras.as_view(), name='gerar-sugestao-de-compras'),
    path('gerar-sugestao-programada', views.GerarSugestaoProgramada.as_view(), name='gerar-sugestao-programada'),
    path('gerar-ordem-de-compra-tiny', views.GerarOrdemDeCompra.as_view(), name='gerar-ordem-de-compra-tiny'),
    path('dashboard/', views.DashboardAndare.as_view(), name='dashboard'),

    path('task-status/<int:task_id>/', views.TaskStatusView.as_view(), name='task_status'),
    path('download/<int:task_id>/', views.DownloadFileView.as_view(), name='download_file'),
]

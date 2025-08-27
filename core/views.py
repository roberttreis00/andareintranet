from django.utils.datastructures import MultiValueDictKeyError
from .forms import SugestaoCompras, SugestaoComprasProgramada, GetSugestaoCompras
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from . import functions_compras
from django.views import View
from django.shortcuts import get_object_or_404
import os
from django.http import JsonResponse
from .tasks import atualizar_lista_produtos, tratar_sugestao_de_compras
from .models import ProdutosCadastradosTiny, ArquivosProcessados
from datetime import datetime, timezone
from django.http import HttpResponse
import openpyxl


class GerarSugestaoCompras(FormView):
    template_name = 'sugestao.html'
    form_class = SugestaoCompras
    success_url = reverse_lazy("gerar-sugestao-de-compras")

    def form_valid(self, form):
        # Aqui posso tratar os dados enviados
        workbook_estoque_full = self.request.FILES['PlanilhaEstoqueFull']
        workbook_estoque_tiny = self.request.FILES['PlanilhaSaldoTiny']
        workbook_relatorio_vendas = self.request.FILES['PlanilhaRelatorioDeVendas']
        try:
            workbook_ordens_de_compra = self.request.FILES['PlanilhaOrdemDeCompras']
        except MultiValueDictKeyError:
            workbook_ordens_de_compra = None
        marca_giro = form.cleaned_data['Marca']
        periodo = form.cleaned_data['Periodo']

        # Ao ser enviado os dados para gerar o giro de compras acionar a função que atualizar as marcas no banco
        functions_compras.verificar_relatorio_vendas_marca_nova(workbook_relatorio_vendas)
        # E a tarefa para atualizar a lista de SKUS Ativos e Inativos/ Uma tarefa que demora precisa colocar na fila do Redis
        ultima_atualizacao_produtos = (ProdutosCadastradosTiny.objects.get(Nome_Lista_Produtos='Produtos Ativos')
                                       .Data_ultima_atualizacao)
        data_atual = datetime.now(timezone.utc)
        qtd_dias_sem_atualizar = data_atual - ultima_atualizacao_produtos
        # Antes verificar se já faz mais de 14 Dias que não tem atualização
        if qtd_dias_sem_atualizar.days > 14:
            atualizar_lista_produtos.delay()  # Mada para fila a tarefa de atualizar o sistema de skus

        workbook_relatorio_vendas.seek(0)

        # Segue o fluxo normal agora trata os dados das planilhas e return a Sugestão de Compras
        df_sugestao_compras_win_and_loser = functions_compras.gerar_sugestao_compras(
            workbook_estoque_full, workbook_estoque_tiny, workbook_relatorio_vendas, workbook_ordens_de_compra,
            marca_giro, periodo)

        df_win = df_sugestao_compras_win_and_loser[0]
        df_loser = df_sugestao_compras_win_and_loser[1]

        # Com a sugestao de compras tratar dados para retornar um response e assim realizar o Download
        # Acrescentar duas colunas df_win
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Produtos Giro OK'
        ws.append(list(df_win.columns) + ['Desvio'])

        for idx, row in df_win.iterrows():
            ws.append(
                [row["SKU_Seller"], row["Estoque Geral"], row["Estoque Full"], row["Estoque Comprado"],
                 row["Saídas Periodo"], row["Sugestão de Compras"], row['Ajuste Comprador'],
                 ""])  # Duas colunas extras vazias

        for row_idx in range(2, len(df_win) + 2):  # Começa na linha 2 (1 é cabeçalho)
            ws[f"H{row_idx}"].value = (
                f'=IF(G{row_idx}="","",'
                f'IF(G{row_idx}=F{row_idx},"",'
                f'IF(AND(F{row_idx}<0,G{row_idx}=0),"",'
                f'IF(G{row_idx}>F{row_idx},"ALTERADO",IF(G{row_idx}<F{row_idx},"ALTERADO","")))))'
            )

        # Acrescentar duas colunas df_loser
        ws2 = wb.create_sheet(title='Produtos Giro Baixo')
        ws2.append(list(df_loser.columns) + ['Desvio'])

        for idx, row in df_loser.iterrows():
            ws2.append(
                [row["SKU_Seller"], row["Estoque Geral"], row["Estoque Full"], row["Estoque Comprado"],
                 row["Saídas Periodo"], row["Sugestão de Compras"], row['Ajuste Comprador'],
                 ""])  # Duas colunas extras vazias

        for row_idx in range(2, len(df_loser) + 2):  # Começa na linha 2 (1 é cabeçalho)
            ws2[f"H{row_idx}"].value = (
                f'=IF(G{row_idx}="","",'
                f'IF(G{row_idx}=F{row_idx},"",'
                f'IF(AND(F{row_idx}<0,G{row_idx}=0),"",'
                f'IF(G{row_idx}>F{row_idx},"ALTERADO",IF(G{row_idx}<F{row_idx},"ALTERADO","")))))'
            )
        # Agora juntar os dois DF em um só
        # Return response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="sugestão_compras_{marca_giro}.xlsx"'
        wb.save(response)
        return response


# Gera a sugestão de compras programada é o mesmo que sugestão giro 1 2 3 meses só que tem 3 semestre de relatorio
# de vendas para cálculos
class GerarSugestaoProgramada(FormView):
    template_name = 'programada.html'
    form_class = SugestaoComprasProgramada
    success_url = reverse_lazy("gerar-sugestao-programada")

    # Agora tratar os dados fazer o mesmo só que agora com duas colunas a mais s
    def form_valid(self, form):
        workbook_estoque_full = self.request.FILES['PlanilhaEstoqueFull']
        workbook_estoque_tiny = self.request.FILES['PlanilhaSaldoTiny']
        workbook_relatorio_1 = self.request.FILES['PlanilhaRelatorioDeVendas1']
        workbook_relatorio_2 = self.request.FILES['PlanilhaRelatorioDeVendas2']
        workbook_relatorio_3 = self.request.FILES['PlanilhaRelatorioDeVendasSemestreAtual']

        try:
            workbook_ordens_de_compra = self.request.FILES['PlanilhaOrdemDeCompras']
        except MultiValueDictKeyError:
            workbook_ordens_de_compra = None
        marca_giro = form.cleaned_data['Marca']

        # Segue o fluxo normal agora trata os dados das planilhas e return a Sugestão de Compras Programada sem precisar
        # Acrescentar novas marcas caso tenha deixa para o Giro
        df_compras_crescimento = functions_compras.gerar_sugestao_compras_programada(workbook_estoque_full,
                                                                                     workbook_estoque_tiny,
                                                                                     workbook_relatorio_1,
                                                                                     workbook_relatorio_2,
                                                                                     workbook_relatorio_3,
                                                                                     workbook_ordens_de_compra,
                                                                                     marca_giro)

        df_compras = df_compras_crescimento[0]
        crescimento = df_compras_crescimento[1]

        # Agora com o DataFrame em mãos acrescentar as colunas e retorna o giro programado
        # Acrescentar duas colunas df_win
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Sugestão de Compras Semestral'
        ws.append(list(df_compras.columns) + ['Desvio'])

        for idx, row in df_compras.iterrows():
            ws.append(
                [row["SKU_Seller"], row["Estoque Geral"], row["Estoque Full"], row["Estoque Comprado"],
                 row["Saídas 1° Semestre"], row['Saídas 2° Semestre'], row['Saídas Semestre Atual'],
                 row["Sugestão de Compras"], row['Ajuste Comprador'], ""])  # Duas colunas extras vazias

        for row_idx in range(2, len(df_compras) + 2):  # Começa na linha 2 (1 é cabeçalho)
            ws[f"J{row_idx}"].value = (
                f'=IF(I{row_idx}="","",'
                f'IF(I{row_idx}=G{row_idx},"",'
                f'IF(AND(H{row_idx}<0,I{row_idx}=0),"",'
                f'IF(I{row_idx}>H{row_idx},"ALTERADO",IF(I{row_idx}<H{row_idx},"ALTERADO","")))))'
            )

        # Agora juntar os dois DF em um só
        # Return response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="sugestao_compras_{marca_giro}_{crescimento}%.xlsx"'
        wb.save(response)
        return response


class GerarOrdemDeCompra(FormView):
    template_name = 'ordem_compras.html.html'
    form_class = GetSugestaoCompras
    success_url = reverse_lazy('gerar-ordem-de-compra-tiny')

    def form_valid(self, form):
        upload_file = form.cleaned_data['PlanilhaSugestaoCompras']
        fornecedor = form.cleaned_data['Fornecedor']
        situacao = form.cleaned_data['Situacao_compra']

        # 1. Criar uma instancia no banco
        # 2. Chama a tarefa com tarefa.delay(task_instance.id)
        task_instance = ArquivosProcessados.objects.create(
            Workbook=upload_file,
            Fornecedor=fornecedor,
            situacao_compra=situacao,  # situação giro ou programação
            status='Pendente',
        )

        # disparar a tarefa no Celery
        tratar_sugestao_de_compras.delay(task_instance.id)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Exibe as últimas 10 tarefas para o usuário
        context['tasks'] = ArquivosProcessados.objects.order_by('-created_at')[:1]
        return context


class TaskStatusView(View):
    def get(self, request, task_id):
        task = get_object_or_404(ArquivosProcessados, id=task_id)
        data = {
            'status': task.status,
            'output_file_url': task.output_file.url if task.output_file else None
        }
        return JsonResponse(data)


class DownloadFileView(View):

    def get(self, request, task_id):
        task = get_object_or_404(ArquivosProcessados, id=task_id)
        if task.status == 'Completo' and task.output_file:
            file_path = task.output_file.path
            if os.path.exists(file_path):
                with open(file_path, 'rb') as fh:
                    response = HttpResponse(fh.read(),
                                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")  # MIME type para .xlsx
                    response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
                    return response
        return HttpResponse("Arquivo não encontrado ou tarefa não concluída.", status=404)

from django.utils.datastructures import MultiValueDictKeyError
from .forms import SugestaoCompras
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from . import functions_compras
from .tasks import atualizar_lista_produtos
from .models import ProdutosCadastradosTiny
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


class GerarSugestaoProgramada(FormView):
    template_name = 'programada.html'


class GerarOrdemComprasTiny(FormView):
    template_name = 'ordem_compras.html'

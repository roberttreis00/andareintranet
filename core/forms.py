from django import forms
from django.forms import ChoiceField

from core.models import Marca
from django.utils.safestring import mark_safe

opcoes = [
    ('1', '1 mês'),
    ('2', '2 meses'),
    ('3', '3 meses'),
]

opcoes2 = [
    ('1', 'Giro'),
    ('2', 'Programada'),
]

# logo_mercado_e_full = ('<img src="/static/images/logoML.png" style="height:20px; vertical-align:middle; margin-right:5px;">'
#                        '<img src="/static/images/logoFull.png" style="height:20px; vertical-align:middle; margin-right:5px;">')

class SugestaoCompras(forms.Form):
    # PlanilhaEstoqueFull = forms.FileField(label='Planilha Saldo Estoque FULL') forma sem colocar logo
    PlanilhaEstoqueFull = forms.FileField(
        # label=mark_safe(f'Planilha Saldo Estoque {logo_mercado_e_full}')
        label='Planilha Saldo Estoque Full'
    )
    PlanilhaSaldoTiny = forms.FileField(label='Planilha Saldo Estoque Tiny')
    PlanilhaRelatorioDeVendas = forms.FileField(label='Planilha Relátorio de Vendas')
    PlanilhaOrdemDeCompras = forms.FileField(label='Planilha Ordens de Compra OPCIONAL', required=False)
    Marca = forms.ModelChoiceField(queryset=Marca.objects.all())
    Periodo = forms.ChoiceField(choices=opcoes, widget=forms.Select, label='Período de giro')

    # Função para validar as extensões das planilhas enviadas se a extensão não for esperada
    # atualiza a pag e levanta um erro
    def validar_arquivos_excel(self, file, nome_campo, extensao, nome_esperado):
        if file is None and nome_campo == 'Planilha Ordens de Compras':
            return file

        # verifica se o arquivo é o esperado com base no nome
        if nome_esperado not in file.name:
            raise forms.ValidationError(
                f'O arquivo está no campo errado deve ser "{nome_esperado}"'
            )

        # Verifica se a extensão é a esperada
        if not file.name.endswith(extensao):
            raise forms.ValidationError(
                f'O arquivo "{nome_campo}" deve estar no formato {extensao}'
            )
        return file

    def clean_PlanilhaEstoqueFull(self):
        return self.validar_arquivos_excel(
            self.cleaned_data['PlanilhaEstoqueFull'], 'Planilha Estoque Full', '.xlsx', 'stock_general_full'
        )

    def clean_PlanilhaSaldoTiny(self):
        return self.validar_arquivos_excel(
            self.cleaned_data['PlanilhaSaldoTiny'], 'Planilha Saldo Tiny', '.xls', 'saldos-em-estoque'
        )

    def clean_PlanilhaRelatorioDeVendas(self):
        return self.validar_arquivos_excel(
            self.cleaned_data['PlanilhaRelatorioDeVendas'], 'Planilha Relatorio De Vendas', '.xls', 'relatorio-de-vendas'
        )

    def clean_PlanilhaOrdemDeCompras(self):
        return self.validar_arquivos_excel(
            self.cleaned_data['PlanilhaOrdemDeCompras'], 'Planilha Ordens de Compras', '.xls', 'pedidos_compra'
        )

class SugestaoComprasProgramada(forms.Form):
    PlanilhaEstoqueFull = forms.FileField(label='Planilha Saldo Estoque Full')
    PlanilhaSaldoTiny = forms.FileField(label='Planilha Saldo Estoque Tiny')

    PlanilhaRelatorioDeVendas1 = forms.FileField(label='Planilha Relátorio de Vendas 1° Semestre')
    PlanilhaRelatorioDeVendas2 = forms.FileField(label='Planilha Relátorio de Vendas 2° Semestre')
    PlanilhaRelatorioDeVendasSemestreAtual = forms.FileField(label='Planilha Relátorio de Vendas Semestre Atual')

    PlanilhaOrdemDeCompras = forms.FileField(label='Planilha Ordens de Compra OPCIONAL', required=False)
    Marca = forms.ModelChoiceField(queryset=Marca.objects.all())

    # Função para validar as extensões das planilhas enviadas se a extensão não for esperada
    # atualiza a pag e levanta um erro
    def validar_arquivos_excel(self, file, nome_campo, extensao, nome_esperado):
        if file is None and nome_campo == 'Planilha Ordens de Compras':
            return file

        # verifica se o arquivo é o esperado com base no nome
        if nome_esperado not in file.name:
            raise forms.ValidationError(
                f'O arquivo está no campo errado deve ser "{nome_esperado}"'
            )

        # Verifica se a extensão é a esperada
        if not file.name.endswith(extensao):
            raise forms.ValidationError(
                f'O arquivo "{nome_campo}" deve estar no formato {extensao}'
            )
        return file

    def clean_PlanilhaEstoqueFull(self):
        return self.validar_arquivos_excel(
            self.cleaned_data['PlanilhaEstoqueFull'], 'Planilha Estoque Full', '.xlsx', 'stock_general_full'
        )

    def clean_PlanilhaSaldoTiny(self):
        return self.validar_arquivos_excel(
            self.cleaned_data['PlanilhaSaldoTiny'], 'Planilha Saldo Tiny', '.xls', 'saldos-em-estoque'
        )

    def clean_PlanilhaRelatorioDeVendas1(self):
        return self.validar_arquivos_excel(
            self.cleaned_data['PlanilhaRelatorioDeVendas1'], 'Planilha Relatorio De Vendas 1°', '.xls',
            'relatorio-de-vendas'
        )

    def clean_PlanilhaRelatorioDeVendas2(self):
        return self.validar_arquivos_excel(
            self.cleaned_data['PlanilhaRelatorioDeVendas2'], 'Planilha Relatorio De Vendas 2°', '.xls',
            'relatorio-de-vendas'
        )
    def clean_PlanilhaRelatorioDeVendasSemestreAtual(self):
        return self.validar_arquivos_excel(
            self.cleaned_data['PlanilhaRelatorioDeVendasSemestreAtual'], 'Planilha Relatorio De Vendas Semestre Atual',
            '.xls', 'relatorio-de-vendas'
        )

    def clean_PlanilhaOrdemDeCompras(self):
        return self.validar_arquivos_excel(
            self.cleaned_data['PlanilhaOrdemDeCompras'], 'Planilha Ordens de Compras', '.xls', 'pedidos_compra'
        )

class GetSugestaoCompras(forms.Form):
    PlanilhaSugestaoCompras = forms.FileField(label='Planilha Sugestão Compra')
    Fornecedor = forms.CharField(max_length=50, label='Fornecedor')
    Situacao_compra = forms.ChoiceField(choices=opcoes2, widget=forms.Select, label='Situação da Compra')

opcoes3 = [
    ('1', 'Em aberto'),
    ('2', 'Aprovado'),
    ('3', 'Preparando envio'),
    ('4', 'Faturado'),
    ('5', 'Pronto para envio'),
    ('6', 'Enviado'),
    ('7', 'Entregue'),
    ('8', 'Não Entregue'),
    ('9', 'Dados incompletos'),
    ('10', 'Cancelado'),
]

class FiltroDataForm(forms.Form):
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    Marca = forms.ChoiceField(choices=[], label='Marca')  # inicial vazio

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pega todas as marcas do banco quando o form é instanciado
        marcas = [(m.nome_marca, m.nome_marca) for m in Marca.objects.all()]
        marcas = [('Todas', 'Todas')] + marcas
        self.fields['Marca'].choices = marcas

Periodos = [
    (1, 'Último Mês'),
    (3, 'Último Trimestre'),
    (6, 'Último Semestre'),
    (12, 'Último Ano'),
]

class FiltroPeriodoAnterior(FiltroDataForm):
    Periodo = ChoiceField(choices=Periodos)

class ConsultarCusto(forms.Form):
    sku_ean_pesquisado = forms.CharField(max_length=50, label='Digite o SKU ou EAN')

class AtualizarCusto(forms.Form):
    arquivo_zip_nfs = forms.FileField(label='Arquivo Zipado com os .xml')

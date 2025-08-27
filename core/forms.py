from django import forms
from .models import Marca
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
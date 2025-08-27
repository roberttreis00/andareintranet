from django.db import models

class Marca(models.Model):
    nome_marca = models.CharField(max_length=30)

    class Meta:
        ordering = ['nome_marca']  # Ordena no painel ADMIN por ordem crescente

    def __str__(self):
        return self.nome_marca


class ProdutosCadastradosTiny(models.Model):
    Nome_Lista_Produtos = models.CharField(max_length=30)
    Lista_Produtos = models.JSONField(default=dict)  # Armazenar um dict
    Data_ultima_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.Nome_Lista_Produtos

class ArquivosProcessados(models.Model):
    status_choices = [
        ('Pendente', 'Pendente'),
        ('Processando', 'Processando'),
        ('Completo', 'Completo'),
        ('Falha', 'Falha'),
    ]

    Workbook = models.FileField(upload_to='uploaded_files/')
    Fornecedor = models.CharField(max_length=50)
    situacao_compra = models.CharField(max_length=50)
    output_file = models.FileField(upload_to='processed_outputs/', null=True, blank=True)
    task_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status = models.CharField(max_length=50, choices=status_choices, default='Pendente')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tarefa {self.id} - Arquivo: {self.Workbook.name} - Status: {self.status}"

    class Meta:
        verbose_name = "Arquivo Processado"
        verbose_name_plural = "Arquivos Processados"

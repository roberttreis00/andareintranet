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

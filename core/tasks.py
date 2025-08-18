from celery import shared_task
from .functions_uso_geral import pesquisar_marca_get_all
from .models import Marca, ProdutosCadastradosTiny
from time import sleep

marcas = list(Marca.objects.values_list('nome_marca', flat=True))  # Pegar todas as marcas do Banco de Dados e transforma em uma lista
ProdutosAtivos = {marca:[] for marca in marcas}  # Pega a lista de marca e faz um dict assim {marca: []}
ProdutosAtivosExcluidos = {marca:[] for marca in marcas}


# Atualiza a lista de produtos ativos e excluidos contendo todas as marcas e skus filhos
@shared_task(bind=True)
def atualizar_lista_produtos(self):
    # Pesquisa na API todos os produtos
    for marca in ProdutosAtivos.keys():
        sleep(0.5)
        ProdutosAtivos[marca] = pesquisar_marca_get_all(marca)
        sleep(0.5)

    # Salva no banco de Dados os Produtos Ativos
    produtos = ProdutosCadastradosTiny.objects.get(Nome_Lista_Produtos='Produtos Ativos')
    produtos.Lista_Produtos = ProdutosAtivos
    produtos.save()
    print('Produtos Ativos atualizado salvo com Sucesso!')

    # Now Juntar os Ativos com os Excluidos
    produtos_ativos_bd = ProdutosCadastradosTiny.objects.get(Nome_Lista_Produtos='Produtos Ativos').Lista_Produtos
    produtos_excluidos_bd = ProdutosCadastradosTiny.objects.get(Nome_Lista_Produtos='Produtos Excluidos').Lista_Produtos

    for marca in ProdutosAtivosExcluidos.keys():
        try:
            data = produtos_ativos_bd[marca] + produtos_excluidos_bd[marca]
            ProdutosAtivosExcluidos[marca] = data
        except KeyError:
            continue

    produtos_ativos_excluidos = ProdutosCadastradosTiny.objects.get(Nome_Lista_Produtos='Produtos Ativos+Excluidos')
    produtos_ativos_excluidos.Lista_Produtos = ProdutosAtivosExcluidos
    produtos_ativos_excluidos.save()
    print('Produtos Ativos + Excluidos salvo com Sucesso!')

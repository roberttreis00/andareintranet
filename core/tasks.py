from celery import shared_task
from .functions_uso_geral import pesquisar_marca_get_all, consultar_sku
from .models import Marca, ProdutosCadastradosTiny, ArquivosProcessados
from django.core.files.base import ContentFile
from time import sleep
from random import randint
import pandas as pd
import os
from datetime import datetime

marcas = list(Marca.objects.values_list('nome_marca', flat=True))  # Pegar todas as marcas do Banco de Dados e transforma em uma lista
ProdutosAtivos = {marca:[] for marca in marcas}  # Pega a lista de marca e faz um dict assim {marca: []}
ProdutosAtivosExcluidos = {marca:[] for marca in marcas}
data_atual = datetime.now().strftime('%d/%m/%y')

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

@shared_task(bind=True)
def tratar_sugestao_de_compras(self, file_id):

    # 3. Pegar a instancia e roda a função
    task_instance = None
    try:
        task_instance = ArquivosProcessados.objects.get(id=file_id)
        task_instance.status = 'Processando'
        task_instance.task_id = self.request.id
        task_instance.save()

        if not task_instance.workbook:
            raise FileNotFoundError('Workbook não encontrado para processamento.')

        ordem_compra = "".join([str(randint(0, 9)) for x in range(0, 9)])

        work_new_compras = {
            'ID': [],
            'DATA': [],
            'ID contato': [],
            'Nome do contato': [],  # Marca
            'Desconto': [],
            'Observações': [],
            'Situação': [],  # Em aberto, Em andamento
            'ID Produto': [],  # Get API
            'Descrição': [],
            'Quantidade': [],
            'Valor Custo': [],
            'Número da ordem de compra': [],  # Pode ter isso no BD ORDEM 1 e vai acrescentando
            'Código (SKU)': [],
        }

        sugestao_compras_excel = pd.read_excel(task_instance.workbook)

        sk_us = sugestao_compras_excel.iloc[0:, 0]

        if task_instance.tipo_giro_compras == 'Giro':
            sugestao_compras = sugestao_compras_excel.iloc[:, 5]
            ajuste_comprador = sugestao_compras_excel.iloc[:, 6]
        else:
            sugestao_compras = sugestao_compras_excel.iloc[:, 7]
            ajuste_comprador = sugestao_compras_excel.iloc[:, 8]

        qtd_de_skus = len(sk_us)
        cont = 1

        for x, y, z in zip(sk_us, sugestao_compras, ajuste_comprador):
            comprado = z

            if str(z) == 'nan':
                comprado = y

            if isinstance(x, float):  # quer dizer que é vazio
                continue

            if comprado < 0:
                continue

            consulta_sku = consultar_sku(x)
            print(f'Pesquisando: {cont}/{qtd_de_skus}')
            cont += 1

            work_new_compras['ID'].append('')
            work_new_compras['DATA'].append(data_atual)
            work_new_compras['ID contato'].append('')
            work_new_compras['Nome do contato'].append(task_instance.Fornecedor)
            work_new_compras['Desconto'].append('')
            work_new_compras['Observações'].append('')
            work_new_compras['Situação'].append('Em Aberto')
            work_new_compras['ID Produto'].append(consulta_sku['id'])
            work_new_compras['Descrição'].append(consulta_sku['nome'])
            work_new_compras['Quantidade'].append(comprado)
            work_new_compras['Valor Custo'].append(consulta_sku['preco_custo'])
            work_new_compras['Número da ordem de compra'].append(ordem_compra)
            work_new_compras['Código (SKU)'].append(x)

            sleep(0.6)

        df_processado = pd.DataFrame(work_new_compras)
        original_filename_base, original_filename_ext = os.path.splitext(task_instance.workbook.name)
        output_filename = f"processed_{os.path.basename(original_filename_base)}_{task_instance.id}.xlsx"

        # Cria um caminho temporário para salvar o arquivo processado antes de salvá-lo no FileField
        temp_output_path = os.path.join('/tmp', output_filename)  # Usar /tmp para arquivos temporários no Docker

        # Salva o DataFrame processado em um novo arquivo Excel
        df_processado.to_excel(temp_output_path, index=False)

        # Salva o arquivo de saída no modelo ArquivosProcessados
        with open(temp_output_path, 'rb') as f_output:
            task_instance.output_file.save(output_filename, ContentFile(f_output.read()), save=True)

        # Remove o arquivo temporário após salvar no modelo
        os.remove(temp_output_path)

        task_instance.status = 'Completo'
        task_instance.save()

        return {'status': 'success', 'output_file_url': task_instance.output_file.url}

    except ArquivosProcessados.DoesNotExist:
        print(f"Erro: Instância de ArquivosProcessados com ID {file_id} não encontrada.")
        return {'status': 'Falha', 'error': 'Tarefa não encontrada'}
    except Exception as e:
        if task_instance:
            task_instance.status = 'Falha'
            task_instance.save()
        print(f"Erro ao processar arquivos para a tarefa {file_id}: {e}")
        return {'status': 'Falha', 'error': str(e)}
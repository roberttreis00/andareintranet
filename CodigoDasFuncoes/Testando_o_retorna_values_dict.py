work_new_compras_sem_filtro = {
    'SKU_Seller': ['dados1', 'dados2'],  # A
    'Estoque Geral': ['dados1', 'dados2'],  # B
    'Estoque Full': ['dados1', 'dados2'],  # C
    'Estoque Comprado': ['dados1', 'dados2'],  # D
    'Saídas Periodo': ['dados1', 'dados2'],  # E
    'Sugestão de Compras': ['dados1', 'dados2'],  # F
    'Ajuste Comprador': ['dados1', 'dados2'],  # G
}
w = work_new_compras_sem_filtro
listas_w = (w['SKU_Seller'], w['Estoque Geral'], w['Estoque Full'], w['Estoque Comprado'], w['Saídas Periodo'],
            w['Sugestão de Compras'], w['Ajuste Comprador'])
for a, b, c, d, e, f, g in zip(*listas_w):
    print(a, b, c, d, e, f, g)

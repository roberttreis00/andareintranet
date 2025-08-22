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
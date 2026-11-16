import pandas as pd

print("📂 Carregando o arquivo original de 10 milhões de linhas...")
# Se o seu arquivo for separado por vírgula (,), mantenha sep=','
# Se for por ponto e vírgula (;), ajuste para sep=';'
df_focos = pd.read_csv("frp_harm_brasil.csv", sep=",")

print(f"Total de linhas antes do filtro: {len(df_focos):,}")

# 🚀 Filtra mantendo apenas de 2016 até 2025
df_filtrado = df_focos[(df_focos["year"] >= 2016) & (df_focos["year"] <= 2025)]

print(f"Total de linhas após o filtro (2016-2025): {len(df_filtrado):,}")

# Salva o arquivo já limpo para você usar no pipeline principal
arquivo_saida = "frp_harm_brasil_2016_2025.csv"
df_filtrado.to_csv(arquivo_saida, index=False, encoding="utf-8")

print(f"💾 Arquivo filtrado salvo com sucesso como '{arquivo_saida}'!")
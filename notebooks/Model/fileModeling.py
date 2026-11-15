import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# =====================================================================
# 1. CARREGAR OS DADOS
# =====================================================================
print("Lendo os dados de focos de calor por H3...")
df_focos = pd.read_csv("frp_harm_brasil.csv", sep=";")

print("Lendo o Shapefile dos biomas...")
biomas_gdf = gpd.read_file("./extraDataAquisition/Biomas5000.shp")

# Define o padrão oficial do IBGE (SIRGAS 2000) caso o shapefile venha sem CRS
if biomas_gdf.crs is None:
  biomas_gdf.set_crs(epsg=4674, inplace=True)

print("Lendo o dataset de clima da NASA...")
df_clima = pd.read_csv("./extraDataAquisition/clima_biomas_nasa.csv", sep=";")

# =====================================================================
# 2. ASSOCIAR CADA CENTRÓIDE DE H3 AO SEU RESPECTIVO BIOMA
# =====================================================================
print("Realizando o cruzamento espacial (H3 -> Bioma)...")

geometry = [Point(xy) for xy in zip(df_focos["lon"], df_focos["lat"])]
gdf_focos = gpd.GeoDataFrame(df_focos, geometry=geometry, crs="EPSG:4674")

if biomas_gdf.crs != gdf_focos.crs:
  biomas_gdf = biomas_gdf.to_crs(gdf_focos.crs)

# Mantemos 'how="left"' para não perder as linhas antes da checagem
gdf_enriquecido = gpd.sjoin(
    gdf_focos, biomas_gdf, how="left", predicate="within"
)
gdf_enriquecido = gdf_enriquecido.rename(columns={"NOM_BIOMA": "bioma"})

colunas_para_manter = ["cell", "lat", "lon", "year", "month", "monthly_frp", "bioma"]
df_para_merge = pd.DataFrame(gdf_enriquecido[colunas_para_manter])


# =====================================================================
# 3. NORMALIZAR NOMES E FAZER O MERGE COM O CLIMA DA NASA
# =====================================================================
print("Fazendo o merge com as variáveis climáticas da NASA...")

def limpar_nome_bioma(serie):
  return (
      serie.str.normalize("NFKD")
      .str.encode("ascii", errors="ignore")
      .str.decode("utf-8")
      .str.lower()
      .str.strip()
      .str.replace(" ", "_")
  )

# Padroniza nomes para: amazonia, caatinga, cerrado, mata_atlantica, pampa, pantanal
df_para_merge["bioma_limpo"] = limpar_nome_bioma(df_para_merge["bioma"])
df_clima["bioma_limpo"] = limpar_nome_bioma(df_clima["bioma"])

# Renomeia temp max para temp_max para manter o padrão snake_case
df_clima = df_clima.rename(columns={"temp max": "temp_max"})

df_final = pd.merge(
    df_para_merge.drop(columns=["bioma"]),
    df_clima[["bioma_limpo", "ano", "mes", "precipitacao", "umidade", "temp_max"]],
    left_on=["bioma_limpo", "year", "month"],
    right_on=["bioma_limpo", "ano", "mes"],
    how="left",
)

# Remove colunas duplicadas de ano/mês que vieram do df_clima
df_final = df_final.drop(columns=["ano", "mes"])

# =====================================================================
# 4. APLICAR ONE-HOT ENCODING E FILTRAR LINHAS SEM BIOMA
# =====================================================================
print("Aplicando One-Hot Encoding nos biomas...")

df_final = pd.get_dummies(df_final, columns=["bioma_limpo"], prefix="", prefix_sep="", dtype=int)

todos_biomas = ["amazonia", "caatinga", "cerrado", "mata_atlantica", "pampa", "pantanal"]
for b in todos_biomas:
  if b not in df_final.columns:
    df_final[b] = 0

linhas_antes = len(df_final)
df_final = df_final[df_final[todos_biomas].sum(axis=1) > 0]
linhas_removidas = linhas_antes - len(df_final)

if linhas_removidas > 0:
  print(f"🗑️ {linhas_removidas} linha(s) com todos os biomas zerados foram removidas com sucesso.")

# Reordena as colunas exatamente na sequência solicitada
ordem_colunas = [
    "cell",
    "lat",
    "lon",
    "year",
    "month",
    "monthly_frp",
    "precipitacao",  # (junto com o merge do clima)
    "umidade",
    "temp_max",
    "amazonia",
    "caatinga",
    "cerrado",
    "mata_atlantica",
    "pampa",
    "pantanal",
]

df_final = df_final[ordem_colunas]

# =====================================================================
# 5. EXPORTAR PARA PARQUET E CSV
# =====================================================================
arquivo_parquet = "dataset_focos_clima_h3.parquet"
arquivo_csv = "dataset_focos_clima_h3.csv"

df_final.to_parquet(arquivo_parquet, index=False)
df_final.to_csv(arquivo_csv, sep=";", index=False, encoding="utf-8")

print(f"\n✨ Sucesso! Total de linhas processadas: {len(df_final)}")
print("Colunas finais:", df_final.columns.tolist())
print(df_final.head())
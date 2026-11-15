import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# =====================================================================
# 1. CARREGAR OS DADOS
# =====================================================================
print("Lendo os dados de focos de calor por H3 (10M linhas)...")
df_focos = pd.read_csv("frp_harm_brasil.csv", sep=",")

print("Lendo o Shapefile dos biomas...")
biomas_gdf = gpd.read_file("./extraDataAquisition/Biomas5000.shp")

if biomas_gdf.crs is None:
  biomas_gdf.set_crs(epsg=4674, inplace=True)

print("Lendo o dataset de clima da NASA...")
df_clima = pd.read_csv("./extraDataAquisition/clima_biomas_nasa.csv", sep=";")

# =====================================================================
# 2. ASSOCIAR CADA CENTRÓIDE AO BIOMA (COM FALLBACK PARA O MAIS PRÓXIMO)
# =====================================================================
print("Realizando o cruzamento espacial (H3 -> Bioma)...")

geometry = [Point(xy) for xy in zip(df_focos["lon"], df_focos["lat"])]
gdf_focos = gpd.GeoDataFrame(df_focos, geometry=geometry, crs="EPSG:4674")

if biomas_gdf.crs != gdf_focos.crs:
  biomas_gdf = biomas_gdf.to_crs(gdf_focos.crs)

# Passo A: Cruzamento estrito dentro do bioma
gdf_enriquecido = gpd.sjoin(
    gdf_focos, biomas_gdf, how="left", predicate="within"
)
gdf_enriquecido = gdf_enriquecido.rename(columns={"NOM_BIOMA": "bioma"})

# Passo B: Resgatar pontos que ficaram sem bioma (borda/costa) usando o mais próximo
mask_sem_bioma = gdf_enriquecido["bioma"].isna()
if mask_sem_bioma.any():
  print(
      f"⚠️ {mask_sem_bioma.sum()} ponto(s) caíram na borda. Resgatando"
      " pelo bioma mais próximo (sjoin_nearest)..."
  )
  # Faz o join nearest apenas com os pontos órfãos
  gdf_proximo = gpd.sjoin_nearest(
      gdf_focos[mask_sem_bioma], biomas_gdf, how="left", distance_col="dist"
  )
  # Atribui o bioma encontrado
  col_nome_bioma = (
      "NOM_BIOMA" if "NOM_BIOMA" in gdf_proximo.columns else "bioma"
  )
  gdf_enriquecido.loc[mask_sem_bioma, "bioma"] = gdf_proximo[
      col_nome_bioma
  ].values

# Remove qualquer caso extremo que ainda tenha persistido nulo
gdf_enriquecido = gdf_enriquecido.dropna(subset=["bioma"])

colunas_para_manter = ["cell", "lat", "lon", "year", "month", "monthly_frp", "bioma"]
df_para_merge = pd.DataFrame(gdf_enriquecido[colunas_para_manter])

# =====================================================================
# 3. NORMALIZAR E GARANTIR TIPOS PARA O MERGE DO CLIMA
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


df_para_merge["bioma_limpo"] = limpar_nome_bioma(df_para_merge["bioma"])
df_clima["bioma_limpo"] = limpar_nome_bioma(
    df_clima["bioma"]
    if "bioma" in df_clima.columns
    else df_clima["NOM_BIOMA"]
)

# 🚀 Blindagem de Tipos: Garante que ano e mês sejam inteiros idênticos em ambos
df_para_merge["year"] = df_para_merge["year"].astype(int)
df_para_merge["month"] = df_para_merge["month"].astype(int)
df_clima["ano"] = df_clima["ano"].astype(int)
df_clima["mes"] = df_clima["mes"].astype(int)

# Padroniza nome da coluna de temperatura máxima
if "temp max" in df_clima.columns:
  df_clima = df_clima.rename(columns={"temp max": "temp_max"})

df_final = pd.merge(
    df_para_merge.drop(columns=["bioma"]),
    df_clima[["bioma_limpo", "ano", "mes", "precipitacao", "umidade", "temp_max"]],
    left_on=["bioma_limpo", "year", "month"],
    right_on=["bioma_limpo", "ano", "mes"],
    how="inner",  # Inner para garantir que só passa quem encontrou o clima correspondente
)

df_final = df_final.drop(columns=["ano", "mes"])
df_final["bioma"] = df_final["bioma_limpo"]
df_final = df_final.drop(columns=["bioma_limpo"])

# =====================================================================
# 4. APLICAR ONE-HOT ENCODING
# =====================================================================
print("Aplicando One-Hot Encoding...")
df_final = pd.get_dummies(
    df_final, columns=["bioma"], prefix="", prefix_sep="", dtype=int
)

todos_biomas = [
    "amazonia",
    "caatinga",
    "cerrado",
    "mata_atlantica",
    "pampa",
    "pantanal",
]
for b in todos_biomas:
  if b not in df_final.columns:
    df_final[b] = 0

ordem_colunas = [
    "cell",
    "lat",
    "lon",
    "year",
    "month",
    "monthly_frp",
    "precipitacao",
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
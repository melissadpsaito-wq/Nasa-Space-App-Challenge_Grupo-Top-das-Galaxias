"""Base do modelo D48: ΣFRP harmonizado (D40/D42) + bioma + clima NASA POWER, 2016–2025.

Rodar da pasta notebooks/Model:
    python fileModeling.py
    python fileModeling.py --base ../../data/processed/res5_frp/frp_harm_full.csv.gz   # sem o contorno IBGE

Entrada: a base COMPLETA em .csv.gz (frp_harmonize csv --brazil ... --gzip). NÃO abrir/salvar no Excel:
o Excel corta em 1.048.576 linhas e sobram ~3,5 mil dos 31,9 mil hexágonos (aconteceu em 15/11).
Saída: dataset_model_ready_2016_2025.parquet (+ .csv) com as colunas que o RF e o rf_outlook usam.
Junta o bioma por hexágono (31,9 mil pontos), não por linha (9,6 M) — mesmo resultado, muito mais rápido.
"""
import argparse

import geopandas as gpd
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--base", default="../../data/processed/res5_frp/frp_harm_brasil.csv.gz")
ap.add_argument("--from-year", type=int, default=2016)
ap.add_argument("--to-year", type=int, default=2025)
ap.add_argument("--out", default="dataset_model_ready_2016_2025")
args = ap.parse_args()

# =====================================================================
# 1. CARREGAR OS DADOS
# =====================================================================
print(f"Lendo a base de ΣFRP harmonizado: {args.base}")
df_focos = pd.read_csv(args.base)
if "frp" in df_focos.columns and "monthly_frp" not in df_focos.columns:
  df_focos = df_focos.rename(columns={"frp": "monthly_frp"})
n_cells_all = df_focos["cell"].nunique()
print(f"  {len(df_focos):,} linhas · {n_cells_all:,} hexágonos")
if len(df_focos) == 1_048_575 or n_cells_all < 20_000:
  raise SystemExit("Base cortada (limite do Excel?). Gere de novo: python -m pipeline.frp_harmonize csv --brazil data/raw/br_pais.geojson --gzip")

df_focos = df_focos[df_focos["year"].between(args.from_year, args.to_year)].copy()
print(f"  {args.from_year}–{args.to_year}: {len(df_focos):,} linhas")

print("Lendo o Shapefile dos biomas...")
biomas_gdf = gpd.read_file("./extraDataAquisition/Biomas5000.shp")
if biomas_gdf.crs is None:
  biomas_gdf.set_crs(epsg=4674, inplace=True)
# só os 6 biomas terrestres (o shapefile tem também mar territorial / ZEE)
biomas_gdf = biomas_gdf[biomas_gdf["COD_BIOMA"].isin(["AMZ", "MAT", "CER", "CAAT", "PTN", "PMP"])]

print("Lendo o dataset de clima da NASA...")
df_clima = pd.read_csv("./extraDataAquisition/clima_biomas_nasa.csv", sep=";")

# =====================================================================
# 2. BIOMA POR HEXÁGONO (centro; fallback = bioma mais próximo)
# =====================================================================
print("Cruzamento espacial (H3 -> Bioma) por hexágono...")
cells = df_focos.groupby("cell", as_index=False)[["lat", "lon"]].first()
gdf_cells = gpd.GeoDataFrame(cells, geometry=gpd.points_from_xy(cells["lon"], cells["lat"]), crs="EPSG:4674")
if biomas_gdf.crs != gdf_cells.crs:
  biomas_gdf = biomas_gdf.to_crs(gdf_cells.crs)

j = gpd.sjoin(gdf_cells, biomas_gdf[["NOM_BIOMA", "geometry"]], how="left", predicate="within")
j = j[~j.index.duplicated()]
sem = j["NOM_BIOMA"].isna()
if sem.any():
  print(f"⚠️ {sem.sum()} hexágono(s) na borda/costa → bioma mais próximo (sjoin_nearest)")
  near = gpd.sjoin_nearest(gdf_cells[sem], biomas_gdf[["NOM_BIOMA", "geometry"]], how="left")
  near = near[~near.index.duplicated()]
  j.loc[sem, "NOM_BIOMA"] = near["NOM_BIOMA"].values
cell_bioma = j[["cell", "NOM_BIOMA"]].rename(columns={"NOM_BIOMA": "bioma"}).dropna()


def limpar_nome_bioma(serie):
  return (serie.str.normalize("NFKD").str.encode("ascii", errors="ignore").str.decode("utf-8")
          .str.lower().str.strip().str.replace(" ", "_"))


cell_bioma["bioma"] = limpar_nome_bioma(cell_bioma["bioma"])
print(cell_bioma["bioma"].value_counts().to_string())

# =====================================================================
# 3. CLIMA (bioma × ano × mês)
# =====================================================================
print("Merge com as variáveis climáticas da NASA...")
df_clima["bioma"] = limpar_nome_bioma(df_clima["bioma"])
df_clima = df_clima.rename(columns={"temp max": "temp_max", "ano": "year", "mes": "month"})
df_clima[["year", "month"]] = df_clima[["year", "month"]].astype(int)

df = df_focos.merge(cell_bioma, on="cell", how="inner")
df = df.merge(df_clima[["bioma", "year", "month", "precipitacao", "umidade", "temp_max"]],
              on=["bioma", "year", "month"], how="inner")

# =====================================================================
# 4. ONE-HOT DO BIOMA E EXPORT
# =====================================================================
todos_biomas = ["amazonia", "caatinga", "cerrado", "mata_atlantica", "pampa", "pantanal"]
for b in todos_biomas:
  df[b] = (df["bioma"] == b).astype(int)
ordem = ["cell", "lat", "lon", "year", "month", "monthly_frp", "precipitacao", "umidade", "temp_max", *todos_biomas]
df = df[ordem].sort_values(["cell", "year", "month"]).reset_index(drop=True)

per_cell = df.groupby("cell").size()
print(f"\n✨ {len(df):,} linhas · {df['cell'].nunique():,} hexágonos "
      f"(de {n_cells_all:,}) · meses por hexágono: {per_cell.min()}–{per_cell.max()}")
df.to_parquet(f"{args.out}.parquet", index=False)
print(f"💾 {args.out}.parquet")

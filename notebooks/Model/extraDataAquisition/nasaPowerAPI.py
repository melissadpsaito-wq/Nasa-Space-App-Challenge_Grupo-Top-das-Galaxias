import time
import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point

# =====================================================================
# CONFIGURAÇÕES INICIAIS
# =====================================================================
caminho_shapefile = "Biomas5000.shp"
coluna_nome_bioma = "NOM_BIOMA"
url_nasa = "https://power.larc.nasa.gov/api/temporal/monthly/point"

print("1. Lendo o arquivo Shapefile dos biomas...")
biomas_gdf = gpd.read_file(caminho_shapefile)

print("Biomas encontrados no Shapefile:", biomas_gdf[coluna_nome_bioma].unique())

resultados_finais = []

# =====================================================================
# GERANDO GRADE DE PONTOS E CONSULTANDO A NASA PARA TODOS OS BIOMAS
# =====================================================================
for bioma_nome in biomas_gdf[coluna_nome_bioma].unique():
  
  # por algum motivo o acento em amazonia e mata atlantica da problema
  nome_lower = bioma_nome.lower()
  termos_desejados = ["amaz", "ntica", "cerrado", "caatinga", "pantanal", "pampa"]
  
  if not any(termo in nome_lower for termo in termos_desejados):
    continue  # Pula qualquer coisa que não seja um dos 6 biomas

  print(
      f"\n=========================================="
      f"\nProcessando Bioma: {bioma_nome}"
      f"\n=========================================="
  )

  geom_bioma = biomas_gdf[
      biomas_gdf[coluna_nome_bioma] == bioma_nome
  ].union_all()
  min_lon, min_lat, max_lon, max_lat = geom_bioma.bounds

  if "amaz" in nome_lower:
    passo_grade = 2.0  
  elif "ntica" in nome_lower:
    passo_grade = 1.5  
  elif "caatinga" in nome_lower:
    passo_grade = 1.5  
  elif "cerrado" in nome_lower:
    passo_grade = 2.0  
  elif "pantanal" in nome_lower or "pampa" in nome_lower:
    passo_grade = 1.0  
  else:
    passo_grade = 2.0 #espacamento ok

  pontos_internos = []

  lon = min_lon
  while lon <= max_lon:
    lat = min_lat
    while lat <= max_lat:
      pt = Point(lon, lat)
      if geom_bioma.contains(pt):
        pontos_internos.append((lon, lat))
      lat += passo_grade
    lon += passo_grade

  print(
      f"📍 {len(pontos_internos)} pontos de amostragem gerados dentro do"
      f" {bioma_nome}."
  )

  dados_bioma_acumulados = {}

  for i, (lon, lat) in enumerate(pontos_internos):
    print(
        f"   Consultando ponto {i+1}/{len(pontos_internos)} (Lon: {lon:.2f},"
        f" Lat: {lat:.2f})..."
    )

    parametros = {
        "parameters": "PRECTOTCORR,RH2M,T2M_MAX",
        "community": "RE",
        "longitude": round(lon, 4),
        "latitude": round(lat, 4),
        "start": 2016,
        "end": 2025,
        "format": "JSON",
    }

    try:
      resposta = requests.get(url_nasa, params=parametros, timeout=30)
      if resposta.status_code == 200:
        properties = resposta.json().get("properties", {}).get("parameter", {})
        precip = properties.get("PRECTOTCORR", {})
        umidade = properties.get("RH2M", {})
        temp_max = properties.get("T2M_MAX", {})

        for chave in precip.keys():
          if len(chave) == 6:
            p = precip.get(chave)
            u = umidade.get(chave)
            t = temp_max.get(chave)

            if (
                p is not None
                and u is not None
                and t is not None
                and p > -100
                and u > -100
                and t > -100
            ):
              if chave not in dados_bioma_acumulados:
                dados_bioma_acumulados[chave] = {
                    "soma_p": 0.0,
                    "soma_u": 0.0,
                    "soma_t": 0.0,
                    "count": 0,
                }
              dados_bioma_acumulados[chave]["soma_p"] += p
              dados_bioma_acumulados[chave]["soma_u"] += u
              dados_bioma_acumulados[chave]["soma_t"] += t
              dados_bioma_acumulados[chave]["count"] += 1
    except Exception as e:
      print(f"      ⚠️ Falha no ponto: {e}")

    time.sleep(1)

  for chave, vals in dados_bioma_acumulados.items():
    n = vals["count"]
    if n > 0:
      resultados_finais.append({
          "bioma": bioma_nome,
          "mes": int(chave[4:]),
          "ano": int(chave[:4]),
          "precipitacao": round(vals["soma_p"] / n, 2),
          "umidade": round(vals["soma_u"] / n, 2),
          "temp max": round(vals["soma_t"] / n, 2),
      })

# =====================================================================
# SALVANDO O CSV FINAL
# =====================================================================
df_resultado = pd.DataFrame(resultados_finais)
df_resultado.to_csv(
    "clima_biomas_nasa.csv", sep=";", index=False, encoding="utf-8"
)
print(
    "\n✨ Arquivo 'clima_biomas_nasa.csv' gerado com sucesso contendo apenas"
    " os 6 biomas do Brasil!"
)
print(df_resultado["bioma"].value_counts())
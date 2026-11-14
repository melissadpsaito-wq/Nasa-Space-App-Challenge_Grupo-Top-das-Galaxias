# Guia técnico — como construir o Fire Almanac

Passo a passo por frente, com o "como funciona" e esqueletos de código. Os trechos são **referência**: cada dono escreve, roda, revisa e commita o código final durante o evento (registrar `AI-assisted: Claude` quando usar). Decisões citadas: `DECISIONS.md`.

## 1. Arquitetura
```
FIRMS CSV 2000–2025 (Terra, Aqua, S-NPP, NOAA-20)
        │ ingest + clean (Murilo)                      │
        ▼                                              ▼
data/clean/<sensor>/<ano>.parquet
        │ grid 0,02° por passagem + H3 res 4 (Murilo)
        ▼
grid2km_pass.parquet ──► agg_monthly.parquet
        │ bridges M1/M2 + bootstrap (Melissa)
        ▼
harm_series.parquet ──► validate (Samuel) ──► validation.json
        │                analytics (Samuel) ─► pettitt.json, score/pico (referência)
        ▼ export (Murilo)
app/public/data/*.json ──► app estático (Luana) ──► GitHub Pages
```
Unidade da série (D03): **detecções por célula de 0,02° por passagem, na escala S-NPP** ("focos VIIRS-equivalentes").

| Mês | Fonte do valor harmonizado | Conversão |
|---|---|---|
| 2000-11 → 2002-06 | Terra | Terra → Aqua → S-NPP · `low_conf = 1` (D10) |
| 2002-07 → 2012-01 | Aqua | Aqua → S-NPP (M2 ou M1) |
| 2012-02 → 2025-12 | S-NPP | nativo (só grade) |
| 2018 → 2025 (paralelo) | NOAA-20 | N20 → S-NPP (M1): não entra na linha do tempo; prova de continuidade (D33) |

D33: **todos** os sensores são harmonizados em **todos** os seus anos (Terra 2000–2025, Aqua 2002–2025, S-NPP 2012–2025, N20 2018–2025). A série do app usa a linha do tempo acima; as 4 séries convertidas vão para `sensors4.json` e para a validação cruzada.

O **bruto** (toggle) é a contagem de pixels do sensor de referência de cada mês, sem grade: é ele que mostra o salto falso de 2012.

---
## 2. Dados — Murilo

### 2.1 Ingest + clean (sáb 15:00–17:00)
Como funciona: cada sensor tem colunas e códigos próprios; o clean leva tudo a um schema único e aplica os filtros do guia MODIS C6, contando quantas linhas cada filtro remove (vira prova de qualidade na página Method).
```python
# pipeline/ingest.py  (esqueleto)
import duckdb
con = duckdb.connect()
PANTANAL = (-22.5, -15.5, -59.5, -54.5)   # lat_min, lat_max, lon_min, lon_max (piloto)

def load(path, kind):
    sat = ("CASE satellite WHEN 'Terra' THEN 'TERRA' WHEN 'Aqua' THEN 'AQUA' END" if kind == "modis"
           else "CASE satellite WHEN 'N' THEN 'SNPP' WHEN 'N20' THEN 'N20' END")
    conf = "confidence >= 30" if kind == "modis" else "confidence IN ('n','h')"
    return con.sql(f"""
      SELECT {sat} AS sensor,
             strptime(CAST(acq_date AS VARCHAR) || lpad(CAST(acq_time AS VARCHAR),4,'0'),
                      '%Y-%m-%d%H%M') AS ts,
             latitude, longitude, CAST(frp AS FLOAT) AS frp, daynight,
             CAST(scan*track AS FLOAT) AS pixel_area
      FROM read_csv_auto('{path}', union_by_name=true)
      WHERE type = 0 AND {conf} AND acq_date >= DATE '2000-11-01'""")
```
Checklist: contar linhas antes/depois de cada filtro → `data/clean/filter_log.csv`; salvar `data/clean/<sensor>/<ano>.parquet`.

**Status (sáb 15:13): ✅ concluído** — commit `2e66d2e`. Brasil 2025 = 08-fatos (0,00%); Pantanal 2000–2025 = 2.028.235 focos; 4/4 testes. Detalhes e números: `docs/DADOS-2.1-INGEST-CLEAN.md`.
```bat
python -m pipeline.ingest --area pantanal          :: ou --area brasil [--years 2025] [--raw <pasta FIRMS>]
python -m pytest -q tests/test_clean.py
```
Diferenças do esqueleto: leitura `all_varchar` + `TRY_CAST`; descoberta automática nos ZIPs `all_countries`; bbox aplicado; DuckDB 2.0 não tem `fetchone()` em relações.

### 2.2 Grade comum + H3 (sáb 17:00–19:00)
**Status (sáb 17:45): concluído** — `pipeline/grid.py` + `tests/test_grid.py`; Pantanal 1 s, conservação OK, 199 células. Diferenças: `frp_sum` (Σ FRP dos pixels, D29) na grade e no agregado; H3 só para as células 0,02° distintas; `grid_log.csv`. Detalhes: `docs/DADOS-2.2-2.3-GRADE-H3.md`.
Como funciona: um fogo visto pelo VIIRS (375 m) vira vários pixels; no MODIS (1 km), um. Contar **uma detecção por célula de 0,02° por passagem** remove esse efeito (razão S-NPP/Aqua 5,42 → 3,45). Manter a definição de passagem usada na análise de 13/11 (`sensor + ts + daynight`) para reproduzir o 3,45.
```python
# pipeline/grid.py
g = con.sql("""
  SELECT sensor, ts, daynight,
         CAST(floor(latitude/0.02) AS INT) gy, CAST(floor(longitude/0.02) AS INT) gx,
         max(frp) AS frp_max,          -- D26: resumo do FRP na célula = máximo
         count(*) AS n_pix, avg(pixel_area) AS pix_area
  FROM clean GROUP BY ALL""").df()
g["lat_c"], g["lon_c"] = (g.gy + .5) * .02, (g.gx + .5) * .02
u = g[["gy","gx","lat_c","lon_c"]].drop_duplicates()
u["cell"] = [h3.latlng_to_cell(a, b, 4) for a, b in zip(u.lat_c, u.lon_c)]   # h3 v4
g = g.merge(u, on=["gy","gx","lat_c","lon_c"])
g["ym"] = g.ts.dt.year * 100 + g.ts.dt.month
g.to_parquet("data/interim/grid2km_pass.parquet")
```
Sem bioma (D33): não há `cell_biome.parquet`, shapefile nem geopandas.

Agregado mensal (`agg_monthly.parquet`): `GROUP BY sensor, cell, ym` → `n = count(*)`, `frp_mean`, `frp_p90 = quantile_cont(frp_max, .9)`, `night_frac = avg(daynight='N')`, `pix_area`.
**Teste de conservação:** `sum(n)` do agregado = linhas de `grid2km_pass` (por sensor e ano). Vai para `tests/`.

### 2.3 Escalar para o Brasil inteiro (D28) (sáb 19:45 → madrugada)
**Status (sáb 17:53): concluído, adiantado** — `python -m pipeline.ingest --area brasil` (~1 min) + `python -m pipeline.grid --area brasil` (19 s); conservação OK; ~4.200 células; S-NPP/Aqua 2025 na grade = 3,45. Plano B (R14) não foi necessário.
Mesmo código sem o filtro de bbox, com os arquivos do Brasil (`COUNTRY=BRA` no `.env`/Makefile; para o mundo no futuro, trocar país ou usar o arquivo global do FIRMS); rodar em 2º plano por sensor/ano (`make ingest grid`). Se às 23:30 não tiver terminado: deixar rodando; plano B = áreas prontas (R14).

### 2.4 Export para o app (sáb 23:30 · dom 07:30)
```python
# pipeline/export.py  (formato: DATA_DICTIONARY §3)
months = list(range_ym(200011, last_ym))
def vec(s): return [int(round(10 * s.get(m, 0))) for m in months]
out = {"months": months, "cells": {}, "raw": {}, "lo": {}, "hi": {}, "low_conf": {}, "src": src_by_month}
for cell, d in harm.groupby("cell"):
    s = d.set_index("ym")
    if s.n_harm.sum() == 0: continue           # células sem fogo omitidas
    out["cells"][cell] = vec(s.n_harm); out["raw"][cell] = vec(s.n_raw)
    out["lo"][cell] = vec(s.lo); out["hi"][cell] = vec(s.hi)
    out["low_conf"][cell] = [int(s.low_conf.get(m, 0)) for m in months]
json.dump(out, open("app/public/data/harm_monthly.json", "w"), separators=(",", ":"))
```
Tamanho (R06): Brasil em res 4 (~4.800 células × 313 meses) deve passar de 5 MB: exportar já em **tiles** — um arquivo por célula-pai res 2 (`harm_<parent>.json`) e o app baixa só os pais da área desenhada (`cellToParent(cell, 2)`). Registrar em `STATUS.md` se acionar.

### 2.5 Áreas prontas (dom 07:30–10:00, D22)
`app/public/data/areas.json`: `[{id, name, polygon:[[lat,lng],...], story}]` para **Pantanal (parte brasileira, MS/MT)** e **região canavieira de SP** [verificar polígono: Ribeirão Preto / Alta Mogiana]. A frase de impacto agro só entra com fonte, ano e link (CNA [verificar]).

### 2.6 ~~NRT~~ — fora por D33. No lugar: `sensors4.json` (dom 10:00–12:00)
Série anual harmonizada de cada sensor (Brasil e áreas prontas) a partir das saídas da Melissa; alimenta o gráfico "4 satélites, 1 curva".

<details><summary>NRT (histórico, não fazer)</summary>

GitHub Action (cron diário + no build do Pages) chama `https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/VIIRS_NOAA20_NRT/{W,S,E,N}/{DAY_RANGE}` [verificar limite de `DAY_RANGE` na doc], com `FIRMS_MAP_KEY` dos Secrets. Aplica a mesma grade por passagem e o fator N20 → S-NPP; grava `nrt_last7.json` **no build** (não commita). Se o build falhar, o Pages mantém o último deploy.
</details>

### 2.7 `meta.json` e `open/`
`meta.json`: fontes, `version` FIRMS, datas de download, commit do pipeline. `open/`: `harm_series.parquet` + CSV + citação NASA FIRMS.

---
## 3. Ciência — dupla Melissa + Samuel

### 3.1 Contrato interno da dupla (sáb 15:00)
```yaml
# config/sensors.yaml  (Melissa)
reference: SNPP
unit: "cell-pass detections, 0.02° grid, S-NPP scale"
season: quarter            # D26: DJF, MAM, JJA, SON
bridges:
  - {from: AQUA,  to: SNPP, fit: [2012, 2021], exclude: [["2020-08-16","2020-09-02"]], methods: [M1, M2]}
  - {from: TERRA, to: AQUA, fit: [2003, 2010], methods: [M1]}     # antes da deriva (R05)
  - {from: N20,   to: SNPP, fit: [2018, 2025], methods: [M1]}
lambda_grid: [5, 20, 50]   # escolhido na validação
```
```python
# pipeline/bridges/base.py  (Melissa escreve; Samuel só consome)
class Bridge(Protocol):
    def fit(self, A: pd.DataFrame, B: pd.DataFrame, years: list[int]) -> "Bridge": ...
    def transform(self, A: pd.DataFrame) -> pd.DataFrame: ...   # cell, ym, n_pred
# A, B = agg_monthly filtrado por sensor; M2 também lê grid2km_pass (FRP por passagem)
```

### 3.2 Melissa — M1: razão com encolhimento (sáb 15:00–19:00)
Como funciona: por célula × mês do calendário, a razão B/A aprendida na sobreposição. Com poucos focos, a razão local é ruidosa, então é "puxada" para a razão do Brasil naquele mês do calendário (D33).
```
k(c,M) = (ΣB⁺ + λ·k_global(M)) / (ΣA⁺ + λ)     ⁺ = meses com A > 0 nos anos de ajuste (D32)
pred(c,ym) = k(c,M)·A(c,ym)       se A > 0
           = a(c,M)               se A = 0      (média de B nos meses com A = 0 → termo aditivo)
```
Antes: reproduzir a tabela do `METHOD.md` com 2025 (5,42 → 3,45 → ≈1,0). Se bater, o entendimento está certo.

**Status (sáb 17:53): concluído** — `pipeline/bridges/m1.py` (`M1(lam, ctx)`, `--eval`, `--agg`), `check_method.py` (bateu 5,42 → 3,58 → 3,45 → 1,00), `m1_preview.py`, `check_extra.py`; `tests/test_m1.py`. Brasil, teste 2020–21: consistency M1 0,45 × taxa única 0,69 × bruto 1,10. Coluna do termo aditivo = `add_term` (`add` colide com `DataFrame.add`). Detalhes: `docs/CIENCIA-3.2-M1.md`.

### 3.3 Melissa — limiar de FRP + M2 (sáb 19:45–23:30)
Como funciona: depois da grade ainda sobra 3,45×, porque o VIIRS vê fogos fracos que o MODIS não vê. Para cada estrato *s* = trimestre × dia/noite (8 estratos, Brasil inteiro, D33), o limiar τ é o FRP que iguala as contagens na sobreposição:
```
τ_s = quantil( frp_max das passagens S-NPP em s , 1 − N_Aqua,s / N_SNPP,s )
forte = S-NPP com frp_max ≥ τ_s  (≈ o que o Aqua vê)     fraco = o resto
r(c,M) = (Σfraco + λ·r_global(M)) / (Σforte + λ)
M2: pred_SNPP = k_forte(c,M)·A·(1 + r(c,M))   + termo aditivo onde A = 0
```
Registrar τ por estrato (tabela no Method: é um resultado físico interpretável). Entregar M1 e M2 do Pantanal ao Samuel às 22:00.

### 3.4 Melissa — incerteza C4 (sáb 23:30, roda à noite)
Bootstrap por blocos de ano: 200 vezes, sorteia anos de ajuste com reposição, reajusta a ponte e recalcula os meses convertidos. `lo`, `hi` = percentis 5 e 95. Meses nativos S-NPP: `lo = hi = valor`.
`low_conf = 1` se `(hi − lo)/valor > 0,5` ou `n < 5`, e em todo Terra nov/2000–jun/2002. Paralelizar com `joblib` por célula se lento.

### 3.5 Melissa — continuidade (dom 07:30–10:00)
Ponte N20 → S-NPP (M1, 2018–2025; razão medida 0,98) — não vai para 2026 (D33): serve para mostrar que o NOAA-20 harmonizado coincide com o S-NPP. Deriva: se o resíduo Aqua→S-NPP cresce com o ano, encurtar `fit` (R05).

### 3.6 Samuel — métrica e validação (sáb 15:00–23:30)
Como funciona: todo método é julgado igual — ajusta em alguns anos da sobreposição e prevê os anos que não viu (leave-one-year-out). Nunca dividir por linha (vaza informação entre meses do mesmo ano).
```python
# pipeline/validate/run.py
def score(pred, real):
    e = np.log((pred + 1) / (real + 1))
    return dict(consistency=float(np.median(np.abs(e))),
                r2_log=r2_score(np.log1p(real), np.log1p(pred)),
                bias=float(np.median(e)))                    # também por estação (sem bioma, D33)
for y in overlap_years:                                         # sem a pane do Aqua
    for name, m in {"raw": Identity(), "global": GlobalFactor(), "M1": M1(lam), "M2": M2(lam)}.items():
        m.fit(A, B, [t for t in overlap_years if t != y]); collect(name, y, m.transform(A_y), B_y)
```
Saída `validation.json`: por ponte e método → `consistency`, `r2_log`, `bias`, `n_test`, `vencedor`. Regra do CP3: vencedor tem de ganhar do bruto e do fator global; λ escolhido aqui.

### 3.7 Samuel — testes de homogeneidade (sáb 23:30 · dom 07:30)
Se a harmonização funcionou, a troca de satélite não deixa marca. Núcleo: **Pettitt** e **sazonalidade**; KS e pegada se der tempo (D24).
```python
def pettitt(x):                      # x = série anual de uma célula (25 valores)
    n = len(x); s = np.sign(np.subtract.outer(x, x))
    U = [s[:t+1, t+1:].sum() for t in range(n-1)]
    K = np.max(np.abs(U)); t = int(np.argmax(np.abs(U)))
    p = 2 * np.exp(-6 * K**2 / (n**3 + n**2))
    return t, min(p, 1.0)
```
Métrica: % de células com quebra (p < 0,05) em 2012 ± 1, **bruto × harmonizado** → `pettitt.json`. Sazonalidade: correlação do ciclo mensal médio 2003–2011 × 2013–2021.

### 3.8 Samuel — Fire Anomaly Score e pico (dom 07:30–10:00, D25)
O app calcula no navegador; Samuel escreve a **implementação de referência em Python** e 3 casos de teste (`tests/score_cases.json`) para a Luana conferir o JS.
```
Área A, mês do ano M, ano Y:  x = harm(A, Y, M);  H = {harm(A, y, M) : y ≠ Y}
Score = 100 · ( #{h < x} + 0,5·#{h = x} ) / |H|          (percentil empírico, 0–100)
Faixa:  < 60 normal · 60–85 acima · 85–95 muito acima · ≥ 95 extremo
Razão:  x / mediana(H)        Frase: "pior que 92% dos setembros desde 2001"
Pico:   P(M) = % dos anos completos em que M foi o mês de maior atividade
        Pico típico = M com maior P(M)   →  "Setembro foi o pico em 15 de 24 anos (63%)"
Chance (D27): normal = mediana(harm(A, y, M) em todos os anos)
        chance = % dos últimos 10 anos completos com harm(A, y, M) > normal  → "40% (4 de 10 anos)"
        < 5 anos com fogo em M → "dados insuficientes"
Mês padrão do score: o último mês da série (dez/2025) ou o mês clicado no calendário (D33: sem NRT)
```
É **comparação com o histórico** (climatologia, como o Twisters), não previsão (D21).

---
## 4. Front — Luana

### 4.1 Setup e deploy (sáb 15:00–19:00)
```bash
npm create vite@latest app -- --template vanilla
cd app && npm i leaflet leaflet-draw h3-js @observablehq/plot
```
`vite.config.js`: `base: '/Nasa-Space-App-Challenge_Grupo-Top-das-Galaxias/'` (com domínio próprio, `base: '/'`).
`.github/workflows/pages.yml`: `checkout@v4` → `setup-node@v4` → `npm ci && npm run build` (em `app/`) → `upload-pages-artifact@v3` (`app/dist`) → `deploy-pages@v4`; permissões `pages: write`, `id-token: write`. Testar o link em janela anônima e no celular.

### 4.2 Leitor do JSON (sáb 15:00)
```js
const D = await (await fetch(`${import.meta.env.BASE_URL}data/harm_monthly.json`)).json();
const areaSeries = (cells, key) => {                // soma mês a mês e divide por 10
  const out = new Float64Array(D.months.length);
  for (const c of cells) { const v = D[key][c]; if (v) v.forEach((x, i) => out[i] += x / 10); }
  return out;
};
```

### 4.3 Mapa, seleção e calendário (sáb 19:45–23:30 — início do app)
```js
const map = L.map('map').setView([-18.5, -57], 6);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {attribution: '© OpenStreetMap'}).addTo(map);
map.on(L.Draw.Event.CREATED, e => {
  const ring = e.layer.getLatLngs()[0].map(p => [p.lat, p.lng]);
  let cells = polygonToCells(ring, 4);                       // h3-js v4: [lat, lng]
  if (!cells.length) { const c = e.layer.getBounds().getCenter(); cells = [latLngToCell(c.lat, c.lng, 4)]; }
  render(cells);                                             // área menor que 1 hexágono → célula do centro
});
```
Calendário (linhas = anos, colunas = meses):
```js
Plot.plot({
  color: {scheme: 'cividis', type: 'sqrt', legend: true, domain: [0, vmax]},  // vmax = máx(bruto, harm)
  x: {tickFormat: m => 'JFMAMJJASOND'[m-1], label: null}, y: {label: null},
  marks: [Plot.cell(rows, {x: 'month', y: 'year', fill: 'value', inset: 0.5, tip: true}),
          Plot.dot(rows.filter(r => r.low_conf), {x: 'month', y: 'year', r: 1.5, fill: 'white'})]
})
```
**Mesmo `domain` no bruto e no harmonizado**: é isso que faz o salto de 2012 aparecer e sumir no toggle.

### 4.4 Toggle, série, incerteza, score (sáb 23:30 · dom 07:30–12:00)
| Componente | Como |
|---|---|
| Toggle | troca `key` entre `raw` e `cells` e redesenha |
| Série com emendas | `Plot.areaY(lo..hi, fillOpacity .3)` + `Plot.lineY(harm)` + `Plot.lineY(raw, strokeDasharray)` + `Plot.ruleX([2002-07, 2012-02])` com rótulo do satélite |
| Incerteza | soma de `lo`/`hi` das células (aproximação conservadora; declarar no Method) |
| Score | fórmula da §3.8; clicar num mês do calendário mostra o score daquele mês |
| Card de pico | "Peak usually in **Sep** (63% of years)" |
| Card de chance (D27) | "Historical chance this month ends above normal: **40%** (4 of 10 years)" — logo abaixo do score |
| 4 satélites (D33) | `Plot.lineY(sensors4, {x: 'year', y: 'value', stroke: 'sensor'})` — as 4 curvas harmonizadas se sobrepõem; a bruta fica tracejada |
| Áreas prontas | botões "Pantanal" e "São Paulo sugarcane" que carregam o polígono de `areas.json` |

### 4.5 CSV, Method, celular (dom 10:00–12:00)
```js
const csv = ['year,month,harmonized,lo,hi,raw,low_conf', ...rows.map(r => [r.year,r.month,r.value,r.lo,r.hi,r.raw,r.low_conf].join(','))].join('\n');
const a = Object.assign(document.createElement('a'), {href: URL.createObjectURL(new Blob([csv], {type: 'text/csv'})), download: 'fire_almanac_area.csv'}); a.click();
```
Method: tabela 5,42 → 3,45 → ≈1,0, τ por estrato, `validation.json`, `pettitt.json` (bruto × harm), limitações. Acessibilidade: cividis, contraste, foco por teclado, textos alternativos. Testar tudo em 375 px.

### 4.6 Telas do produto (padrão Twisters: uma pergunta, resposta em 10 s)
| Tela | Responde |
|---|---|
| 1. Hero + mapa | "Is fire in my area unusual right now, and when does it usually peak?" + botões das áreas prontas |
| 2. Resposta | Score + chance acima do normal + frase + card de pico + calendário |
| 3. Prova | Toggle bruto × harmonizado + série com emendas + incerteza |
| 4. Method | Como funciona + números de validação + dataset aberto |

---
## 5. Integração e testes
| Teste | Dono | Quando |
|---|---|---|
| Conservação de focos (grade e agregado) | Murilo | CP2 |
| Contrato: JSON valida (vetores alinhados com `months`, inteiros) | Murilo | cada export |
| Razões 2025 reproduzidas | Melissa | CP2 |
| Vencedor > bruto e > fator global | Samuel | CP3 |
| Score JS = referência Python nos 3 casos | Luana + Samuel | CP5 |
| `make all` do zero em outra máquina | Samuel | dom 15–19 |
| Link em anônimo + celular | Luana | CP2, CP7, CP8 |

## 6. Submissão no formato Twisters (dom 15:00–19:00, Murilo)
| Campo | Conteúdo |
|---|---|
| Summary | Pergunta + quem usa + o que entrega + "25 years, 4 satellites, one consistent record" (+ "S-NPP went dark on Nov 2, 2026: our NOAA-20 harmonization shows the record can continue") |
| Demo | Vídeo ≤ 30 s: pergunta → área → resposta em 10 s → toggle 2012 → score |
| Project | Link curto do app (GitHub Pages ou domínio D17) |
| Details | Pipeline, harmonização em 3 etapas, validação, stack (Python/DuckDB/H3, Vite/Leaflet/Plot) |
| Use of AI | Por ferramenta e por finalidade (de `AI_USAGE.md`), como o Twisters |
| NASA Data | FIRMS MODIS C6.1 (Terra 2000–2025, Aqua 2002–2025), VIIRS 375 m (S-NPP 2012–2025, NOAA-20 2018–2025) |
| Partner/Other | OpenStreetMap, INPE (se V1), bibliotecas |

## 7. Por que isso chega à final (critérios)
| Critério | Onde ganhamos ponto |
|---|---|
| Impact | Persona concreta (brigada/Defesa Civil × produtor rural), áreas prontas, CSV para a chefia |
| Creativity | História do S-NPP apagado; limiar de FRP físico por estrato |
| Validity | Validação fora da amostra contra 2 baselines; Pettitt bruto × harm; incerteza por mês |
| Relevance | Cumpre todos os verbos do desafio: calendário harmonizado, área, mês atual × mediana, CSV, cores acessíveis |
| Presentation | Uma pergunta, resposta em 10 s, toggle visual, vídeo legendado, página completa |

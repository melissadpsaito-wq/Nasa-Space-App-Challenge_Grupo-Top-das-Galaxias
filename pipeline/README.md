# pipeline/

| Módulo | Etapa | Dono | Saída |
|---|---|---|---|
| `ingest.py`, `clean.py` | ingest + clean ✅ (`2e66d2e`) | Murilo | `data/clean/<sensor>/<ano>.parquet` + `filter_log.csv` |
| `grid.py` | grade 2 km por passagem + H3 res 4 (sem bioma, D33) ✅ Pantanal e Brasil 14/11 17:53 | Murilo | `data/interim/grid2km_pass.parquet`, `agg_monthly.parquet` |
| `bridges/` | interface `Bridge` ✅ · M1 ✅ (`m1.py`, `--eval`) · M2 · C4 · conferências: `check_method.py` (5,42 → 3,45 → 1,0, ΣFRP), `check_extra.py` (fogos extras do VIIRS), `m1_preview.py` (série dos 4 satélites) | Melissa | `data/processed/harm_series.parquet` |
| `validate/` | métrica, baselines, AI1 (M3) | Samuel | `validation.json` |
| `analytics/` | bateria C1 (Pettitt, KS, pegada, sazonalidade) | Samuel | `pettitt.json` |
| `export.py` | JSON do app (`harm_monthly`, `sensors4`), dataset aberto (NRT fora por D33) | Murilo | `app/public/data/`, `open/` |

Pendente: `extrair_paises.py` (citado em `docs/AI_USAGE.md`) ainda não está no repo — subir na Fase 0.
Regra R12: Melissa e Samuel não editam o mesmo módulo; a interface `Bridge` (`bridges/base.py`, `docs/CONTRATO-CIENCIA.md`) é o ponto de contato.

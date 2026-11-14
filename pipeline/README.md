# pipeline/

| Módulo | Etapa | Dono | Saída |
|---|---|---|---|
| `ingest.py`, `clean.py` | ingest + clean | Murilo | `data/clean/<sensor>/<ano>.parquet` |
| `grid.py` | grade 2 km por passagem + H3 res 4 + bioma | Murilo | `data/interim/` |
| `bridges/` | interface `Bridge`, M1, M2, C4 | Melissa | `data/processed/harm_series.parquet` |
| `validate/` | métrica, baselines, AI1 (M3) | Samuel | `validation.json` |
| `analytics/` | bateria C1 (Pettitt, KS, pegada, sazonalidade) | Samuel | `pettitt.json` |
| `export.py`, `nrt.py` | JSON do app, dataset aberto, NRT | Murilo | `app/public/data/`, `open/` |

Pendente: `extrair_paises.py` (citado em `docs/AI_USAGE.md`) ainda não está no repo — subir na Fase 0.
Regra R12: Melissa e Samuel não editam o mesmo módulo; a interface `Bridge` é o ponto de contato.

# data/ (fora do Git, fica no Drive da equipe)
| Pasta | Conteúdo | No Git? |
|---|---|---|
| `raw/` | ZIP/CSV do FIRMS e shapefile RESOLVE, nunca editados | não |
| `clean/` | Parquet por sensor/ano, schema único | não |
| `interim/` | grade 2 km, agregado H3, célula → bioma | não |
| `processed/` | série harmonizada + validação (gerado por `make all`) | sim, se < 50 MB |
Linhagem e regras: `docs/DATA_GOVERNANCE.md`.

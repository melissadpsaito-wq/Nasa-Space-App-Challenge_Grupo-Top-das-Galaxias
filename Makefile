# Pipeline Fire Almanac: ingest → grid → bridges → validate → analytics → export
# Cada alvo chama um script em pipeline/. Os scripts são escritos durante o evento.
PY ?= python

.PHONY: all ingest grid bridges validate analytics export test clean-data

all: ingest grid bridges validate analytics export

ingest:     ; $(PY) -m pipeline.ingest      # Dados  · raw → data/clean/<sensor>/<ano>.parquet
grid:       ; $(PY) -m pipeline.grid        # Dados  · grade 0,02° por passagem + H3 res 4 → data/interim/
bridges:    ; $(PY) -m pipeline.bridges     # Melissa · M1/M2/C4 → data/processed/harm_series.parquet
validate:   ; $(PY) -m pipeline.validate    # Samuel  · métrica, AI1 → validation.json
analytics:  ; $(PY) -m pipeline.analytics   # Samuel  · bateria C1 → pettitt.json
export:     ; $(PY) -m pipeline.export      # Dados  · → app/public/data/*.json, open/

test:       ; $(PY) -m pytest -q tests

# Fire Almanac — Harmonized MODIS + VIIRS Burning Activity Calendar

**NASA Space Apps Challenge 2026 · Challenge: Harmonization of MODIS and VIIRS Hot Spots · Local event: São Paulo, Brazil**

> On November 2, 2026, the S-NPP satellite stopped observing. Our hotspot record survived.

Fire Almanac harmonizes 25 years of NASA FIRMS active-fire hotspots from four satellites (Terra and Aqua MODIS, S-NPP and NOAA-20 VIIRS) into one consistent series, so the sensor of origin no longer matters. A static web app turns that series into a burning-activity calendar for any area the user draws.

## What it does
- Draw an area or enter lat/lon → burning calendar (year × month), most critical month and year, CSV download.
- Compares the current month with the historical median (Fire Anomaly Score, 0–100).
- Toggle **raw × harmonized** to see the false 2012 jump disappear.
- Shows uncertainty for every harmonized value.

## How the harmonization works (summary)
1. Both sensors aggregated on a common ~2 km grid per overpass (removes the pixel-size effect).
2. Fire Radiative Power threshold by biome × season × day/night (removes the sensitivity effect).
3. Residual calibrated per cell × month on overlap years; competing methods (ratio, physical FRP, gradient boosting) are chosen by out-of-sample validation.
4. Homogeneity test battery (Pettitt, Kolmogorov–Smirnov, spatial footprint, seasonality) at every satellite switch.

Details: [`docs/METHOD.md`](docs/METHOD.md) · Data: [`docs/DATA_GOVERNANCE.md`](docs/DATA_GOVERNANCE.md)

## Data
NASA FIRMS: MODIS Collection 6.1 (Terra, Aqua), VIIRS 375 m (S-NPP, NOAA-20). See [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md).

## Reproduce
```bash
cp .env.example .env        # add your FIRMS MAP_KEY
make all                    # ingest → grid → bridges → validate → analytics → export
cd app && npm install && npm run dev
```

## Team
Grupo Top das Galáxias — Escola Politécnica da USP: Murilo (captain, data), Melissa and Samuel (science), Luana (front-end). Roles in [`GOVERNANCE.md`](GOVERNANCE.md).

## Use of AI
Declared in [`docs/AI_USAGE.md`](docs/AI_USAGE.md), as required by Space Apps rules.

## License
MIT — see [`LICENSE`](LICENSE). Data © NASA FIRMS, used under NASA open data policy.

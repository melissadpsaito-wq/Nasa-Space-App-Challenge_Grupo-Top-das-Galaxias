"""Análise descritiva: os fogos "a mais" do VIIRS ficam perto de um incêndio que o MODIS viu ou são isolados?

Unidade S-NPP = fogo (célula de 0,02° por passagem, posição = média dos pixels; FRP = máximo).
Referência Aqua = detecções (pixels) do mesmo dia UTC e mesmo turno (D/N).
Distância = menor distância (km) do fogo S-NPP à detecção Aqua mais próxima.
Classes: mesmo fogo ≤ 2 km · vizinhança 2–10 km · isolado 10–50 km · muito isolado > 50 km.

Ressalva: "isolado" mistura (a) fogo pequeno que o MODIS não detecta e (b) lugar que o Aqua não observou
naquele dia (faixa do MODIS é mais estreita e tem falhas perto do Equador; nuvens). Não é método: não muda D13.

Duas medidas para separar "fogo que o MODIS não vê" de "lugar que o Aqua não observou no dia":
  · janela do mês: distância ao Aqua mais próximo no mesmo mês e turno (qualquer dia). O que segue > 50 km é
    lugar onde o Aqua não registrou fogo no mês inteiro.
  · casamento inverso: % dos fogos do Aqua com um pixel S-NPP a ≤ 2 km na mesma janela. Se o dia der ~50%,
    os dois satélites muitas vezes não observam o mesmo lugar no mesmo dia (faixa, horário, nuvem).

Uso (raiz do repo):
    python -m pipeline.bridges.check_extra --clean data/clean --year 2025
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.bridges import base
from pipeline.bridges.check_method import load_clean

R_EARTH = 6371.0
BINS = [0, 2, 10, 50, np.inf]
LABELS = ["mesmo fogo (≤2 km)", "vizinhança (2–10 km)", "isolado (10–50 km)", "muito isolado (>50 km)"]


def xyz(lat, lon) -> np.ndarray:
    la, lo = np.radians(np.asarray(lat, float)), np.radians(np.asarray(lon, float))
    return np.column_stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]) * R_EARTH


def nearest_km(q: np.ndarray, ref: np.ndarray) -> np.ndarray:
    """Menor distância (corda ≈ arco para < 100 km) de cada ponto de q ao conjunto ref."""
    if len(ref) == 0:
        return np.full(len(q), np.inf)
    try:
        from scipy.spatial import cKDTree
        return cKDTree(ref).query(q, k=1)[0]
    except ImportError:
        out = np.empty(len(q))
        chunk = max(1, int(4e6 // len(ref)))                    # limita a memória (~100 MB por bloco)
        for i in range(0, len(q), chunk):
            d = ((q[i:i + chunk, None, :] - ref[None, :, :]) ** 2).sum(-1)
            out[i:i + chunk] = np.sqrt(d.min(1))
        return out


def snpp_fires(snpp: pd.DataFrame, g: float = 0.02) -> pd.DataFrame:
    d = snpp.assign(gy=np.floor(snpp.latitude / g).astype("int64"), gx=np.floor(snpp.longitude / g).astype("int64"))
    return d.groupby(["ts", "daynight", "gy", "gx"], as_index=False, sort=False).agg(
        latitude=("latitude", "mean"), longitude=("longitude", "mean"), frp_max=("frp", "max"), n_pix=("frp", "size"))


def _key(ts: pd.Series, window: str) -> pd.Series:
    return ts.dt.normalize() if window == "day" else ts.dt.to_period("M").dt.start_time


def _nearest_by_group(q: pd.DataFrame, ref: pd.DataFrame, window: str) -> np.ndarray:
    """Para cada linha de q: menor distância (km) a ref na mesma janela (dia ou mês) e turno."""
    q, ref = q.assign(k=_key(q.ts, window)), ref.assign(k=_key(ref.ts, window))
    groups = {k: xyz(v.latitude, v.longitude) for k, v in ref.groupby(["k", "daynight"])}
    dist = np.empty(len(q))
    for key, idx in q.groupby(["k", "daynight"]).groups.items():
        sub = q.loc[idx]
        dist[q.index.get_indexer(idx)] = nearest_km(xyz(sub.latitude, sub.longitude), groups.get(key, np.empty((0, 3))))
    return dist


def classify(aqua: pd.DataFrame, snpp: pd.DataFrame, window: str = "day") -> pd.DataFrame:
    """Uma linha por fogo S-NPP com dist_km à detecção Aqua mais próxima (mesma janela e turno) e classe."""
    f = snpp_fires(snpp)
    f["dist_km"] = _nearest_by_group(f, aqua, window)
    f["classe"] = pd.cut(f.dist_km, BINS, labels=LABELS, right=True, include_lowest=True)
    return f


def reverse_match(aqua: pd.DataFrame, snpp: pd.DataFrame, window: str = "day") -> pd.DataFrame:
    """% dos fogos do Aqua (células 0,02° × passagem) com pixel S-NPP a ≤ 2 km e ≤ 10 km, por turno."""
    a = snpp_fires(aqua)
    a["dist_km"] = _nearest_by_group(a, snpp, window)
    g = a.groupby("daynight").dist_km
    out = pd.DataFrame({"fogos_aqua": g.size(), "pct_ate_2km": g.apply(lambda d: 100 * (d <= 2).mean()),
                        "pct_ate_10km": g.apply(lambda d: 100 * (d <= 10).mean())})
    tot = pd.DataFrame({"fogos_aqua": [len(a)], "pct_ate_2km": [100 * (a.dist_km <= 2).mean()],
                        "pct_ate_10km": [100 * (a.dist_km <= 10).mean()]}, index=["total"])
    return pd.concat([out, tot])


def summarize(f: pd.DataFrame, n_aqua_fires: int, cfg: dict | None = None) -> dict[str, pd.DataFrame]:
    tot = len(f)
    t = f.groupby("classe", observed=False).agg(fogos=("frp_max", "size"), frp_mediano=("frp_max", "median"),
                                                pixels_por_fogo=("n_pix", "mean"),
                                                noite=("daynight", lambda s: (s == "N").mean()))
    t["pct_fogos"] = 100 * t.fogos / tot
    t["por_fogo_aqua"] = t.fogos / max(n_aqua_fires, 1)        # quanto cada classe soma à razão S-NPP/Aqua
    dn = (f.groupby(["daynight", "classe"], observed=False).size().unstack().pipe(lambda x: 100 * x.div(x.sum(axis=1), axis=0)))
    out = {"classes": t[["fogos", "pct_fogos", "por_fogo_aqua", "frp_mediano", "pixels_por_fogo", "noite"]],
           "por_turno_pct": dn}
    if cfg is not None:
        s = f.assign(season=base.season_of(f.ts.dt.month, cfg))
        out["por_trimestre_pct"] = (s.groupby(["season", "classe"], observed=False).size().unstack()
                                     .pipe(lambda x: 100 * x.div(x.sum(axis=1), axis=0)))
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Fogos extras do VIIRS: perto de um incêndio do MODIS ou isolados?")
    ap.add_argument("--clean", default="data/clean")
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--out", default="data/interim/previa")
    ap.add_argument("--config", default=str(base.CONFIG))
    a = ap.parse_args(argv)
    cfg = base.load_config(a.config)
    aqua = load_clean(Path(a.clean), "AQUA", a.year)
    snpp = load_clean(Path(a.clean), "SNPP", a.year)
    n_aqua_fires = len(snpp_fires(aqua))                      # Aqua também contado por célula 0,02° × passagem
    pd.set_option("display.width", 160)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res = {}
    for window, label in (("day", "mesmo dia"), ("month", "mesmo mês")):
        f = classify(aqua, snpp, window)
        r = summarize(f, n_aqua_fires, cfg)
        res[window] = r["classes"]
        if window == "day":
            print(f"{a.clean} · {a.year} · fogos S-NPP {len(f):,} · fogos Aqua {n_aqua_fires:,} · razão {len(f) / n_aqua_fires:.2f}\n")
        print(f"=== Janela: {label} e turno ===")
        print(r["classes"].round(2).to_string())
        print("\n% por turno:\n" + r["por_turno_pct"].round(1).to_string())
        print("\n% por trimestre:\n" + r["por_trimestre_pct"].round(1).to_string())
        print(f"\nCasamento inverso ({label}): fogos do Aqua com pixel S-NPP por perto")
        print(reverse_match(aqua, snpp, window).round(1).to_string() + "\n")
        r["classes"].to_csv(out / f"extra_fires_{a.year}_{window}.csv")
    comp = pd.DataFrame({"% dia": res["day"].pct_fogos, "% mês": res["month"].pct_fogos,
                         "razão dia": res["day"].por_fogo_aqua, "razão mês": res["month"].por_fogo_aqua})
    print("=== Comparação dia × mês (% dos fogos S-NPP e contribuição para a razão S-NPP/Aqua) ===")
    print(comp.round(2).to_string())
    print(f"\n→ {out / f'extra_fires_{a.year}_day.csv'} e _month.csv")

if __name__ == "__main__":
    main()

from __future__ import annotations

import os
import math
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Index,
    select,
    func,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


# -----------------------------
# DB schema
# -----------------------------
metadata = MetaData()

recommendation_events = Table(
    "recommendation_events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),

    # when the recommendation was actually used/accepted (UTC)
    Column("event_ts", DateTime(timezone=True), nullable=False, index=True),

    # context
    Column("product_category", String(128), nullable=True),   # e.g., dairy, beverages
    Column("product_id", String(64), nullable=True),

    # chosen material
    Column("material_id", String(64), nullable=False),
    Column("material_name", String(256), nullable=True),

    # predictions (per unit)
    Column("pred_cost_per_unit_usd", Float, nullable=False),
    Column("pred_co2_per_unit_kg", Float, nullable=False),

    # volume used (units) - unit depends on your UI (packs, cartons, etc.)
    Column("volume_units", Float, nullable=False),

    # derived totals for convenience
    Column("total_cost_usd", Float, nullable=False),
    Column("total_co2_kg", Float, nullable=False),
)

Index("ix_reco_events_ts_cat", recommendation_events.c.event_ts, recommendation_events.c.product_category)


def get_engine(database_url: Optional[str] = None) -> Engine:
    url = database_url or os.getenv("DATABASE_URL") or "sqlite:///ecopackai_events.db"
    # pool_pre_ping helps with stale DB connections on Postgres
    return create_engine(url, pool_pre_ping=True, future=True)


def init_db(engine: Optional[Engine] = None) -> None:
    """
    Creates tables if they don't exist.
    Safe to call at app startup.
    """
    engine = engine or get_engine()
    metadata.create_all(engine)
    logger.info("DB initialized (tables ensured).")


# -----------------------------
# Event logging
# -----------------------------
def log_recommendation_event(
    *,
    engine: Optional[Engine] = None,
    event_ts: Optional[datetime] = None,
    product_category: Optional[str] = None,
    product_id: Optional[str] = None,
    material_id: str,
    material_name: Optional[str],
    pred_cost_per_unit_usd: float,
    pred_co2_per_unit_kg: float,
    volume_units: float,
) -> int:
    """
    Store a REAL usage event when user selects/applies a recommendation.

    Returns inserted row id.
    """
    engine = engine or get_engine()
    init_db(engine)

    # normalize
    ts = event_ts or datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    cat = (product_category or "").strip().lower() or None

    # validate numeric inputs
    def _num(x: Any, lo: float = 0.0) -> float:
        try:
            v = float(x)
        except Exception:
            v = 0.0
        return max(lo, v)

    cost_u = _num(pred_cost_per_unit_usd, 0.0)
    co2_u = _num(pred_co2_per_unit_kg, 0.0)
    vol = _num(volume_units, 0.0)

    total_cost = cost_u * vol
    total_co2 = co2_u * vol

    try:
        with engine.begin() as conn:
            res = conn.execute(
                recommendation_events.insert().values(
                    event_ts=ts,
                    product_category=cat,
                    product_id=(str(product_id).strip() if product_id else None),
                    material_id=str(material_id),
                    material_name=(str(material_name).strip() if material_name else None),
                    pred_cost_per_unit_usd=cost_u,
                    pred_co2_per_unit_kg=co2_u,
                    volume_units=vol,
                    total_cost_usd=total_cost,
                    total_co2_kg=total_co2,
                )
            )
            inserted_id = int(res.inserted_primary_key[0])
            logger.info(f"Logged recommendation event id={inserted_id}")
            return inserted_id
    except SQLAlchemyError as e:
        logger.exception("Failed to insert recommendation event.")
        raise RuntimeError(f"DB insert failed: {e}") from e


# -----------------------------
# Time-series building
# -----------------------------
def _normalize_freq(freq: str) -> str:
    f = (freq or "M").upper().strip()
    if f in ("M", "MS"):
        return "M"  # monthly buckets
    if f in ("W", "W-SUN", "W-MON"):
        return "W"
    if f in ("D",):
        return "D"
    return "M"


def fetch_event_timeseries(
    *,
    engine: Optional[Engine] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    product_category: Optional[str] = None,
    material_id: Optional[str] = None,
    freq: str = "M",
) -> pd.DataFrame:
    """
    Returns aggregated time series with columns:
      ds, volume_units, total_cost_usd, total_co2_kg

    ds is period end timestamp (Pandas convention for M/W/D buckets).
    """
    engine = engine or get_engine()
    init_db(engine)

    freq = _normalize_freq(freq)
    cat = (product_category or "").strip().lower() or None

    # Basic query
    stmt = select(
        recommendation_events.c.event_ts,
        recommendation_events.c.volume_units,
        recommendation_events.c.total_cost_usd,
        recommendation_events.c.total_co2_kg,
        recommendation_events.c.product_category,
        recommendation_events.c.material_id,
    )

    # Filters
    if start is not None:
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        stmt = stmt.where(recommendation_events.c.event_ts >= start)

    if end is not None:
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        stmt = stmt.where(recommendation_events.c.event_ts <= end)

    if cat is not None:
        stmt = stmt.where(func.lower(recommendation_events.c.product_category) == cat)

    if material_id is not None:
        stmt = stmt.where(recommendation_events.c.material_id == str(material_id))

    with engine.begin() as conn:
        rows = conn.execute(stmt).fetchall()

    if not rows:
        return pd.DataFrame(columns=["ds", "volume_units", "total_cost_usd", "total_co2_kg"])

    df = pd.DataFrame(rows, columns=["event_ts", "volume_units", "total_cost_usd", "total_co2_kg", "product_category", "material_id"])
    df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)

    # bucket by freq
    if freq == "M":
        df["ds"] = df["event_ts"].dt.to_period("M").dt.to_timestamp("M")
    elif freq == "W":
        # week ending Sunday by default
        df["ds"] = df["event_ts"].dt.to_period("W").dt.to_timestamp("W")
    else:  # "D"
        df["ds"] = df["event_ts"].dt.to_period("D").dt.to_timestamp("D")

    agg = df.groupby("ds", as_index=False)[["volume_units", "total_cost_usd", "total_co2_kg"]].sum()

    # fill missing periods between min and max
    full = pd.date_range(start=agg["ds"].min(), end=agg["ds"].max(), freq=("M" if freq == "M" else "W" if freq == "W" else "D"))
    full_df = pd.DataFrame({"ds": full})
    out = full_df.merge(agg, on="ds", how="left").fillna(0.0)

    return out


# -----------------------------
# Forecasting
# -----------------------------
@dataclass
class FitResult:
    method: str
    residual_std: float
    slope: float
    intercept: float


def _fit_linear(y: np.ndarray) -> FitResult:
    """
    Robust baseline: linear trend fit on index [0..n-1].
    """
    n = len(y)
    x = np.arange(n, dtype=float)
    if n < 2 or float(np.nanstd(y)) == 0.0:
        # constant fallback
        intercept = float(np.nanmean(y)) if n > 0 else 0.0
        return FitResult("constant", residual_std=0.0, slope=0.0, intercept=intercept)

    slope, intercept = np.polyfit(x, y, 1)
    preds = slope * x + intercept
    resid = y - preds
    std = float(np.nanstd(resid))
    return FitResult("linear", residual_std=std, slope=float(slope), intercept=float(intercept))


def _forecast_linear(fit: FitResult, periods: int, start_index: int) -> np.ndarray:
    idx = np.arange(start_index, start_index + periods, dtype=float)
    yhat = fit.slope * idx + fit.intercept
    # no negative totals
    return np.maximum(yhat, 0.0)


def _monte_carlo_band(
    mean_series: np.ndarray,
    residual_std: float,
    simulations: int = 500,
    lower_q: float = 0.1,
    upper_q: float = 0.9,
) -> Dict[str, List[float]]:
    """
    Adds Gaussian noise using residual std to generate interval bands.
    """
    if residual_std <= 0:
        return {
            "p10": mean_series.tolist(),
            "p50": mean_series.tolist(),
            "p90": mean_series.tolist(),
        }

    draws = []
    rng = np.random.default_rng(42)
    for _ in range(simulations):
        noise = rng.normal(0.0, residual_std, size=len(mean_series))
        s = np.maximum(mean_series + noise, 0.0)
        draws.append(s)

    sims = np.vstack(draws)  # shape: (simulations, T)
    return {
        "p10": np.quantile(sims, lower_q, axis=0).tolist(),
        "p50": np.quantile(sims, 0.5, axis=0).tolist(),
        "p90": np.quantile(sims, upper_q, axis=0).tolist(),
    }


def generate_forecast_from_events(
    *,
    engine: Optional[Engine] = None,
    horizon_periods: int = 6,
    freq: str = "M",
    product_category: Optional[str] = None,
    material_id: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    simulations: int = 500,
) -> Dict[str, Any]:
    """
    Forecast based on REAL recommendation events stored in DB.

    Returns:
      {
        "series": [...history rows...],
        "forecast": [...future rows...],
        "bands": {"volume_units": {...}, "total_cost_usd": {...}, "total_co2_kg": {...}},
        "meta": {...}
      }
    """
    engine = engine or get_engine()
    freq = _normalize_freq(freq)

    history = fetch_event_timeseries(
        engine=engine,
        start=start,
        end=end,
        product_category=product_category,
        material_id=material_id,
        freq=freq,
    )

    if history.empty or len(history) < 2:
        return {
            "series": history.to_dict(orient="records") if not history.empty else [],
            "forecast": [],
            "bands": {},
            "meta": {
                "method": "insufficient_data",
                "message": "Not enough historical events to forecast. Log more recommendation events first.",
                "horizon_periods": horizon_periods,
                "freq": freq,
            },
        }

    # Fit per metric
    metrics = ["volume_units", "total_cost_usd", "total_co2_kg"]
    fits: Dict[str, FitResult] = {}
    means_future: Dict[str, np.ndarray] = {}

    for m in metrics:
        y = history[m].astype(float).to_numpy()
        fit = _fit_linear(y)
        fits[m] = fit
        means_future[m] = _forecast_linear(fit, horizon_periods, start_index=len(y))

    # future ds index
    last_ds = pd.to_datetime(history["ds"].max(), utc=True)
    if freq == "M":
        future_ds = pd.period_range(last_ds.to_period("M") + 1, periods=horizon_periods, freq="M").to_timestamp("M")
    elif freq == "W":
        future_ds = pd.period_range(last_ds.to_period("W") + 1, periods=horizon_periods, freq="W").to_timestamp("W")
    else:
        future_ds = pd.period_range(last_ds.to_period("D") + 1, periods=horizon_periods, freq="D").to_timestamp("D")

    forecast_df = pd.DataFrame({"ds": pd.to_datetime(future_ds, utc=True)})
    for m in metrics:
        forecast_df[m] = means_future[m]

    # Bands
    bands = {}
    for m in metrics:
        bands[m] = _monte_carlo_band(means_future[m], fits[m].residual_std, simulations=simulations)

    # Extra derived KPIs (per-unit estimates)
    # Avoid division by 0
    forecast_df["cost_per_unit_usd_est"] = forecast_df["total_cost_usd"] / forecast_df["volume_units"].replace(0, np.nan)
    forecast_df["co2_per_unit_kg_est"] = forecast_df["total_co2_kg"] / forecast_df["volume_units"].replace(0, np.nan)
    forecast_df = forecast_df.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    meta = {
        "method": {m: fits[m].method for m in metrics},
        "residual_std": {m: fits[m].residual_std for m in metrics},
        "horizon_periods": horizon_periods,
        "freq": freq,
        "filters": {
            "product_category": (product_category.strip().lower() if product_category else None),
            "material_id": material_id,
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
        },
        "history_points": int(len(history)),
    }

    return {
        "series": history.to_dict(orient="records"),
        "forecast": forecast_df.to_dict(orient="records"),
        "bands": bands,
        "meta": meta,
    }


# -----------------------------
# Convenience: quick dashboard rollups
# -----------------------------

def generate_plan_impact_forecast(
    *,
    engine: Optional[Engine] = None,
    planned: List[Dict[str, Any]],
    simulations: int = 500,
    product_category: Optional[str] = None,
    material_id: Optional[str] = None,
    freq: str = "M",
) -> Dict[str, Any]:
    """
    Plan-based forecast.

    The UI supplies a future plan in tons per period (typically months):
      planned = [{"period":"YYYY-MM", "volumeTons": 1.2}, ...]

    We convert tons -> kg and forecast *per-kg* cost and CO2 from historical
    recommendation events, then multiply by the planned volume.

    Returns mean series plus p10/p50/p90 bands via Monte-Carlo simulation.
    """
    engine = engine or get_engine()
    freq = _normalize_freq(freq)

    if not planned:
        raise ValueError("planned must be a non-empty list")

    history = fetch_event_timeseries(
        engine=engine,
        start=None,
        end=None,
        product_category=product_category,
        material_id=material_id,
        freq=freq,
    )

    if history.empty:
        raise ValueError("No historical data found for forecasting. Log more recommendation events first.")

    # Use only periods where we have non-zero volume to compute per-kg metrics.
    vol = history["volume_units"].astype(float).to_numpy()
    cost = history["total_cost_usd"].astype(float).to_numpy()
    co2 = history["total_co2_kg"].astype(float).to_numpy()

    mask = vol > 0
    if mask.sum() < 3:
        raise ValueError(
            "Not enough non-zero historical periods to forecast per-kg metrics. "
            "Generate more recommendations across multiple months first."
        )

    vol_nz = vol[mask]
    cost_nz = cost[mask]
    co2_nz = co2[mask]

    eps = 1e-9
    cost_per_kg = cost_nz / (vol_nz + eps)
    co2_per_kg = co2_nz / (vol_nz + eps)

    # Fit and forecast per-kg series
    fit_cost = _fit_linear(cost_per_kg)
    fit_co2 = _fit_linear(co2_per_kg)

    horizon = len(planned)
    mean_cost_per_kg_future = _forecast_linear(fit_cost, horizon, start_index=len(cost_per_kg))
    mean_co2_per_kg_future = _forecast_linear(fit_co2, horizon, start_index=len(co2_per_kg))

    # Convert plan: tons -> kg
    labels: List[str] = []
    volume_kg: List[float] = []
    for item in planned:
        period = str(item.get("period", "")).strip()
        tons = float(item.get("volumeTons", 0.0))
        if not period:
            raise ValueError("Each planned item must include a non-empty 'period' like '2026-02'")
        if tons < 0:
            raise ValueError("volumeTons must be non-negative")
        labels.append(period)
        volume_kg.append(tons * 1000.0)

    volume_kg_arr = np.array(volume_kg, dtype=float)

    # Mean totals
    mean_total_cost = mean_cost_per_kg_future * volume_kg_arr
    mean_total_co2 = mean_co2_per_kg_future * volume_kg_arr

    # Bands for per-kg metrics (use existing helper)
    bands_cost_per_kg = _monte_carlo_band(mean_cost_per_kg_future, fit_cost.residual_std, simulations=simulations)
    bands_co2_per_kg = _monte_carlo_band(mean_co2_per_kg_future, fit_co2.residual_std, simulations=simulations)

    # Bands for totals: simulate per-kg and multiply by volume plan
    rng = np.random.default_rng(42)
    std_cost = max(fit_cost.residual_std, 1e-9)
    std_co2 = max(fit_co2.residual_std, 1e-9)

    sims_cost_per_kg = rng.normal(loc=mean_cost_per_kg_future, scale=std_cost, size=(simulations, horizon))
    sims_co2_per_kg = rng.normal(loc=mean_co2_per_kg_future, scale=std_co2, size=(simulations, horizon))

    sims_total_cost = sims_cost_per_kg * volume_kg_arr
    sims_total_co2 = sims_co2_per_kg * volume_kg_arr

    def qbands(arr: np.ndarray) -> Dict[str, List[float]]:
        return {
            "p10": np.quantile(arr, 0.10, axis=0).tolist(),
            "p50": np.quantile(arr, 0.50, axis=0).tolist(),
            "p90": np.quantile(arr, 0.90, axis=0).tolist(),
        }

    return {
        "labels": labels,
        "inputs": {
            "volume_kg": volume_kg,
            "count_periods": horizon,
            "freq": freq,
        },
        "history": history.to_dict(orient="records"),
        "per_kg": {
            "cost_usd_per_kg": {
                "mean": mean_cost_per_kg_future.tolist(),
                "bands": bands_cost_per_kg,
                "meta": {"method": fit_cost.method, "residual_std": fit_cost.residual_std},
            },
            "co2_kg_per_kg": {
                "mean": mean_co2_per_kg_future.tolist(),
                "bands": bands_co2_per_kg,
                "meta": {"method": fit_co2.method, "residual_std": fit_co2.residual_std},
            },
        },
        "totals": {
            "total_cost_usd": {"mean": mean_total_cost.tolist(), "bands": qbands(sims_total_cost)},
            "total_co2_kg": {"mean": mean_total_co2.tolist(), "bands": qbands(sims_total_co2)},
        },
    }


def get_material_usage_trends(
    *,
    engine: Optional[Engine] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    product_category: Optional[str] = None,
    top_n: int = 10,
) -> Dict[str, Any]:
    """
    Returns total volume per material (top N) for BI dashboards.
    """
    engine = engine or get_engine()
    init_db(engine)

    cat = (product_category or "").strip().lower() or None

    stmt = select(
        recommendation_events.c.material_id,
        recommendation_events.c.material_name,
        func.sum(recommendation_events.c.volume_units).label("volume_units"),
        func.sum(recommendation_events.c.total_cost_usd).label("total_cost_usd"),
        func.sum(recommendation_events.c.total_co2_kg).label("total_co2_kg"),
    )

    if start is not None:
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        stmt = stmt.where(recommendation_events.c.event_ts >= start)

    if end is not None:
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        stmt = stmt.where(recommendation_events.c.event_ts <= end)

    if cat is not None:
        stmt = stmt.where(func.lower(recommendation_events.c.product_category) == cat)

    stmt = stmt.group_by(recommendation_events.c.material_id, recommendation_events.c.material_name)
    stmt = stmt.order_by(func.sum(recommendation_events.c.volume_units).desc())
    stmt = stmt.limit(int(max(1, top_n)))

    with engine.begin() as conn:
        rows = conn.execute(stmt).fetchall()

    labels = []
    volumes = []
    costs = []
    co2s = []
    for r in rows:
        name = r.material_name or r.material_id
        labels.append(str(name))
        volumes.append(float(r.volume_units or 0.0))
        costs.append(float(r.total_cost_usd or 0.0))
        co2s.append(float(r.total_co2_kg or 0.0))

    return {
        "labels": labels,
        "volume_units": volumes,
        "total_cost_usd": costs,
        "total_co2_kg": co2s,
        "count": len(labels),
    }

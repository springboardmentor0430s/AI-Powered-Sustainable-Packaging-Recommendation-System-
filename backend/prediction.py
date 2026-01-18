from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent

# models/
if (CURRENT_DIR / "models").exists():
    MODELS_DIR = CURRENT_DIR / "models"
elif (PARENT_DIR / "models").exists():
    MODELS_DIR = PARENT_DIR / "models"
else:
    MODELS_DIR = CURRENT_DIR / "models"

# DB/ (csv folder)
if (CURRENT_DIR / "DB").exists():
    CSV_DIR_PATH = CURRENT_DIR / "DB"
else:
    CSV_DIR_PATH = PARENT_DIR / "DB"


def _db_url_from_env() -> str:
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL", "")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASS", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "ecopackai")
    safe_pass = quote_plus(password)
    return f"postgresql://{user}:{safe_pass}@{host}:{port}/{name}"


def get_db_engine():
    return create_engine(_db_url_from_env())


_cost_model = None
_co2_model = None
_materials_raw: Optional[pd.DataFrame] = None
_expected_feature_cols: Optional[List[str]] = None


def _minmax(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    mn, mx = s.min(), s.max()
    if pd.isna(mn) or pd.isna(mx) or mn == mx:
        return pd.Series(0.5, index=series.index)
    return (s - mn) / (mx - mn)


def _clamp(v, lo: float, hi: float, default: float) -> float:
    try:
        v = float(v)
    except Exception:
        return default
    return max(lo, min(hi, v))


def _load_raw_materials() -> pd.DataFrame:
    # Try DB first (materials table)
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        df = pd.read_sql("SELECT * FROM materials", engine)
        logger.info("Loaded raw materials from DB (%d rows).", len(df))
        return df
    except Exception as e:
        logger.warning("DB load failed for materials (%s). Falling back to CSV.", e)

    csv_path = CSV_DIR_PATH / "ecopackai_materials.csv"
    if not csv_path.exists():
        raise RuntimeError(f"Missing materials CSV: {csv_path}")
    df = pd.read_csv(csv_path).dropna(how="all").copy()
    logger.info("Loaded raw materials from CSV (%d rows).", len(df))
    return df


def _infer_expected_cols_from_pipeline(pipe) -> List[str]:
    """
    IMPORTANT:
    train_models.py builds the Pipeline with step name 'preprocessor' (not 'preprocess').
    We read feature_names_in_ from the ColumnTransformer if available.
    """
    try:
        pre = pipe.named_steps.get("preprocessor", None)
        cols = list(getattr(pre, "feature_names_in_", []))
        return cols or []
    except Exception:
        return []


def load_models() -> None:
    global _cost_model, _co2_model, _materials_raw, _expected_feature_cols

    if _cost_model is not None and _co2_model is not None and _materials_raw is not None:
        return

    manifest_path = MODELS_DIR / "model_manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"Missing {manifest_path}. Run train_models.py first.")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    cost_file = manifest["best_models"]["cost"]["file"]
    co2_file = manifest["best_models"]["co2"]["file"]

    cost_path = MODELS_DIR / cost_file
    co2_path = MODELS_DIR / co2_file
    if not cost_path.exists() or not co2_path.exists():
        raise RuntimeError(f"Model files missing: {cost_path} or {co2_path}")

    _cost_model = joblib.load(cost_path)
    _co2_model = joblib.load(co2_path)
    logger.info("Loaded COST pipeline: %s", cost_path.name)
    logger.info("Loaded CO2  pipeline: %s", co2_path.name)

    _materials_raw = _load_raw_materials()

    cols_cost = _infer_expected_cols_from_pipeline(_cost_model)
    cols_co2 = _infer_expected_cols_from_pipeline(_co2_model)
    cols = sorted(set(cols_cost) | set(cols_co2))
    _expected_feature_cols = cols if cols else None


def _build_inference_frame(product: Dict[str, float], materials: pd.DataFrame) -> pd.DataFrame:
    """
    Build inference feature frame:
    - Start with material rows (one per material)
    - Add product-side fields as constant columns
    - IMPORTANT: map frontend 'category' into training feature name 'ProductCategory'
    """
    df = materials.copy()

    # ---- Product-side inputs (with clamps/defaults) ----
    weight = _clamp(product.get("weightKg", 1.0), 0.05, 1000.0, 1.0)
    fragility = _clamp(product.get("fragility", 5), 1.0, 10.0, 5.0)
    moisture_req = _clamp(product.get("moistureReq", 5), 0.0, 10.0, 5.0)
    oxygen_sens = _clamp(product.get("oxygenSensitivity", 5), 0.0, 10.0, 5.0)
    budget = _clamp(product.get("maxBudget", 10.0), 0.0, 1e9, 10.0)
    ship_km = _clamp(product.get("shippingDistance", 500.0), 0.0, 1e9, 500.0)

    pref_bio = int(_clamp(product.get("preferredBiodegradable", 0), 0.0, 1.0, 0.0))
    pref_rec = int(_clamp(product.get("preferredRecyclable", 0), 0.0, 1.0, 0.0))

    # ---- CRITICAL: category mapping for trained pipeline ----
    # Frontend/back-end use `category`, training feature is `ProductCategory`
    category_val = str(product.get("category", "missing")).strip() or "missing"
    df["ProductCategory"] = category_val

    # ---- Product features used in training ----
    df["Weight_KG"] = weight
    df["RequiredStrength_Level"] = fragility
    df["MoistureRequired"] = moisture_req
    df["OxygenSensitivity"] = oxygen_sens
    df["MaxBudgetPerUnit_USD"] = budget
    df["ShippingDistance_KM"] = ship_km
    df["FragilityLevel"] = fragility
    df["PreferredBiodegradable"] = pref_bio
    df["PreferredRecyclable"] = pref_rec

    # ---- Ensure numeric where expected ----
    for c in ["StrengthRating", "MoistureBarrier", "OxygenBarrier", "CostPerKG_USD", "CO2_Emissions_KG_Per_Ton"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # ---- Derived features (consistent with your existing logic) ----
    df["strength_gap"] = df.get("StrengthRating", 0) - df["RequiredStrength_Level"]
    df["moisture_gap"] = df.get("MoistureBarrier", 0) - df["MoistureRequired"]
    df["oxygen_gap"] = df.get("OxygenBarrier", 0) - df["OxygenSensitivity"]

    material_cost = df.get("CostPerKG_USD", 0).fillna(0) * df["Weight_KG"]
    df["budget_gap"] = df["MaxBudgetPerUnit_USD"] - material_cost

    df["is_strength_insufficient"] = (df["strength_gap"] < 0).astype(int)
    df["is_moisture_insufficient"] = (df["moisture_gap"] < 0).astype(int)
    df["is_oxygen_insufficient"] = (df["oxygen_gap"] < 0).astype(int)
    df["is_over_budget"] = (df["budget_gap"] < 0).astype(int)

    df["logistics_risk"] = df["FragilityLevel"] * df["ShippingDistance_KM"]
    df["sustainability_pref_score"] = (0.5 * df["PreferredBiodegradable"] + 0.5 * df["PreferredRecyclable"])

    # ---- If we could infer expected columns, enforce exact order and pad missing ----
    if _expected_feature_cols:
        for col in _expected_feature_cols:
            if col not in df.columns:
                df[col] = 0
        df = df[_expected_feature_cols].copy()

    return df


def _compute_indices_and_scores(
    materials: pd.DataFrame,
    pred_cost: np.ndarray,
    pred_co2: np.ndarray,
    weights: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """
    Compute cost/CO₂ indices and derive suitability and ranking scores.

    A caller can provide custom weighting via the `weights` parameter.  The expected
    keys are ``co2`` and ``cost``, which control the weighting of CO₂ and cost
    contributions in the MaterialSuitabilityScore.  Any remainder weight is applied
    to the risk/constraint component.  The values should sum to 1.0, but if they
    don't the function will normalise them so that co2 + cost <= 1 and the
    remainder goes to risk.  If ``weights`` is None, default weights of
    0.50 (co2), 0.35 (cost) and 0.15 (risk) are used.
    """
    df = materials.copy()
    df["predicted_cost_unit_usd"] = np.maximum(pred_cost.astype(float), 0.0)
    df["predicted_co2_unit_kg"] = np.maximum(pred_co2.astype(float), 0.0)

    df["CostEfficiencyIndex"] = (1 - _minmax(df["predicted_cost_unit_usd"])) * 100
    df["CO2ImpactIndex"] = (1 - _minmax(df["predicted_co2_unit_kg"])) * 100

    # Determine weighting
    if weights is None:
        w_co2, w_cost = 0.50, 0.35
    else:
        w_co2 = float(weights.get("co2", 0.50))
        w_cost = float(weights.get("cost", 0.35))
        # Clamp negative or invalid weights
        if w_co2 < 0:
            w_co2 = 0.0
        if w_cost < 0:
            w_cost = 0.0
        # Normalise so that co2 + cost <= 1; risk gets the rest
        total = w_co2 + w_cost
        if total > 1.0:
            w_co2 /= total
            w_cost /= total
    w_risk = 1.0 - (w_co2 + w_cost)
    # risk weight cannot be negative; if it is, set to zero and renormalise
    if w_risk < 0:
        w_risk = 0.0
        total = w_co2 + w_cost + w_risk
        if total > 0:
            w_co2 /= total
            w_cost /= total

    # Compute suitability.  The risk component uses (100 - 25 * is_strength_insufficient)
    # as a simple proxy for meeting constraints.  The penalty later will
    # subtract for other insufficiencies.
    df["MaterialSuitabilityScore"] = (
        w_co2 * df["CO2ImpactIndex"] +
        w_cost * df["CostEfficiencyIndex"] +
        w_risk * (100 - 25 * df.get("is_strength_insufficient", 0))
    ).clip(0, 100)

    # Penalty for constraint violations (applied after weighting).  The penalty
    # values remain fixed; the custom weights only affect the base suitability.
    penalty = (
        25 * df.get("is_strength_insufficient", 0) +
        20 * df.get("is_moisture_insufficient", 0) +
        20 * df.get("is_oxygen_insufficient", 0) +
        25 * df.get("is_over_budget", 0)
    )
    df["MaterialSuitabilityScore"] = (df["MaterialSuitabilityScore"] - penalty).clip(0, 100)

    # Final ranking still considers suitability predominantly, but ensures that
    # variations in CO₂ and cost indices influence the sort order.  These weights
    # remain constant regardless of custom weights; altering the suitability
    # weights already adjusts the ranking implicitly.
    df["RankingScore"] = (
        0.60 * df["MaterialSuitabilityScore"] +
        0.20 * df["CO2ImpactIndex"] +
        0.20 * df["CostEfficiencyIndex"]
    ).clip(0, 100)

    return df


def _build_reason(row: pd.Series) -> str:
    """
    Build a concise summary for the top‑level recommendation.  This helper
    preserves the existing behaviour of tagging a material as having a low
    CO₂ footprint, being cost efficient, over budget or lacking strength.
    It is intentionally brief and used for quick labels.  See
    `_build_detailed_explanation` for a more thorough explanation of why a
    material was selected.

    :param row: A row from the scored DataFrame containing prediction
        indices and constraint flags.
    :return: A comma‑separated string of tags summarising the material.
    """
    tags: List[str] = []
    # Low emissions if CO2ImpactIndex is in top 30th percentile (>=70)
    if float(row.get("CO2ImpactIndex", 0)) >= 70:
        tags.append("Low CO₂ footprint")
    # Cost efficient if cost index is in top 30th percentile (>=70)
    if float(row.get("CostEfficiencyIndex", 0)) >= 70:
        tags.append("Cost efficient")
    # Flag constraints explicitly
    if int(row.get("is_over_budget", 0)) == 1:
        tags.append("Over budget")
    if int(row.get("is_strength_insufficient", 0)) == 1:
        tags.append("Strength may be insufficient")
    return ", ".join(tags) if tags else "Optimised for sustainability and cost."


def _build_detailed_explanation(row: pd.Series) -> Dict[str, str]:
    """
    Construct a detailed, plain‑language explanation describing why a given
    material was selected.  The explanation includes comments on cost,
    CO₂ emissions, strength, moisture and oxygen barriers, and sustainability
    attributes.  Each field is expressed as a short sentence for ease of
    consumption by end users and screen readers.

    :param row: A row from the scored DataFrame containing prediction
        indices and constraint flags.
    :return: A dict with keys 'cost', 'co2', 'strength', 'moisture',
        'oxygen' and 'sustainability', mapping to explanatory sentences.
    """
    explanation: Dict[str, str] = {}
    # --- Cost explanation ---
    cost_gap = float(row.get("budget_gap", 0))
    # predicted_cost_unit_usd may not be set on this row yet when called
    predicted_cost = float(row.get("predicted_cost_unit_usd", row.get("predicted_cost", 0) or 0))
    if cost_gap >= 0:
        explanation["cost"] = (
            f"Estimated cost ({predicted_cost:.2f} USD/unit) is within the budget, "
            f"leaving {cost_gap:.2f} USD headroom."
        )
    else:
        explanation["cost"] = (
            f"Estimated cost ({predicted_cost:.2f} USD/unit) exceeds the budget by "
            f"{abs(cost_gap):.2f} USD."
        )
    # --- CO₂ explanation ---
    co2_idx = float(row.get("CO2ImpactIndex", 0))
    predicted_co2 = float(row.get("predicted_co2_unit_kg", row.get("predicted_co2", 0) or 0))
    if co2_idx >= 70:
        explanation["co2"] = (
            f"CO₂ emissions are low compared to alternatives ({predicted_co2:.2f} kg/unit)."
        )
    elif co2_idx <= 40:
        explanation["co2"] = (
            f"CO₂ emissions are relatively high ({predicted_co2:.2f} kg/unit)."
        )
    else:
        explanation["co2"] = (
            f"CO₂ emissions are moderate ({predicted_co2:.2f} kg/unit)."
        )
    # --- Strength explanation ---
    strength_gap = float(row.get("strength_gap", 0))
    if strength_gap >= 0:
        explanation["strength"] = "Strength rating meets or exceeds the product's requirement."
    else:
        explanation["strength"] = "Strength rating is below the product's requirement."
    # --- Moisture explanation ---
    moisture_gap = float(row.get("moisture_gap", 0))
    if moisture_gap >= 0:
        explanation["moisture"] = "Moisture barrier meets or exceeds the product's moisture requirement."
    else:
        explanation["moisture"] = "Moisture barrier is below the product's moisture requirement."
    # --- Oxygen explanation ---
    oxygen_gap = float(row.get("oxygen_gap", 0))
    if oxygen_gap >= 0:
        explanation["oxygen"] = "Oxygen barrier meets or exceeds the product's oxygen sensitivity."
    else:
        explanation["oxygen"] = "Oxygen barrier is below the product's oxygen sensitivity."
    # --- Sustainability explanation ---
    # Materials may have binary flags for biodegradable and recyclable in the raw
    # dataset.  If present, use them to comment on sustainability; otherwise
    # provide generic remarks based on the CO₂ and cost indices.
    bio_flag = row.get("Biodegradable", None)
    rec_flag = row.get("Recyclable", None)
    sustainable_tags: List[str] = []
    try:
        if int(bio_flag) == 1:
            sustainable_tags.append("biodegradable")
    except Exception:
        pass
    try:
        if int(rec_flag) == 1:
            sustainable_tags.append("recyclable")
    except Exception:
        pass
    if sustainable_tags:
        explanation["sustainability"] = (
            f"Material is {' and '.join(sustainable_tags)}."
        )
    else:
        # fallback if no binary flags
        if co2_idx >= 70:
            explanation["sustainability"] = "Overall sustainability is strong due to low emissions."
        else:
            explanation["sustainability"] = "No explicit sustainability certifications available."
    return explanation


def recommend(product: Dict[str, float], weights: Optional[Dict[str, float]] = None) -> List[Dict[str, object]]:
    load_models()
    assert _materials_raw is not None
    assert _cost_model is not None
    assert _co2_model is not None

    # Features for ML prediction (includes ProductCategory now)
    X = _build_inference_frame(product, _materials_raw)

    pred_cost = _cost_model.predict(X)
    pred_co2 = _co2_model.predict(X)

    # --------------------------------------------------------------------------
    # Apply filtering criteria based on user parameters and sustainability goals.
    # We want to discard materials that exceed the user's maxBudget or produce
    # disproportionately high CO₂ emissions relative to their peers.  We use the
    # median predicted CO₂ value as a reasonable threshold for “low emitters”.
    co2_values = np.maximum(pred_co2.astype(float), 0.0)
    cost_values = np.maximum(pred_cost.astype(float), 0.0)
    max_budget = float(product.get("maxBudget", 1e9))
    co2_threshold = float(np.median(co2_values)) if co2_values.size else float("inf")
    valid_mask = (cost_values <= max_budget) & (co2_values <= co2_threshold)
    # If no materials satisfy both constraints, relax the CO₂ threshold but still
    # enforce the budget to avoid returning unfeasible options.
    if not valid_mask.any():
        valid_mask = cost_values <= max_budget

    # Filter out materials and corresponding predictions to evaluate only valid
    # candidates.  This prevents high-emission or over-budget materials from
    # appearing in the recommendation list.
    filtered_materials = _materials_raw[valid_mask].copy()
    filtered_cost = pred_cost[valid_mask]
    filtered_co2 = pred_co2[valid_mask]

    # Scoring frame (human-readable ranking + constraints) for valid materials
    scored = filtered_materials.copy()

    for c in ["StrengthRating", "MoistureBarrier", "OxygenBarrier", "CostPerKG_USD"]:
        if c in scored.columns:
            scored[c] = pd.to_numeric(scored[c], errors="coerce")

    scored["Weight_KG"] = float(product.get("weightKg", 1.0))
    scored["RequiredStrength_Level"] = float(product.get("fragility", 5))
    scored["MoistureRequired"] = float(product.get("moistureReq", 5))
    scored["OxygenSensitivity"] = float(product.get("oxygenSensitivity", 5))
    scored["MaxBudgetPerUnit_USD"] = float(product.get("maxBudget", 10.0))

    scored["strength_gap"] = scored.get("StrengthRating", 0) - scored["RequiredStrength_Level"]
    scored["moisture_gap"] = scored.get("MoistureBarrier", 0) - scored["MoistureRequired"]
    scored["oxygen_gap"] = scored.get("OxygenBarrier", 0) - scored["OxygenSensitivity"]
    scored["budget_gap"] = scored["MaxBudgetPerUnit_USD"] - (scored.get("CostPerKG_USD", 0).fillna(0) * scored["Weight_KG"])

    scored["is_strength_insufficient"] = (scored["strength_gap"] < 0).astype(int)
    scored["is_moisture_insufficient"] = (scored["moisture_gap"] < 0).astype(int)
    scored["is_oxygen_insufficient"] = (scored["oxygen_gap"] < 0).astype(int)
    scored["is_over_budget"] = (scored["budget_gap"] < 0).astype(int)

    # Only compute indices and scores on the filtered predictions
    scored = _compute_indices_and_scores(scored, filtered_cost, filtered_co2, weights=weights)

    results: List[Dict[str, object]] = []
    for _, row in scored.iterrows():
        predicted_cost = float(row["predicted_cost_unit_usd"])
        predicted_co2 = float(row["predicted_co2_unit_kg"])
        # Build concise and detailed explanations
        reason = _build_reason(row)
        detailed_expl = _build_detailed_explanation(row)
        # Confidence is derived from the material suitability score (0–100).  We
        # bound it between 0 and 100 and round to one decimal place for display.
        confidence = float(row["MaterialSuitabilityScore"])
        confidence = max(0.0, min(100.0, confidence))

        results.append(
            {
                "materialName": row.get("MaterialName", "Unknown"),
                "materialType": row.get("MaterialType", "Unknown"),
                "rankingScore": float(row["RankingScore"]),
                "suitabilityScore": float(row["MaterialSuitabilityScore"]),
                "predictedCost": predicted_cost,
                "predictedCO2": predicted_co2,
                # simple reason for quick consumption
                "reason": reason,
                "recommendationReason": reason,
                # detailed explanation as a nested dict
                "explanation": detailed_expl,
                # Confidence score expressed as percentage
                "confidenceScore": round(confidence, 1),
                # legacy field names for backwards compatibility
                "predictedCostUSD": predicted_cost,
                "predictedCO2KG": predicted_co2,
                "co2ImpactIndex": float(row["CO2ImpactIndex"]),
                "costEfficiencyIndex": float(row["CostEfficiencyIndex"]),
            }
        )

    # Sort by ranking score descending and return top five
    results.sort(key=lambda x: x["rankingScore"], reverse=True)
    return results[:5]


def compute_dashboard_metrics() -> Dict[str, object]:
    load_models()
    assert _materials_raw is not None
    df = _materials_raw.copy()

    df["InnovationLevel"] = pd.to_numeric(df.get("InnovationLevel"), errors="coerce")
    df["CO2_Emissions_KG_Per_Ton"] = pd.to_numeric(df.get("CO2_Emissions_KG_Per_Ton"), errors="coerce")
    df["CostPerKG_USD"] = pd.to_numeric(df.get("CostPerKG_USD"), errors="coerce")

    df = df.dropna(subset=["InnovationLevel"])
    if df.empty:
        return {
            "co2Reduction": {"labels": ["Q1", "Q2", "Q3", "Q4"], "values": [0, 0, 0, 0]},
            "costSavings": {"labels": ["Q1", "Q2", "Q3", "Q4"], "values": [0, 0, 0, 0]},
            "materialUsage": {"labels": [], "values": []},
        }

    df["innovation_quartile"] = pd.qcut(df["InnovationLevel"], 4, labels=["Q1", "Q2", "Q3", "Q4"])

    co2_by_q = df.groupby("innovation_quartile")["CO2_Emissions_KG_Per_Ton"].mean()
    cost_by_q = df.groupby("innovation_quartile")["CostPerKG_USD"].mean()

    worst_co2 = float(co2_by_q.max())
    worst_cost = float(cost_by_q.max())
    co2_reduction_pct = (1 - (co2_by_q / worst_co2)).fillna(0) * 100
    cost_savings = (worst_cost - cost_by_q).fillna(0)

    usage = df["MaterialType"].fillna("Unknown").value_counts(normalize=True) * 100

    return {
        "co2Reduction": {"labels": co2_reduction_pct.index.astype(str).tolist(), "values": co2_reduction_pct.round(2).tolist()},
        "costSavings": {"labels": cost_savings.index.astype(str).tolist(), "values": cost_savings.round(2).tolist()},
        "materialUsage": {"labels": usage.index.astype(str).tolist(), "values": usage.round(2).tolist()},
    }

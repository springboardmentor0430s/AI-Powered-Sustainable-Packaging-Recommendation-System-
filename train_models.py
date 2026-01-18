from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, GroupShuffleSplit, KFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler
from sklearn.linear_model import ElasticNetCV
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    StackingRegressor,
    ExtraTreesRegressor,
)

try:
    from xgboost import XGBRegressor
except ImportError:
    raise ImportError("XGBoost not found. Please install: pip install xgboost")


# ---------------------- Global Config ----------------------
TARGET_COST = "estimated_cost_per_unit_usd"
TARGET_CO2 = "estimated_co2_per_unit_kg"
PAIR_CSV = "product_material_features.csv"
MODELS_PREFIX = "ecopackai"
DEFAULT_MODELS_DIR = Path("models")


# ---------------------- Logging Setup ----------------------
def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )


# ---------------------- Data Loading ----------------------
def load_data(csv_dir: Path) -> pd.DataFrame:
    path = (csv_dir / PAIR_CSV).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at: {path}")
    df = pd.read_csv(path)
    logging.info(f"Loaded dataset: {path.name} ({len(df)} rows)")
    return df


def validate_schema(df: pd.DataFrame) -> None:
    missing = [t for t in (TARGET_COST, TARGET_CO2) if t not in df.columns]
    if missing:
        raise ValueError(f"Missing targets in dataset: {missing}")


# ---------------------- Feature Engineering ----------------------
def create_interaction_features(X: pd.DataFrame) -> pd.DataFrame:
    df = X.copy()

    if "Weight_KG" in df.columns and "ShippingDistance_KM" in df.columns:
        df["logistics_work"] = df["Weight_KG"].astype(float) * df["ShippingDistance_KM"].astype(float)

    if "StrengthRating" in df.columns and "RequiredStrength_Level" in df.columns:
        sr = df["StrengthRating"].astype(float)
        req = df["RequiredStrength_Level"].astype(float)
        df["strength_efficiency"] = sr / (req + 1e-3)

    if "BiodegradabilityScore" in df.columns and "RecyclabilityPercentage" in df.columns:
        b = df["BiodegradabilityScore"].astype(float)
        r = df["RecyclabilityPercentage"].astype(float)
        df["eco_score_total"] = b + r
        df["eco_score_mult"] = b * r

    return df


def add_log_numeric_features(X: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    df = X.copy()
    for c in cols:
        if c in df.columns:
            v = pd.to_numeric(df[c], errors="coerce")
            df[f"log1p_{c}"] = np.log1p(np.maximum(v.fillna(0.0).to_numpy(), 0.0))
    return df


def remove_collinear_features(X: pd.DataFrame, threshold: float = 0.995) -> pd.DataFrame:
    numeric_df = X.select_dtypes(include=["number"])
    if numeric_df.shape[1] < 2:
        return X

    corr_matrix = numeric_df.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop = [column for column in upper.columns if any(upper[column] > threshold)]

    if to_drop:
        logging.info(f"Dropped {len(to_drop)} redundant features: {to_drop}")
        return X.drop(columns=to_drop)

    return X


# ---------------------- Preprocessor ----------------------
def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    cat_cols = X.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    num_cols = [c for c in X.columns if c not in cat_cols]

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", RobustScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, num_cols),
            ("cat", categorical_transformer, cat_cols),
        ],
        verbose_feature_names_out=False,
    )


# ---------------------- Model Architecture ----------------------
def _meta_learner(random_state: int) -> ElasticNetCV:
    return ElasticNetCV(
        l1_ratio=[0.1, 0.5, 0.9],
        alphas=100,
        cv=5,
        random_state=random_state,
        max_iter=5000,
    )


def make_cost_model(random_state: int) -> StackingRegressor:
    estimators = [
        ("rf", RandomForestRegressor(
            n_estimators=800,
            max_depth=None,
            min_samples_leaf=1,
            random_state=random_state,
            n_jobs=-1,
        )),
        ("et", ExtraTreesRegressor(
            n_estimators=1200,
            max_depth=None,
            min_samples_leaf=1,
            random_state=random_state,
            n_jobs=-1,
        )),
        ("xgb", XGBRegressor(
            n_estimators=6000,
            learning_rate=0.01,
            max_depth=8,
            min_child_weight=2,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.0,
            reg_lambda=1.0,
            n_jobs=-1,
            random_state=random_state,
            objective="reg:squarederror",
        )),
        ("gb", GradientBoostingRegressor(
            n_estimators=1200,
            learning_rate=0.03,
            max_depth=5,
            random_state=random_state,
        )),
    ]

    return StackingRegressor(
        estimators=estimators,
        final_estimator=_meta_learner(random_state),
        cv=KFold(n_splits=5, shuffle=True, random_state=random_state),
        n_jobs=-1,
        passthrough=True,
    )


def make_co2_model(random_state: int) -> StackingRegressor:
    estimators = [
        ("rf", RandomForestRegressor(
            n_estimators=800,
            max_depth=None,
            min_samples_split=3,
            min_samples_leaf=1,
            max_features="sqrt",
            random_state=random_state,
            n_jobs=-1,
        )),
        ("et", ExtraTreesRegressor(
            n_estimators=1400,
            max_depth=None,
            min_samples_split=3,
            min_samples_leaf=1,
            random_state=random_state,
            n_jobs=-1,
        )),
        ("xgb", XGBRegressor(
            n_estimators=8000,
            learning_rate=0.008,
            max_depth=9,
            min_child_weight=2,
            subsample=0.75,
            colsample_bytree=0.75,
            reg_alpha=0.05,
            reg_lambda=1.0,
            gamma=0.0,
            n_jobs=-1,
            random_state=random_state,
            objective="reg:squarederror",
        )),
        ("gb", GradientBoostingRegressor(
            n_estimators=1500,
            learning_rate=0.02,
            max_depth=6,
            random_state=random_state,
        )),
    ]

    return StackingRegressor(
        estimators=estimators,
        final_estimator=_meta_learner(random_state),
        cv=KFold(n_splits=5, shuffle=True, random_state=random_state),
        n_jobs=-1,
        passthrough=True,
    )


def wrap_log_target(model: Any) -> TransformedTargetRegressor:
    return TransformedTargetRegressor(
        regressor=model,
        func=np.log1p,
        inverse_func=np.expm1,
        check_inverse=False,
    )


# ---------------------- Metrics ----------------------
def _mean_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(y_pred - y_true))


def get_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    me = _mean_error(y_true, y_pred)
    r2 = float(r2_score(y_true, y_pred))
    return {
        "rmse": rmse,
        "mae": mae,
        "me": me,
        "r2": r2,
        "accuracy_pct": float(max(0.0, r2) * 100.0),
    }


def evaluate_holdout(
    pipe: Pipeline,
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_test: pd.DataFrame,
    y_test: np.ndarray,
    target_name: str
) -> Dict[str, Any]:
    logging.info(f"Fitting optimized ensemble for {target_name}...")
    pipe.fit(X_train, y_train)

    pred_train = pipe.predict(X_train)
    pred_test = pipe.predict(X_test)

    pred_train = np.maximum(0.0, pred_train)
    pred_test = np.maximum(0.0, pred_test)

    train_metrics = get_metrics(y_train, pred_train)
    test_metrics = get_metrics(y_test, pred_test)

    logging.info(f"----- {target_name} RESULTS (Holdout) -----")
    logging.info(
        f"Train R2: {train_metrics['r2']:.4f} | Acc: {train_metrics['accuracy_pct']:.2f}% | "
        f"RMSE: {train_metrics['rmse']:.4f} | MAE: {train_metrics['mae']:.4f} | ME: {train_metrics['me']:.4f}"
    )
    logging.info(
        f"Test  R2: {test_metrics['r2']:.4f} | Acc: {test_metrics['accuracy_pct']:.2f}% | "
        f"RMSE: {test_metrics['rmse']:.4f} | MAE: {test_metrics['mae']:.4f} | ME: {test_metrics['me']:.4f}"
    )
    logging.info("-" * 50)

    return {
        "train": train_metrics,
        "test": test_metrics,
    }


def cross_validate_r2(
    pipe: Pipeline,
    X: pd.DataFrame,
    y: np.ndarray,
    random_state: int,
    target_name: str
) -> Tuple[float, float]:
    cv = KFold(n_splits=5, shuffle=True, random_state=random_state)
    scores = cross_val_score(pipe, X, y, scoring="r2", cv=cv, n_jobs=-1)
    mean_r2 = float(scores.mean())
    std_r2 = float(scores.std())
    logging.info(f"----- {target_name} CV (5-fold) -----")
    logging.info(f"Mean R2: {mean_r2:.4f} | Std: {std_r2:.4f} | Mean Acc: {max(0.0, mean_r2)*100:.2f}%")
    logging.info("-" * 50)
    return mean_r2, std_r2


# ---------------------- Split Strategy ----------------------
def split_data(
    df: pd.DataFrame,
    X: pd.DataFrame,
    y_cost: np.ndarray,
    y_co2: np.ndarray,
    test_size: float,
    random_state: int,
    group_col: Optional[str],
) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if group_col and group_col in df.columns:
        groups = df[group_col].astype(str).fillna("missing_group").values
        gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
        train_idx, test_idx = next(gss.split(X, y_cost, groups=groups))
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_cost_train, y_cost_test = y_cost[train_idx], y_cost[test_idx]
        y_co2_train, y_co2_test = y_co2[train_idx], y_co2[test_idx]
        logging.info(f"Using GroupShuffleSplit on '{group_col}'.")
        return X_train, X_test, y_cost_train, y_cost_test, y_co2_train, y_co2_test

    logging.info("Using standard random 80/20 split.")
    X_train, X_test, y_cost_train, y_cost_test, y_co2_train, y_co2_test = train_test_split(
        X, y_cost, y_co2,
        test_size=test_size,
        random_state=random_state,
        shuffle=True,
    )
    return X_train, X_test, y_cost_train, y_cost_test, y_co2_train, y_co2_test


# ---------------------- Main Execution ----------------------
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-data-dir", type=Path, default=Path("DB"))
    parser.add_argument("--models-dir", type=Path, default=DEFAULT_MODELS_DIR)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.20)
    parser.add_argument("--group-col", type=str, default="ProductID",
                        help="If present, use group split to reduce leakage (e.g., ProductID or MaterialID).")
    parser.add_argument("--run-cv", action="store_true",
                        help="Run 5-fold CV R2 on the full pipeline (recommended).")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    configure_logging(args.verbose)
    args.models_dir.mkdir(parents=True, exist_ok=True)

    try:
        df = load_data(args.csv_data_dir)
        validate_schema(df)
    except Exception as e:
        logging.error(e)
        return

    y_cost = pd.to_numeric(df[TARGET_COST], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    y_co2 = pd.to_numeric(df[TARGET_CO2], errors="coerce").fillna(0.0).to_numpy(dtype=float)

    id_cols = ["MaterialID", "ProductID", "RecommendationID"]
    X = df.drop(columns=id_cols + [TARGET_COST, TARGET_CO2], errors="ignore")

    logging.info("Engineering features...")
    X = create_interaction_features(X)

    likely_skew_cols = [
        "Weight_KG", "ShippingDistance_KM", "Volume_cm3", "Thickness_mm",
        "Area_cm2", "Density", "ManufacturingEnergy_kwh"
    ]
    X = add_log_numeric_features(X, likely_skew_cols)

    X = remove_collinear_features(X, threshold=0.995)

    X_train, X_test, y_cost_train, y_cost_test, y_co2_train, y_co2_test = split_data(
        df=df,
        X=X,
        y_cost=y_cost,
        y_co2=y_co2,
        test_size=args.test_size,
        random_state=args.random_state,
        group_col=args.group_col,
    )

    logging.info(f"Training Set: {len(X_train)} | Test Set: {len(X_test)}")

    results_summary: Dict[str, Any] = {}

    # ---------------------- COST ----------------------
    cost_model = make_cost_model(args.random_state)
    cost_pipe = Pipeline([
        ("preprocessor", build_preprocessor(X_train)),
        ("model", wrap_log_target(cost_model)),
    ])

    if args.run_cv:
        mean_r2, std_r2 = cross_validate_r2(cost_pipe, X, y_cost, args.random_state, "COST")
        results_summary.setdefault("cost", {})
        results_summary["cost"]["cv"] = {"mean_r2": mean_r2, "std_r2": std_r2}

    cost_eval = evaluate_holdout(cost_pipe, X_train, y_cost_train, X_test, y_cost_test, "COST")
    cost_filename = f"{MODELS_PREFIX}_cost_stacking_cv_passthrough.joblib"
    joblib.dump(cost_pipe, args.models_dir / cost_filename)
    results_summary.setdefault("cost", {})
    results_summary["cost"]["holdout"] = cost_eval

    # ---------------------- CO2 ----------------------
    co2_model = make_co2_model(args.random_state)
    co2_pipe = Pipeline([
        ("preprocessor", build_preprocessor(X_train)),
        ("model", wrap_log_target(co2_model)),
    ])

    if args.run_cv:
        mean_r2, std_r2 = cross_validate_r2(co2_pipe, X, y_co2, args.random_state, "CO2")
        results_summary.setdefault("co2", {})
        results_summary["co2"]["cv"] = {"mean_r2": mean_r2, "std_r2": std_r2}

    co2_eval = evaluate_holdout(co2_pipe, X_train, y_co2_train, X_test, y_co2_test, "CO2")
    co2_filename = f"{MODELS_PREFIX}_co2_stacking_cv_passthrough.joblib"
    joblib.dump(co2_pipe, args.models_dir / co2_filename)
    results_summary.setdefault("co2", {})
    results_summary["co2"]["holdout"] = co2_eval

    # Save full metrics
    with open(args.models_dir / "final_metrics.json", "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)

    # Save manifest that prediction.py expects
    manifest = {
        "best_models": {
            "cost": {"file": cost_filename},
            "co2": {"file": co2_filename},
        },
        "targets": {
            "cost": TARGET_COST,
            "co2": TARGET_CO2,
        },
        "prefix": MODELS_PREFIX,
    }
    with open(args.models_dir / "model_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    cost_test_r2 = results_summary["cost"]["holdout"]["test"]["r2"]
    co2_test_r2 = results_summary["co2"]["holdout"]["test"]["r2"]

    logging.info("\n Training Complete.")
    logging.info(f"COST Accuracy: {results_summary['cost']['holdout']['test']['accuracy_pct']:.2f}% (R2={cost_test_r2:.4f})")
    logging.info(f"CO2  Accuracy: {results_summary['co2']['holdout']['test']['accuracy_pct']:.2f}% (R2={co2_test_r2:.4f})")
    logging.info(f"Models saved to: {args.models_dir.resolve()}")
    logging.info("Manifest saved to: %s", (args.models_dir / "model_manifest.json").resolve())


if __name__ == "__main__":
    main()

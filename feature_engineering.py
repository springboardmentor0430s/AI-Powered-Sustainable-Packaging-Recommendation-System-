from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler


# --- Configuration ---
SOURCE_TABLES = {
    "materials": "ecopackai_materials.csv",
    "products": "ecopackai_products.csv",
    "recommendations": "ecopackai_recommendations.csv",
}

REQUIRED_COLUMNS = {
    "materials": {
        "MaterialID", "CO2_Emissions_KG_Per_Ton", "CostPerKG_USD",
        "BiodegradabilityScore", "RecyclabilityPercentage", "StrengthRating",
        "MoistureBarrier", "OxygenBarrier", "ChemicalResistance",
        "ScaleRating", "InnovationLevel", "Durability_Months",
        "MaterialType", "CompostableStatus",
    },
    "products": {
        "ProductID", "ProductCategory", "FragilityLevel",
        "ShippingDistance_KM", "PreferredBiodegradable", "PreferredRecyclable",
        "Weight_KG", "RequiredStrength_Level", "MoistureRequired",
        "OxygenSensitivity", "MaxBudgetPerUnit_USD",
    },
    "recommendations": {"ProductID", "MaterialID"},
}

PLOT_ID_COLS = {"MaterialID", "ProductID", "RecommendationID"}


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s | %(levelname)s | %(message)s")


def ensure_columns(df: pd.DataFrame, required: set, name: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {name}: {sorted(missing)}")


def load_source_tables(csv_dir: Path) -> Tuple[Dict[str, pd.DataFrame], bool]:
    csv_dir = csv_dir.resolve()
    tables: Dict[str, pd.DataFrame] = {}

    for name, filename in SOURCE_TABLES.items():
        path = csv_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing data CSV: {path}")
        df = pd.read_csv(path)

        ensure_columns(df, REQUIRED_COLUMNS[name], name)
        tables[name] = df
        logging.info(f"Loaded {len(df)} rows from CSV '{filename}'")

    return tables, True


def plot_numeric_distributions(tables: Dict[str, pd.DataFrame], output_dir: Path) -> None:
    """
    Save histogram + boxplot for each numeric column in each table.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    for table_name, df in tables.items():
        if df is None or df.empty:
            logging.warning(f"Skipping plots for '{table_name}': no data.")
            continue

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        plot_cols = [c for c in numeric_cols if c not in PLOT_ID_COLS]

        if not plot_cols:
            logging.info(f"No numeric columns to plot for '{table_name}' after excluding IDs.")
            continue

        table_dir = output_dir / table_name
        table_dir.mkdir(parents=True, exist_ok=True)

        for col in plot_cols:
            series = pd.to_numeric(df[col], errors="coerce").dropna()
            if series.empty:
                logging.info(f"Skipping '{table_name}.{col}': empty after dropping NaNs.")
                continue

            # Histogram
            plt.figure()
            plt.hist(series.values, bins=30)
            plt.title(f"{table_name}: {col} (hist)")
            plt.xlabel(col)
            plt.ylabel("count")
            hist_path = table_dir / f"{table_name}_{col}_hist.png"
            plt.savefig(hist_path, bbox_inches="tight")
            plt.close()

            # Boxplot
            plt.figure()
            plt.boxplot(series.values, vert=True)
            plt.title(f"{table_name}: {col} (box)")
            plt.ylabel(col)
            box_path = table_dir / f"{table_name}_{col}_box.png"
            plt.savefig(box_path, bbox_inches="tight")
            plt.close()


def min_max(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    mn, mx = s.min(), s.max()
    if pd.isna(mn) or pd.isna(mx) or mn == mx:
        return pd.Series(0.5, index=series.index)
    return (s - mn) / (mx - mn)


def log_score_distribution(df: pd.DataFrame, col: str) -> None:
    if col not in df.columns:
        logging.warning(f"Column {col} not found for sanity check.")
        return
    stats = pd.to_numeric(df[col], errors="coerce").describe()
    logging.info(
        f"STATS for '{col}': Min={stats['min']:.2f} | Max={stats['max']:.2f} | Mean={stats['mean']:.2f}"
    )


def engineer_material_features(materials: pd.DataFrame) -> pd.DataFrame:
    df = materials.copy()

    df["co2_impact_index"] = (1 - min_max(df["CO2_Emissions_KG_Per_Ton"])) * 100
    df["cost_efficiency_index"] = (1 - min_max(df["CostPerKG_USD"])) * 100

    df["sustainability_score"] = min_max(
        0.4 * (df["BiodegradabilityScore"] / 100) +
        0.3 * (df["RecyclabilityPercentage"] / 100) +
        0.3 * (df["co2_impact_index"] / 100)
    ) * 100

    df["protection_score"] = min_max(
        0.4 * min_max(df["StrengthRating"]) +
        0.2 * min_max(df["MoistureBarrier"]) +
        0.2 * min_max(df["OxygenBarrier"]) +
        0.2 * min_max(df["ChemicalResistance"])
    ) * 100

    df["business_score"] = min_max(
        0.4 * (df["ScaleRating"] / 10) +
        0.4 * (df["InnovationLevel"] / 10) +
        0.2 * min_max(df["Durability_Months"])
    ) * 100

    df["eco_fit_score"] = min_max(
        0.4 * df["sustainability_score"] +
        0.3 * df["protection_score"] +
        0.2 * df["business_score"] +
        0.1 * df["cost_efficiency_index"]
    ) * 100

    # One-hot for ML
    df = pd.get_dummies(df, columns=["MaterialType", "CompostableStatus"], drop_first=True)

    # Scale numeric cols (0-1) excluding ID
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if "MaterialID" in numeric_cols:
        numeric_cols.remove("MaterialID")
    if numeric_cols:
        df[numeric_cols] = MinMaxScaler().fit_transform(df[numeric_cols])

    return df


def engineer_product_features(products: pd.DataFrame) -> pd.DataFrame:
    df = products.copy()

    df["logistics_risk"] = df["FragilityLevel"] * df["ShippingDistance_KM"]
    df["sustainability_pref_score"] = 0.5 * df["PreferredBiodegradable"] + 0.5 * df["PreferredRecyclable"]

    df = pd.get_dummies(df, columns=["ProductCategory"], drop_first=True)

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if "ProductID" in numeric_cols:
        numeric_cols.remove("ProductID")
    if numeric_cols:
        df[numeric_cols] = MinMaxScaler().fit_transform(df[numeric_cols])

    return df


def engineer_pair_features(materials: pd.DataFrame, products: pd.DataFrame, recs: pd.DataFrame) -> pd.DataFrame:
    """
    Build supervised dataset for ML:
    merges (recommendations + materials + products) then creates target columns:
      - estimated_cost_per_unit_usd
      - estimated_co2_per_unit_kg
    """
    df = recs.merge(materials, on="MaterialID", how="left").merge(products, on="ProductID", how="left")

    # gaps
    df["strength_gap"] = df["StrengthRating"] - df["RequiredStrength_Level"]
    df["moisture_gap"] = df["MoistureBarrier"] - df["MoistureRequired"]
    df["oxygen_gap"] = df["OxygenBarrier"] - df["OxygenSensitivity"]

    # targets
    df["estimated_cost_per_unit_usd"] = df["CostPerKG_USD"] * df["Weight_KG"].clip(lower=0.05)
    df["budget_gap"] = df["MaxBudgetPerUnit_USD"] - df["estimated_cost_per_unit_usd"]

    df["estimated_co2_per_unit_kg"] = (df["CO2_Emissions_KG_Per_Ton"] / 1000.0) * df["Weight_KG"].clip(lower=0.05)

    # flags
    df["is_strength_insufficient"] = (df["strength_gap"] < 0).astype(int)
    df["is_moisture_insufficient"] = (df["moisture_gap"] < 0).astype(int)
    df["is_oxygen_insufficient"] = (df["oxygen_gap"] < 0).astype(int)
    df["is_over_budget"] = (df["budget_gap"] < 0).astype(int)

    df["preference_alignment"] = 0.5 * df["PreferredBiodegradable"] + 0.5 * df["PreferredRecyclable"]

    return df


def persist_csv(name: str, df: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.csv"
    df.to_csv(path, index=False)
    logging.info(f"Exported CSV: {path} ({len(df)} rows)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-data-dir", type=Path, default=Path("DB"))
    parser.add_argument("--export-dir", type=Path, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    configure_logging(args.verbose)

    tables, _ = load_source_tables(args.csv_data_dir)

    # Plots from RAW data
    plots_dir = args.csv_data_dir / "plots"
    plot_numeric_distributions(tables, plots_dir)

    logging.info("Engineering Material Features...")
    materials_feat = engineer_material_features(tables["materials"])
    log_score_distribution(materials_feat, "eco_fit_score")

    logging.info("Engineering Product Features...")
    products_feat = engineer_product_features(tables["products"])

    logging.info("Engineering Product-Material Pairs...")
    pairs_feat = engineer_pair_features(tables["materials"], tables["products"], tables["recommendations"])
    log_score_distribution(pairs_feat, "budget_gap")

    export_dir = args.export_dir or args.csv_data_dir

    # CSV outputs (no DB)
    persist_csv("materials_features", materials_feat, export_dir)
    persist_csv("products_features", products_feat, export_dir)
    persist_csv("product_material_features", pairs_feat, export_dir)

    logging.info("Done (CSV-only pipeline).")


if __name__ == "__main__":
    main()

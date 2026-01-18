import os
from pathlib import Path
import pandas as pd


# EDA / Cleaning helpers
def check_duplicates(df: pd.DataFrame, name: str) -> pd.DataFrame:
    dup_count = df.duplicated().sum()
    print(f"[{name}] Duplicate rows: {dup_count}")
    if dup_count > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        print(f"[{name}] Duplicates dropped. New row count: {len(df)}")
    return df


def check_outliers_iqr(df: pd.DataFrame, name: str, numeric_cols: list[str]) -> None:
    print(f"\n[{name}] Outlier check using IQR")
    for col in numeric_cols:
        # Skip if column is fully empty or non-numeric after coercion
        s = pd.to_numeric(df[col], errors="coerce")
        if s.dropna().empty:
            print(f"  {col}: skipped (no numeric data)")
            continue
        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = ((s < lower) | (s > upper)).sum()
        print(f"  {col}: {int(outliers)} potential outliers")


def print_corr_and_cov(df: pd.DataFrame, name: str, numeric_cols: list[str]) -> None:
    if not numeric_cols:
        print(f"\n[{name}] No numeric columns for corr/cov.")
        return
    safe = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    print(f"\n[{name}] Correlation matrix")
    print(safe.corr(numeric_only=True))

    print(f"\n[{name}] Covariance matrix")
    print(safe.cov(numeric_only=True))


def basic_missing_value_cleanup(df: pd.DataFrame, name: str) -> pd.DataFrame:
    before = len(df)
    df = df.dropna(how="all").copy()
    after = len(df)
    if after != before:
        print(f"[{name}] Dropped {before - after} fully-empty rows.")

    # Strip whitespace in string columns
    obj_cols = df.select_dtypes(include=["object"]).columns.tolist()
    for c in obj_cols:
        df[c] = df[c].astype(str).str.strip()

    return df


def save_clean_csv(df: pd.DataFrame, path: Path, backup: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if backup and path.exists():
        backup_path = path.with_suffix(path.suffix + ".bak")
        # Avoid overwriting an existing backup
        if not backup_path.exists():
            path.replace(backup_path)
            print(f"[SAVE] Backup created: {backup_path.name}")
        else:
            print(f"[SAVE] Backup already exists: {backup_path.name} (not overwriting)")

    df.to_csv(path, index=False)
    print(f"[SAVE] Clean CSV written: {path}")


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    # Default folder where your CSVs live (same as your earlier code)
    csv_dir = Path(os.getenv("ECOPACKAI_CSV_DIR", "DB")).resolve()

    materials_path = csv_dir / "ecopackai_materials.csv"
    products_path = csv_dir / "ecopackai_products.csv"
    recs_path = csv_dir / "ecopackai_recommendations.csv"

    # Load
    materials_df = pd.read_csv(materials_path)
    products_df = pd.read_csv(products_path)
    recs_df = pd.read_csv(recs_path)

    print("Initial row counts")
    print("Materials:", len(materials_df))
    print("Products:", len(products_df))
    print("Recommendations:", len(recs_df))

    # Basic missing-value cleanup (safe)
    materials_df = basic_missing_value_cleanup(materials_df, "materials")
    products_df = basic_missing_value_cleanup(products_df, "products")
    recs_df = basic_missing_value_cleanup(recs_df, "recommendations")

    # Duplicate checks
    materials_df = check_duplicates(materials_df, "materials")
    products_df = check_duplicates(products_df, "products")
    recs_df = check_duplicates(recs_df, "recommendations")

    # Outlier checks
    materials_num = materials_df.select_dtypes(include="number").columns.tolist()
    products_num = products_df.select_dtypes(include="number").columns.tolist()
    recs_num = recs_df.select_dtypes(include="number").columns.tolist()

    check_outliers_iqr(materials_df, "materials", materials_num)
    check_outliers_iqr(products_df, "products", products_num)
    check_outliers_iqr(recs_df, "recommendations", recs_num)

    # Correlation & Covariance
    print_corr_and_cov(materials_df, "materials", materials_num)
    print_corr_and_cov(products_df, "products", products_num)
    print_corr_and_cov(recs_df, "recommendations", recs_num)

    # Save cleaned data back to the SAME CSVs (no PostgreSQL)
    save_clean_csv(materials_df, materials_path, backup=True)
    save_clean_csv(products_df, products_path, backup=True)
    save_clean_csv(recs_df, recs_path, backup=True)

    print("\n Cleaning complete. Data stored in CSV files ")


if __name__ == "__main__":
    main()

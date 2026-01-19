import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "ecopackai_cosmetics_module2_clean_fe.csv")

df = pd.read_csv(DATA_PATH)

def get_top_recommendations(
    product_weight,
    fragility_level,
    is_liquid,
    premium_level,
    eco_priority,
    top_k=3
):
    filtered_df = df.copy()

    # Weight filter
    filtered_df = filtered_df[
        filtered_df["weight_capacity_kg"] >= product_weight
    ]

    # Fragility filter
    if fragility_level == "High":
        filtered_df = filtered_df[filtered_df["strength"] >= 7]
    elif fragility_level == "Medium":
        filtered_df = filtered_df[filtered_df["strength"] >= 5]

    # Liquid filter
    if is_liquid:
        filtered_df = filtered_df[
            filtered_df["material_type"].isin(["Plastic", "Glass", "Bioplastic", "Aluminum"])
        ]

    if filtered_df.empty:
        filtered_df = df.copy()

    eco_weight = {"Low": 0.3, "Medium": 0.6, "High": 0.9}[eco_priority]
    premium_weight = {"Budget": 0.3, "Standard": 0.6, "Premium": 0.9}[premium_level]

    filtered_df["final_score"] = (
        eco_weight * filtered_df["biodegradability_score_norm"]
        + (1 - eco_weight) * (1 - filtered_df["co2_emission_score_norm"])
        + premium_weight * filtered_df["cost_efficiency_index"]
    )

    filtered_df = filtered_df.sort_values("final_score", ascending=False)

    best = filtered_df.iloc[0]
    top3 = filtered_df.head(top_k)

    return {
        "best_material": {
            "material_name": best["material_name"],
            "biodegradability_score": float(best["biodegradability_score"]),
            "co2_emission_score": float(best["co2_emission_score"]),
            "cost_efficiency_index": float(best["cost_efficiency_index"])
        },
        "top_3_materials": [
            {
                "material_name": row["material_name"],
                "biodegradability_score": float(row["biodegradability_score"]),
                "co2_emission_score": float(row["co2_emission_score"]),
                "cost_efficiency_index": float(row["cost_efficiency_index"])
            }
            for _, row in top3.iterrows()
        ]
    }

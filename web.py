import streamlit as st
import requests
import joblib
import pandas as pd
import altair as alt
import psycopg2
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.lib.styles import getSampleStyleSheet

features = joblib.load("features.pkl")

material_categories = sorted(
    f.replace("material_category_", "")
    for f in features
    if f.startswith("material_category_")
)


st.set_page_config(
    page_title="EcoPack AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

DB_CONFIG = {
    "host": "localhost",
    "database": "ml_db",
    "user": "postgres",
    "password": "postgres",
    "port": 5432
}


@st.cache_data(ttl=30)
def load_db_predictions():
    conn = psycopg2.connect(**DB_CONFIG)
    query = """
        SELECT
            id,
            material_category,
            strength_mpa,
            weight_capacity_kg,
            cost_efficiency_index,
            material_suitability_score,
            co2_emission_score,
            recyclability_percent,
            biodegradability_score,
            predicted_cost_usd,
            predicted_co2_impact,
            created_at
        FROM ml_predictions
        ORDER BY created_at DESC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def generate_recommendation(cost, co2, safety):
    remarks = []

    if cost <= 60:
        remarks.append("✅ Cost is low and economically efficient.")
    elif cost <= 90:
        remarks.append("⚠️ Cost is moderate. Further optimization possible.")
    else:
        remarks.append("❌ Cost is high. Consider reducing material strength or weight.")

    if co2 <= 32:
        remarks.append("✅ CO₂ impact is environmentally friendly.")
    elif co2 <= 35:
        remarks.append("⚠️ CO₂ impact is moderate.")
    else:
        remarks.append("❌ CO₂ impact is high. Improve recyclability or emissions.")

    if safety == "Safe":
        remarks.append("🟢 Material safety classification is SAFE.")
    else:
        remarks.append("🟡 Material safety is MODERATE.")

    if cost <= 90 and co2 <= 35 and safety == "Safe":
        verdict = "✅ RECOMMENDED MATERIAL CONFIGURATION"
    else:
        verdict = "⚠️ NOT OPTIMAL — IMPROVEMENTS SUGGESTED"

    return verdict, remarks

def login_page():
    st.markdown("## 🔐 System Access")
    st.markdown("Restricted access for authorized evaluators only.")

    with st.form("login_form"):
        username = st.text_input("Username (admin)")
        password = st.text_input("Password (admin123)", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.success("Access granted")
                st.rerun()
            else:
                st.error("Invalid credentials")

def main_dashboard():
    with st.sidebar:
        st.markdown("### 👤 Session")
        st.write("Role: **Admin**")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("Manufacturing Cost & CO₂ Prediction System")

    tab1, tab2 = st.tabs(["🔮 Prediction", "📊 Database Dashboard"])

    with tab1:
        API_URL = "http://127.0.0.1:5000/predict"

        st.subheader("📥 Input Material Parameters")

        col1, col2 = st.columns(2)

        with col1:
            material_category = st.selectbox("Material Category", material_categories)
            strength_mpa = st.number_input("Mechanical Strength (MPa)", min_value=0.0)
            weight_capacity_kg = st.number_input("Weight Capacity (kg)", min_value=0.0)

        with col2:
            cost_efficiency_index = st.number_input(
                "Cost Efficiency Index", min_value=0.0, max_value=1.0
            )
            material_suitability_score = st.number_input(
                "Material Suitability Score", min_value=0.0
            )
            co2_emission_score = st.number_input("CO₂ Emission Score", min_value=0.0)
            recyclability_percent = st.slider("Recyclability (%)", 0, 100)
            biodegradability_score = st.number_input(
                "Biodegradability Score", min_value=0.0
            )

        st.divider()

        if st.button("🔍 Run Prediction", use_container_width=True):
            payload = {
                "material_category": material_category,
                "strength_mpa": strength_mpa,
                "weight_capacity_kg": weight_capacity_kg,
                "cost_efficiency_index": cost_efficiency_index,
                "material_suitability_score": material_suitability_score,
                "co2_emission_score": co2_emission_score,
                "recyclability_percent": recyclability_percent,
                "biodegradability_score": biodegradability_score
            }

            try:
                with st.spinner("Running ML inference..."):
                    response = requests.post(API_URL, json=payload, timeout=5)

                if response.status_code != 200:
                    st.error("Prediction failed")
                    return

                result = response.json()
                st.success("Prediction Successful")

                m1, m2, m3 = st.columns(3)
                m1.metric("Estimated Cost (USD)", f"${result['predicted_cost_usd']}")
                m2.metric("Estimated CO₂ Impact", result["predicted_co2_impact"])
                m3.metric("Material Safety", result["predicted_material_safety"])

                graph_df = pd.DataFrame({
                    "Metric": ["Estimated Cost", "Estimated CO₂"],
                    "Value": [
                        result["predicted_cost_usd"],
                        result["predicted_co2_impact"]
                    ]
                })

                bar_chart = alt.Chart(graph_df).mark_bar().encode(
                    x="Metric",
                    y="Value"
                )

                st.altair_chart(bar_chart, use_container_width=True)

                verdict, remarks = generate_recommendation(
                    result["predicted_cost_usd"],
                    result["predicted_co2_impact"],
                    result["predicted_material_safety"]
                )

                st.subheader("System Recommendation")
                st.markdown(f"### {verdict}")
                for r in remarks:
                    st.write(r)

            except requests.exceptions.RequestException:
                st.error("Flask backend is not reachable")


    with tab2:
        st.subheader("📊 Stored Predictions (PostgreSQL)")

        df = load_db_predictions()

        if df.empty:
            st.info("No predictions stored yet.")
            return

        BASELINE_CO2 = 40
        BASELINE_COST = 120

        df["co2_reduction_percent"] = (
            (BASELINE_CO2 - df["predicted_co2_impact"]) / BASELINE_CO2
        ) * 100

        df["cost_savings"] = BASELINE_COST - df["predicted_cost_usd"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Records", len(df))
        c2.metric("Avg Cost (USD)", round(df["predicted_cost_usd"].mean(), 2))
        c3.metric("Avg CO₂ Impact", round(df["predicted_co2_impact"].mean(), 2))

        c4, c5 = st.columns(2)
        c4.metric("Avg CO₂ Reduction %", f"{round(df['co2_reduction_percent'].mean(), 2)} %")
        c5.metric("Avg Cost Savings (USD)", f"${round(df['cost_savings'].mean(), 2)}")

        st.divider()

        material_filter = st.multiselect(
            "Filter by Material Category",
            options=sorted(df["material_category"].unique())
        )

        if material_filter:
            df = df[df["material_category"].isin(material_filter)]

        st.subheader("📄 Database Table View")
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("📈 Material Usage Trend")
        material_counts = df["material_category"].value_counts()

        fig1, ax1 = plt.subplots(figsize=(4.2, 2.4))

        material_counts.plot(kind="bar", ax=ax1)

        ax1.set_title("Material Usage", fontsize=8, pad=4)
        ax1.set_ylabel("Count", fontsize=7)
        ax1.set_xlabel("")

        ax1.tick_params(axis="y", labelsize=6)

        ax1.tick_params(
            axis="x",
            labelsize=4,
            rotation=45
        )

        plt.subplots_adjust(bottom=0.35)
        st.pyplot(fig1, use_container_width=True)

        st.subheader("📉 Sustainability Trend Over Time")
        trend_df = df.sort_values("created_at")

        fig2, ax2 = plt.subplots(figsize=(3.5, 1.6))

        ax2.plot(
            trend_df["created_at"],
            trend_df["predicted_co2_impact"],
            label="CO₂",
            linewidth=1
        )
        ax2.plot(
            trend_df["created_at"],
            trend_df["predicted_cost_usd"],
            label="Cost",
            linewidth=1
        )

        ax2.set_xlabel("", fontsize=6)
        ax2.set_ylabel("Value", fontsize=6)

        ax2.legend(fontsize=5, loc="upper right", frameon=False)

        ax2.tick_params(axis="x", labelsize=5)
        ax2.tick_params(axis="y", labelsize=5)

        ax2.set_title("CO₂ & Cost Trend", fontsize=7, pad=2)

        plt.tight_layout(pad=0.2)
        st.pyplot(fig2, use_container_width=True)

        st.subheader("📤 Export Sustainability Report")

        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        st.download_button(
            "⬇ Download Excel Report",
            excel_buffer,
            "sustainability_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        def generate_pdf(dataframe):
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer)
            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph("Sustainability Analysis Report", styles["Title"]))
            table_data = [dataframe.columns.tolist()] + dataframe.head(15).values.tolist()
            elements.append(Table(table_data))
            doc.build(elements)
            buffer.seek(0)
            return buffer

        pdf_buffer = generate_pdf(df)

        st.download_button(
            "⬇ Download PDF Report",
            pdf_buffer,
            "sustainability_report.pdf",
            mime="application/pdf"
        )


if st.session_state.logged_in:
    main_dashboard()
else:
    login_page()

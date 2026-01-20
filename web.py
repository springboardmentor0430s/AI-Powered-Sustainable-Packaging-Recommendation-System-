import streamlit as st
import requests
import joblib
import pandas as pd
import altair as alt
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.lib.styles import getSampleStyleSheet

# Set matplotlib style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

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

# Custom CSS for modern UI
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .stApp {
        background: transparent;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #1e3a8a;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.95rem;
        font-weight: 600;
        color: #475569;
    }
    
    .prediction-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 1.5rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .success-badge {
        background: linear-gradient(135deg, #34d399 0%, #059669 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        display: inline-block;
        margin: 1rem 0;
    }
    
    .warning-badge {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        display: inline-block;
        margin: 1rem 0;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: white;
        font-weight: 600;
        padding: 12px 24px;
    }
    
    .stTabs [aria-selected="true"] {
        background: white;
        color: #667eea;
    }
    
    h1, h2, h3 {
        color: white;
        font-weight: 700;
    }
    
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.75rem 2rem;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    .dataframe-container {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

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
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; margin-top: 5rem;'>🔐 EcoPack AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.9); margin-bottom: 3rem;'>Sustainable Manufacturing Intelligence</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password", placeholder="admin123")
            submit = st.form_submit_button("Login", use_container_width=True)

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
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    st.title("🌿 Manufacturing Cost & CO₂ Prediction System")
    st.markdown("<p style='color: rgba(255,255,255,0.9); font-size: 1.1rem;'>AI-Powered Sustainability Intelligence</p>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔮 Prediction", "📊 Analytics Dashboard"])

    with tab1:
        API_URL = "http://127.0.0.1:5000/predict"

        st.markdown("<div class='prediction-card'>", unsafe_allow_html=True)
        st.subheader("📥 Input Material Parameters")

        col1, col2 = st.columns(2)

        with col1:
            material_category = st.selectbox("Material Category", material_categories)
            strength_mpa = st.number_input("Mechanical Strength (MPa)", min_value=0.0)
            weight_capacity_kg = st.number_input("Weight Capacity (kg)", min_value=0.0)
            cost_efficiency_index = st.number_input(
                "Cost Efficiency Index", min_value=0.0, max_value=1.0
            )

        with col2:
            material_suitability_score = st.number_input(
                "Material Suitability Score", min_value=0.0
            )
            co2_emission_score = st.number_input("CO₂ Emission Score", min_value=0.0)
            recyclability_percent = st.slider("Recyclability (%)", 0, 100)
            biodegradability_score = st.number_input(
                "Biodegradability Score", min_value=0.0
            )

        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("🚀 Run Prediction", use_container_width=True):
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
                st.success("✅ Prediction Successful")

                m1, m2, m3 = st.columns(3)
                m1.metric("Estimated Cost", f"${result['predicted_cost_usd']:.2f}", 
                         delta=f"-${120 - result['predicted_cost_usd']:.2f} vs baseline")
                m2.metric("CO₂ Impact", f"{result['predicted_co2_impact']:.2f}", 
                         delta=f"-{40 - result['predicted_co2_impact']:.2f} vs baseline")
                m3.metric("Safety Rating", result["predicted_material_safety"])

                # Enhanced visualization with Altair
                graph_df = pd.DataFrame({
                    "Metric": ["Cost (USD)", "CO₂ Impact"],
                    "Value": [result["predicted_cost_usd"], result["predicted_co2_impact"]],
                    "Color": ["#667eea", "#34d399"]
                })

                bar_chart = alt.Chart(graph_df).mark_bar(
                    cornerRadiusTopLeft=8,
                    cornerRadiusTopRight=8
                ).encode(
                    x=alt.X("Metric:N", axis=alt.Axis(labelAngle=0, labelFontSize=12)),
                    y=alt.Y("Value:Q", axis=alt.Axis(labelFontSize=12)),
                    color=alt.Color("Metric:N", scale=alt.Scale(
                        domain=["Cost (USD)", "CO₂ Impact"],
                        range=["#667eea", "#34d399"]
                    ), legend=None),
                    tooltip=[
                        alt.Tooltip("Metric:N", title="Metric"),
                        alt.Tooltip("Value:Q", title="Value", format=".2f")
                    ]
                ).properties(
                    height=400,
                    title="Prediction Results"
                ).configure_view(
                    strokeWidth=0
                ).configure_axis(
                    grid=True,
                    gridColor='#f0f0f0'
                )

                st.altair_chart(bar_chart, use_container_width=True)

                verdict, remarks = generate_recommendation(
                    result["predicted_cost_usd"],
                    result["predicted_co2_impact"],
                    result["predicted_material_safety"]
                )

                st.markdown("<div class='prediction-card'>", unsafe_allow_html=True)
                st.subheader("💡 System Recommendation")
                
                if "RECOMMENDED" in verdict:
                    st.markdown(f"<div class='success-badge'>{verdict}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='warning-badge'>{verdict}</div>", unsafe_allow_html=True)
                
                for r in remarks:
                    st.markdown(f"**{r}**")
                st.markdown("</div>", unsafe_allow_html=True)

            except requests.exceptions.RequestException:
                st.error("🔌 Flask backend is not reachable")

    with tab2:
        st.subheader("📊 Analytics & Insights")

        df = load_db_predictions()

        if df.empty:
            st.info("📭 No predictions stored yet.")
            return

        BASELINE_CO2 = 40
        BASELINE_COST = 120

        df["co2_reduction_percent"] = (
            (BASELINE_CO2 - df["predicted_co2_impact"]) / BASELINE_CO2
        ) * 100

        df["cost_savings"] = BASELINE_COST - df["predicted_cost_usd"]

        # Enhanced metrics display
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Total Records", len(df))
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Avg Cost", f"${df['predicted_cost_usd'].mean():.2f}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Avg CO₂", f"{df['predicted_co2_impact'].mean():.2f}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col4:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("CO₂ Reduction", f"{df['co2_reduction_percent'].mean():.1f}%")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col5:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Avg Savings", f"${df['cost_savings'].mean():.2f}")
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        material_filter = st.multiselect(
            "🔍 Filter by Material Category",
            options=sorted(df["material_category"].unique())
        )

        if material_filter:
            df = df[df["material_category"].isin(material_filter)]

        # Enhanced Material Usage Chart
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Material Usage Distribution")
            material_counts = df["material_category"].value_counts().reset_index()
            material_counts.columns = ['Material', 'Count']
            
            # Create pie chart with matplotlib
            fig_pie, ax_pie = plt.subplots(figsize=(8, 8))
            colors = sns.color_palette("husl", len(material_counts))
            
            wedges, texts, autotexts = ax_pie.pie(
                material_counts['Count'],
                labels=material_counts['Material'],
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                textprops={'fontsize': 10, 'weight': 'bold'}
            )
            
            # Make percentage text white
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(11)
            
            ax_pie.set_title('Material Distribution', fontsize=14, weight='bold', pad=20)
            plt.tight_layout()
            st.pyplot(fig_pie, use_container_width=True)
        
        with col2:
            st.subheader("📊 Material Comparison")
            
            # Enhanced bar chart with Altair
            bar_chart = alt.Chart(material_counts).mark_bar(
                cornerRadiusTopLeft=8,
                cornerRadiusTopRight=8
            ).encode(
                x=alt.X('Material:N', axis=alt.Axis(labelAngle=-45, labelFontSize=11)),
                y=alt.Y('Count:Q', axis=alt.Axis(labelFontSize=11)),
                color=alt.Color('Material:N', scale=alt.Scale(scheme='category20'), legend=None),
                tooltip=[
                    alt.Tooltip('Material:N', title='Material'),
                    alt.Tooltip('Count:Q', title='Count')
                ]
            ).properties(
                height=400
            ).configure_view(
                strokeWidth=0
            ).configure_axis(
                grid=True,
                gridColor='#f0f0f0'
            )
            
            st.altair_chart(bar_chart, use_container_width=True)

        # Enhanced Trend Analysis
        st.subheader("📉 Sustainability Trends Over Time")
        trend_df = df.sort_values("created_at").reset_index(drop=True)

        # Create multi-line chart with matplotlib
        fig_trend, ax_trend = plt.subplots(figsize=(12, 5))
        
        # Plot CO2 line
        ax_trend.plot(
            trend_df.index,
            trend_df["predicted_co2_impact"],
            label="CO₂ Impact",
            color='#34d399',
            linewidth=3,
            marker='o',
            markersize=6,
            markerfacecolor='#34d399',
            markeredgecolor='white',
            markeredgewidth=2
        )
        
        # Plot Cost line
        ax_trend.plot(
            trend_df.index,
            trend_df["predicted_cost_usd"],
            label="Cost (USD)",
            color='#667eea',
            linewidth=3,
            marker='s',
            markersize=6,
            markerfacecolor='#667eea',
            markeredgecolor='white',
            markeredgewidth=2
        )
        
        ax_trend.set_xlabel('Prediction Index', fontsize=12, weight='bold')
        ax_trend.set_ylabel('Value', fontsize=12, weight='bold')
        ax_trend.set_title('CO₂ & Cost Trends', fontsize=14, weight='bold', pad=15)
        ax_trend.legend(fontsize=11, loc='upper right', frameon=True, shadow=True)
        ax_trend.grid(True, alpha=0.3, linestyle='--')
        ax_trend.set_facecolor('#f8f9fa')
        
        plt.tight_layout()
        st.pyplot(fig_trend, use_container_width=True)

        # Data Table
        st.subheader("📄 Database Table View")
        st.markdown("<div class='dataframe-container'>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Export Section
        st.subheader("📤 Export Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)

            st.download_button(
                "⬇️ Download Excel Report",
                excel_buffer,
                "sustainability_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col2:
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
                "⬇️ Download PDF Report",
                pdf_buffer,
                "sustainability_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

if st.session_state.logged_in:
    main_dashboard()
else:
    login_page()
    main_dashboard()
else:
    login_page()

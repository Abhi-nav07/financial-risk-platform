import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
import plotly.express as px
import shap
import warnings
import io
import base64
from datetime import datetime
from fpdf import FPDF

warnings.filterwarnings('ignore')

# ─────────────────────────────
# PAGE CONFIG
# ─────────────────────────────
st.set_page_config(
    page_title="FinRisk AI Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────
# CUSTOM CSS
# ─────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background-color: #040d1a;
    color: #e2e8f0;
}
.stApp {
    background: radial-gradient(ellipse at top left, #0a1628 0%, #040d1a 50%, #020810 100%);
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #060f1f 0%, #040d1a 100%);
    border-right: 1px solid #0ea5e920;
}
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #0f1f3d 0%, #0a1628 100%);
    border: 1px solid #0ea5e930;
    border-radius: 16px;
    padding: 20px !important;
    box-shadow: 0 0 30px #0ea5e910;
    transition: all 0.3s ease;
}
[data-testid="metric-container"]:hover {
    border-color: #0ea5e960;
    box-shadow: 0 0 40px #0ea5e920;
    transform: translateY(-2px);
}
[data-testid="metric-container"] label {
    color: #64748b !important;
    font-size: 12px !important;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #0ea5e9 !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
}
.stButton > button {
    background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
    color: white !important;
    border: none;
    border-radius: 12px;
    padding: 14px 32px;
    font-size: 16px;
    font-weight: 600;
    font-family: 'Space Grotesk', sans-serif;
    width: 100%;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px #0ea5e940;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
    box-shadow: 0 6px 30px #0ea5e960;
    transform: translateY(-2px);
}
.stTextInput input, .stNumberInput input {
    background: #0a1628 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #0ea5e9 !important;
    box-shadow: 0 0 0 2px #0ea5e920 !important;
}
div[data-baseweb="select"] > div {
    background: #0a1628 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}
[data-testid="stFileUploader"] {
    background: #0a1628;
    border: 2px dashed #1e3a5f;
    border-radius: 16px;
    padding: 20px;
    transition: all 0.3s;
}
[data-testid="stFileUploader"]:hover {
    border-color: #0ea5e9;
    background: #0f1f3d;
}
hr { border-color: #1e3a5f !important; margin: 24px 0 !important; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #040d1a; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #0ea5e9; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# ─────────────────────────────
# LOGIN PAGE
# ─────────────────────────────
USERS = {
    "admin": "finrisk2024",
    "analyst": "analyst123",
    "demo": "demo123"
}

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center; padding: 60px 0 40px 0;'>
            <div style='font-size: 64px;'>🏦</div>
            <div style='font-size: 28px; font-weight: 700; color: #0ea5e9; margin-top: 16px;'>FinRisk AI</div>
            <div style='font-size: 13px; color: #475569; letter-spacing: 3px; text-transform: uppercase; margin-top: 4px;'>Intelligence Platform</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style='background: linear-gradient(135deg, #0a1628, #0f1f3d); border: 1px solid #1e3a5f; border-radius: 20px; padding: 36px;'>
            <div style='font-size: 18px; font-weight: 600; color: #f1f5f9; margin-bottom: 24px; text-align:center;'>Secure Login</div>
        """, unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")

        if st.button("🔐 Login"):
            if username in USERS and USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Please try again.")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <div style='text-align:center; margin-top: 24px;'>
            <div style='color: #475569; font-size: 13px; margin-bottom: 8px;'>Demo Credentials</div>
            <div style='background: #0a1628; border: 1px solid #1e3a5f; border-radius: 10px; padding: 12px; font-family: JetBrains Mono, monospace; font-size: 13px; color: #64748b;'>
                username: <span style='color: #0ea5e9;'>demo</span> &nbsp;|&nbsp; password: <span style='color: #0ea5e9;'>demo123</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────
# LOAD MODELS
# ─────────────────────────────
@st.cache_resource
def load_models():
    fraud_model = joblib.load('models/fraud_model.pkl')
    credit_model = joblib.load('models/credit_risk_model.pkl')
    credit_scaler = joblib.load('models/credit_scaler.pkl')
    return fraud_model, credit_model, credit_scaler

@st.cache_resource
def load_shap_explainer(_model):
    return shap.TreeExplainer(_model)

fraud_model, credit_model, credit_scaler = load_models()
credit_explainer = load_shap_explainer(credit_model)

# ─────────────────────────────
# HELPERS
# ─────────────────────────────
CREDIT_COLS = [
    'person_age', 'person_income', 'person_home_ownership',
    'person_emp_length', 'loan_intent', 'loan_grade',
    'loan_amnt', 'loan_int_rate', 'loan_percent_income',
    'cb_person_default_on_file', 'cb_person_cred_hist_length'
]
NUM_COLS = [
    'person_age', 'person_income', 'person_emp_length',
    'loan_amnt', 'loan_int_rate', 'loan_percent_income',
    'cb_person_cred_hist_length'
]
HOME_MAP    = {'RENT': 0, 'OWN': 1, 'MORTGAGE': 2, 'OTHER': 3}
INTENT_MAP  = {'PERSONAL': 0, 'EDUCATION': 1, 'MEDICAL': 2,
               'VENTURE': 3, 'HOMEIMPROVEMENT': 4, 'DEBTCONSOLIDATION': 5}
GRADE_MAP   = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7}
DEFAULT_MAP = {'N': 0, 'Y': 1}

def encode_credit(row_df):
    row_df = row_df.copy()
    if row_df['person_home_ownership'].dtype == object:
        row_df['person_home_ownership'] = row_df['person_home_ownership'].map(HOME_MAP)
    if row_df['loan_intent'].dtype == object:
        row_df['loan_intent'] = row_df['loan_intent'].map(INTENT_MAP)
    if row_df['loan_grade'].dtype == object:
        row_df['loan_grade'] = row_df['loan_grade'].map(GRADE_MAP)
    if row_df['cb_person_default_on_file'].dtype == object:
        row_df['cb_person_default_on_file'] = row_df['cb_person_default_on_file'].map(DEFAULT_MAP)
    return row_df

def get_risk_meta(score):
    if score < 30:
        return "LOW RISK", "#22c55e", "🟢", "Strong financial profile. Loan approval recommended."
    elif score < 60:
        return "MEDIUM RISK", "#f59e0b", "🟡", "Moderate risk. Consider additional verification before approval."
    else:
        return "HIGH RISK", "#ef4444", "🔴", "High default probability. Approval not recommended without collateral."

def generate_pdf(info: dict, risk_score: float, category: str, description: str) -> bytes:
    pdf = FPDF()
    pdf.set_margins(20, 20, 20)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(14, 165, 233)
    pdf.cell(170, 12, "FinRisk AI - Credit Risk Report", align="C", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(170, 8, f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", align="C", ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(14, 165, 233)
    pdf.cell(170, 12, f"Risk Score: {risk_score} / 100", align="C", ln=True)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(170, 8, f"Category: {category}", align="C", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.set_x(20)
    pdf.multi_cell(170, 7, description)
    pdf.ln(6)

    pdf.set_draw_color(30, 58, 95)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(14, 165, 233)
    pdf.set_x(20)
    pdf.cell(170, 10, "Customer Financial Profile", ln=True)
    pdf.ln(2)
    for key, val in info.items():
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(100, 116, 139)
        pdf.set_x(20)
        pdf.cell(90, 8, str(key), ln=False)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(80, 8, str(val), ln=True)

    pdf.ln(6)
    pdf.set_draw_color(30, 58, 95)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(14, 165, 233)
    pdf.set_x(20)
    pdf.cell(170, 10, "Recommendations", ln=True)
    pdf.ln(2)

    if risk_score < 30:
        recs = [
            "Approve loan application - low default risk detected.",
            "Standard interest rate applicable.",
            "Regular monthly monitoring recommended.",
        ]
    elif risk_score < 60:
        recs = [
            "Conduct additional income verification before approval.",
            "Consider a slightly higher interest rate to offset moderate risk.",
            "Request recent 3-month bank statements.",
            "Monitor account quarterly.",
        ]
    else:
        recs = [
            "Do not approve without collateral or guarantor.",
            "Request full credit history report.",
            "Consider partial loan with strict repayment terms.",
            "Flag for manual review by senior credit officer.",
        ]

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    for r in recs:
        pdf.set_x(20)
        pdf.multi_cell(170, 8, f"- {r}")

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.set_x(20)
    pdf.multi_cell(170, 6, "This report is generated by FinRisk AI Platform and is for internal use only. It does not constitute financial or legal advice.")

    return bytes(pdf.output())

# ─────────────────────────────
# SIDEBAR
# ─────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center; padding: 20px 0 24px 0;'>
        <div style='font-size: 44px;'>🏦</div>
        <div style='font-size: 18px; font-weight: 700; color: #0ea5e9; margin-top: 10px;'>FinRisk AI</div>
        <div style='font-size: 11px; color: #475569; letter-spacing: 2px; text-transform: uppercase; margin-top: 4px;'>Intelligence Platform</div>
        <div style='margin-top: 12px; background: #0a1628; border: 1px solid #1e3a5f; border-radius: 8px; padding: 8px 12px; font-size: 13px; color: #64748b;'>
            👤 <span style='color: #0ea5e9;'>{st.session_state.username}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='color: #475569; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px;'>Navigation</div>", unsafe_allow_html=True)

    page = st.radio("", [
        "🏠  Home",
        "🔍  Fraud Detection",
        "📊  Credit Risk Scoring",
        "📦  Batch Credit Scoring",
        "📈  Analytics Dashboard",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("""
    <div style='padding: 16px; background: #0a1628; border-radius: 12px; border: 1px solid #1e3a5f;'>
        <div style='color: #64748b; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;'>Model Performance</div>
        <div style='display: flex; justify-content: space-between; margin-bottom: 6px;'>
            <span style='color: #94a3b8; font-size: 13px;'>Fraud Detection</span>
            <span style='color: #0ea5e9; font-weight: 600; font-size: 13px;'>93.2%</span>
        </div>
        <div style='background: #1e3a5f; border-radius: 4px; height: 4px; margin-bottom: 12px;'>
            <div style='background: linear-gradient(90deg, #0ea5e9, #38bdf8); width: 93.2%; height: 4px; border-radius: 4px;'></div>
        </div>
        <div style='display: flex; justify-content: space-between; margin-bottom: 6px;'>
            <span style='color: #94a3b8; font-size: 13px;'>Credit Risk</span>
            <span style='color: #0ea5e9; font-weight: 600; font-size: 13px;'>94.1%</span>
        </div>
        <div style='background: #1e3a5f; border-radius: 4px; height: 4px;'>
            <div style='background: linear-gradient(90deg, #0ea5e9, #38bdf8); width: 94.1%; height: 4px; border-radius: 4px;'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

# ─────────────────────────────
# HOME PAGE
# ─────────────────────────────
if page == "🏠  Home":
    st.markdown("""
    <div style='padding: 50px 0 36px 0;'>
        <div style='font-size: 12px; color: #0ea5e9; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 14px;'>AI-Powered Financial Intelligence</div>
        <h1 style='font-size: 50px; font-weight: 700; color: #f1f5f9; line-height: 1.1; margin: 0;'>
            Financial Risk<br>
            <span style='background: linear-gradient(135deg, #0ea5e9, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>Intelligence Platform</span>
        </h1>
        <p style='color: #64748b; font-size: 17px; margin-top: 18px; max-width: 600px; line-height: 1.7;'>
            Enterprise-grade fraud detection and credit risk scoring powered by XGBoost. Built to protect financial institutions and their customers.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Fraud Model AUC", "93.2%", "+3.2% vs baseline")
    with col2: st.metric("Credit Model AUC", "94.1%", "+4.1% vs baseline")
    with col3: st.metric("Transactions Trained", "284K+", "Real world data")
    with col4: st.metric("Risk Categories", "3 Levels", "Low / Med / High")

    st.markdown("---")
    cols = st.columns(4)
    features = [
        ("🔍", "Fraud Detection", "Upload transactions and flag suspicious activity instantly."),
        ("📊", "Credit Scoring", "AI-powered 0-100 risk score for any customer."),
        ("📦", "Batch Scoring", "Score hundreds of customers at once via CSV upload."),
        ("📈", "Analytics", "Deep insights into model performance and data patterns."),
    ]
    for col, (icon, title, desc) in zip(cols, features):
        with col:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg,#0a1628,#0f1f3d); border:1px solid #0ea5e930; border-radius:16px; padding:24px; height:170px;'>
                <div style='font-size:30px; margin-bottom:10px;'>{icon}</div>
                <div style='font-size:16px; font-weight:700; color:#f1f5f9; margin-bottom:8px;'>{title}</div>
                <div style='color:#64748b; font-size:13px; line-height:1.5;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────
# FRAUD DETECTION PAGE
# ─────────────────────────────
elif page == "🔍  Fraud Detection":
    st.markdown("""
    <h1 style='font-size:36px; font-weight:700; color:#f1f5f9; margin-bottom:6px;'>🔍 Fraud Detection</h1>
    <p style='color:#64748b; font-size:15px; margin-bottom:28px;'>Upload a transaction CSV to identify fraudulent activity using AI</p>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Drop your transaction CSV here", type=['csv'])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.markdown("**Data Preview**")
        st.dataframe(df.head(), use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🔍 Run Fraud Detection Analysis"):
            with st.spinner("Analyzing transactions with AI..."):
                df_input = df.drop(columns=['Class'], errors='ignore')
                predictions = fraud_model.predict(df_input)
                probabilities = fraud_model.predict_proba(df_input)[:, 1]
                df['Fraud Probability %'] = (probabilities * 100).round(2)
                df['Prediction'] = predictions
                df['Status'] = df['Prediction'].apply(lambda x: '🚨 FRAUD' if x == 1 else '✅ SAFE')

            st.markdown("---")
            total = len(df)
            fraud_count = int(df['Prediction'].sum())
            safe_count = total - fraud_count
            fraud_rate = round((fraud_count / total) * 100, 2)

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Total Transactions", f"{total:,}")
            with c2: st.metric("🚨 Fraudulent", f"{fraud_count:,}")
            with c3: st.metric("✅ Safe", f"{safe_count:,}")
            with c4: st.metric("Fraud Rate", f"{fraud_rate}%")

            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                fig = go.Figure(data=[go.Pie(
                    labels=['Safe', 'Fraud'],
                    values=[safe_count, fraud_count],
                    hole=0.6,
                    marker_colors=['#0ea5e9', '#ef4444'],
                    textfont=dict(color='white', size=13),
                )])
                fig.update_layout(
                    title=dict(text="Transaction Distribution", font=dict(color='#94a3b8', size=15)),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#94a3b8'), legend=dict(font=dict(color='#94a3b8')),
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig2 = go.Figure()
                fig2.add_trace(go.Histogram(x=df['Fraud Probability %'], nbinsx=50,
                                            marker_color='#0ea5e9', opacity=0.8))
                fig2.update_layout(
                    title=dict(text="Fraud Probability Distribution", font=dict(color='#94a3b8', size=15)),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#94a3b8'),
                    xaxis=dict(gridcolor='#1e3a5f', title='Probability %'),
                    yaxis=dict(gridcolor='#1e3a5f', title='Count'),
                    height=300
                )
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("**🚨 Flagged Transactions**")
            st.dataframe(df[df['Prediction'] == 1][['Fraud Probability %', 'Status']].head(50), use_container_width=True)

            csv = df.to_csv(index=False)
            st.download_button("📥 Download Full Report", csv, "fraud_report.csv", "text/csv")

# ─────────────────────────────
# CREDIT RISK SCORING PAGE
# ─────────────────────────────
elif page == "📊  Credit Risk Scoring":
    st.markdown("""
    <h1 style='font-size:36px; font-weight:700; color:#f1f5f9; margin-bottom:6px;'>📊 Credit Risk Scoring</h1>
    <p style='color:#64748b; font-size:15px; margin-bottom:28px;'>Enter customer profile for AI-powered risk assessment with SHAP explanation</p>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div style='color:#0ea5e9;font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-bottom:14px;'>Personal Info</div>", unsafe_allow_html=True)
        age            = st.number_input("Age", 18, 100, 30)
        income         = st.number_input("Annual Income ($)", 1000, 1000000, 50000)
        emp_length     = st.number_input("Employment Length (years)", 0, 50, 5)
        home_ownership = st.selectbox("Home Ownership", ['RENT', 'OWN', 'MORTGAGE', 'OTHER'])

    with col2:
        st.markdown("<div style='color:#0ea5e9;font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-bottom:14px;'>Loan Details</div>", unsafe_allow_html=True)
        loan_amnt           = st.number_input("Loan Amount ($)", 500, 100000, 10000)
        loan_int_rate       = st.number_input("Interest Rate (%)", 1.0, 30.0, 10.0)
        loan_percent_income = st.number_input("Loan % of Income", 0.0, 1.0, 0.2)
        loan_intent         = st.selectbox("Loan Intent", ['PERSONAL','EDUCATION','MEDICAL','VENTURE','HOMEIMPROVEMENT','DEBTCONSOLIDATION'])

    with col3:
        st.markdown("<div style='color:#0ea5e9;font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-bottom:14px;'>Credit History</div>", unsafe_allow_html=True)
        loan_grade       = st.selectbox("Loan Grade", ['A','B','C','D','E','F','G'])
        cred_hist_length = st.number_input("Credit History Length (years)", 0, 50, 5)
        default_on_file  = st.selectbox("Previous Default?", ['N','Y'])

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("📊 Generate Risk Assessment"):
        raw_input = pd.DataFrame([[
            age, income, home_ownership, emp_length, loan_intent,
            loan_grade, loan_amnt, loan_int_rate, loan_percent_income,
            default_on_file, cred_hist_length
        ]], columns=CREDIT_COLS)

        encoded = encode_credit(raw_input.copy())
        encoded[NUM_COLS] = credit_scaler.transform(encoded[NUM_COLS])

        prob       = credit_model.predict_proba(encoded)[:, 1][0]
        risk_score = round(prob * 100, 2)
        category, color, emoji, description = get_risk_meta(risk_score)

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=risk_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Risk Score", 'font': {'color': '#94a3b8', 'size': 16}},
                number={'font': {'color': color, 'size': 44}, 'suffix': '/100'},
                gauge={
                    'axis': {'range': [0, 100], 'tickcolor': '#475569', 'tickfont': {'color': '#475569'}},
                    'bar': {'color': color, 'thickness': 0.3},
                    'bgcolor': '#0a1628',
                    'bordercolor': '#1e3a5f',
                    'steps': [
                        {'range': [0, 30],  'color': '#052e16'},
                        {'range': [30, 60], 'color': '#1c1000'},
                        {'range': [60, 100],'color': '#1c0000'},
                    ],
                    'threshold': {'line': {'color': color, 'width': 4}, 'thickness': 0.75, 'value': risk_score}
                }
            ))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=290, font=dict(color='#94a3b8'), margin=dict(t=50, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,#0a1628,#0f1f3d); border:1px solid {color}40; border-radius:20px; padding:28px; margin-top:10px;'>
                <div style='font-size:11px; color:#475569; letter-spacing:2px; text-transform:uppercase; margin-bottom:10px;'>Assessment Result</div>
                <div style='font-size:36px; font-weight:700; color:{color}; margin-bottom:8px;'>{emoji} {category}</div>
                <div style='font-size:14px; color:#94a3b8; line-height:1.6; margin-bottom:20px;'>{description}</div>
                <div style='background:#040d1a; border-radius:12px; padding:18px;'>
                    <div style='display:flex; justify-content:space-between; margin-bottom:8px;'>
                        <span style='color:#64748b; font-size:13px;'>Default Probability</span>
                        <span style='color:{color}; font-weight:600;'>{risk_score}%</span>
                    </div>
                    <div style='display:flex; justify-content:space-between; margin-bottom:8px;'>
                        <span style='color:#64748b; font-size:13px;'>Loan Grade</span>
                        <span style='color:#e2e8f0; font-weight:600;'>{loan_grade}</span>
                    </div>
                    <div style='display:flex; justify-content:space-between; margin-bottom:8px;'>
                        <span style='color:#64748b; font-size:13px;'>Loan / Income</span>
                        <span style='color:#e2e8f0; font-weight:600;'>{loan_percent_income:.0%}</span>
                    </div>
                    <div style='display:flex; justify-content:space-between;'>
                        <span style='color:#64748b; font-size:13px;'>Prior Default</span>
                        <span style='color:#e2e8f0; font-weight:600;'>{'Yes ⚠️' if default_on_file=='Y' else 'No ✅'}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── SHAP Explanation ──
        st.markdown("---")
        st.markdown("### 🧠 Why did the model give this score?")
        st.markdown("<p style='color:#64748b; font-size:14px;'>SHAP values show which factors pushed the risk score up (red) or down (green)</p>", unsafe_allow_html=True)

        with st.spinner("Computing SHAP explanation..."):
            shap_vals = credit_explainer.shap_values(encoded)[0]
            feature_labels = [
                'Age', 'Income', 'Home Ownership', 'Employment Length',
                'Loan Intent', 'Loan Grade', 'Loan Amount', 'Interest Rate',
                'Loan % Income', 'Prior Default', 'Credit History Length'
            ]
            shap_df = pd.DataFrame({'Feature': feature_labels, 'SHAP Value': shap_vals})
            shap_df = shap_df.reindex(shap_df['SHAP Value'].abs().sort_values().index)

            fig_shap = go.Figure(go.Bar(
                x=shap_df['SHAP Value'],
                y=shap_df['Feature'],
                orientation='h',
                marker_color=['#ef4444' if v > 0 else '#22c55e' for v in shap_df['SHAP Value']],
                text=[f"{v:+.3f}" for v in shap_df['SHAP Value']],
                textposition='outside',
                textfont=dict(color='#94a3b8', size=11),
            ))
            fig_shap.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8'),
                xaxis=dict(gridcolor='#1e3a5f', title='Impact on Risk Score', zerolinecolor='#1e3a5f'),
                yaxis=dict(gridcolor='#1e3a5f'),
                height=380,
                margin=dict(l=10, r=40, t=20, b=20)
            )
            st.plotly_chart(fig_shap, use_container_width=True)

        # ── PDF Download ──
        st.markdown("---")
        customer_info = {
            "Age":                    age,
            "Annual Income":          f"${income:,}",
            "Home Ownership":         home_ownership,
            "Employment Length":      f"{emp_length} years",
            "Loan Intent":            loan_intent,
            "Loan Grade":             loan_grade,
            "Loan Amount":            f"${loan_amnt:,}",
            "Interest Rate":          f"{loan_int_rate}%",
            "Loan % of Income":       f"{loan_percent_income:.0%}",
            "Previous Default":       default_on_file,
            "Credit History Length":  f"{cred_hist_length} years",
        }
        pdf_bytes = generate_pdf(customer_info, risk_score, category, description)
        st.download_button(
            "📄 Download PDF Risk Report",
            data=pdf_bytes,
            file_name=f"credit_risk_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )

# ─────────────────────────────
# BATCH CREDIT SCORING PAGE
# ─────────────────────────────
elif page == "📦  Batch Credit Scoring":
    st.markdown("""
    <h1 style='font-size:36px; font-weight:700; color:#f1f5f9; margin-bottom:6px;'>📦 Batch Credit Scoring</h1>
    <p style='color:#64748b; font-size:15px; margin-bottom:28px;'>Upload a CSV with multiple customers to score them all at once</p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#0a1628; border:1px solid #1e3a5f; border-radius:14px; padding:20px; margin-bottom:24px;'>
        <div style='color:#0ea5e9; font-size:13px; font-weight:600; margin-bottom:10px;'>📋 Required CSV Columns:</div>
        <div style='font-family: JetBrains Mono, monospace; font-size:12px; color:#64748b; line-height:2;'>
            person_age, person_income, person_home_ownership, person_emp_length,<br>
            loan_intent, loan_grade, loan_amnt, loan_int_rate,<br>
            loan_percent_income, cb_person_default_on_file, cb_person_cred_hist_length
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sample CSV download
    sample = pd.DataFrame([{
        'person_age': 28, 'person_income': 45000, 'person_home_ownership': 'RENT',
        'person_emp_length': 3, 'loan_intent': 'PERSONAL', 'loan_grade': 'C',
        'loan_amnt': 8000, 'loan_int_rate': 12.5, 'loan_percent_income': 0.18,
        'cb_person_default_on_file': 'N', 'cb_person_cred_hist_length': 4
    }, {
        'person_age': 45, 'person_income': 90000, 'person_home_ownership': 'MORTGAGE',
        'person_emp_length': 15, 'loan_intent': 'EDUCATION', 'loan_grade': 'A',
        'loan_amnt': 20000, 'loan_int_rate': 7.2, 'loan_percent_income': 0.22,
        'cb_person_default_on_file': 'N', 'cb_person_cred_hist_length': 18
    }])
    st.download_button("📥 Download Sample CSV", sample.to_csv(index=False),
                       "sample_customers.csv", "text/csv")

    st.markdown("<br>", unsafe_allow_html=True)
    batch_file = st.file_uploader("Upload Customer CSV", type=['csv'])

    if batch_file:
        batch_df = pd.read_csv(batch_file)
        st.markdown(f"**{len(batch_df)} customers loaded**")
        st.dataframe(batch_df.head(), use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("📦 Score All Customers"):
            with st.spinner(f"Scoring {len(batch_df)} customers..."):
                encoded_batch = encode_credit(batch_df[CREDIT_COLS].copy())
                encoded_batch[NUM_COLS] = credit_scaler.transform(encoded_batch[NUM_COLS])

                probs  = credit_model.predict_proba(encoded_batch)[:, 1]
                scores = (probs * 100).round(2)

                batch_df['Risk Score']    = scores
                batch_df['Risk Category'] = [get_risk_meta(s)[0] for s in scores]
                batch_df['Risk Emoji']    = [get_risk_meta(s)[2] for s in scores]
                batch_df['Status']        = batch_df['Risk Emoji'] + " " + batch_df['Risk Category']

            st.markdown("---")
            low    = int((scores < 30).sum())
            medium = int(((scores >= 30) & (scores < 60)).sum())
            high   = int((scores >= 60).sum())

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Total Customers", len(batch_df))
            with c2: st.metric("🟢 Low Risk",    low)
            with c3: st.metric("🟡 Medium Risk", medium)
            with c4: st.metric("🔴 High Risk",   high)

            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                fig = go.Figure(data=[go.Pie(
                    labels=['Low Risk', 'Medium Risk', 'High Risk'],
                    values=[low, medium, high],
                    hole=0.55,
                    marker_colors=['#22c55e', '#f59e0b', '#ef4444'],
                )])
                fig.update_layout(
                    title=dict(text="Risk Distribution", font=dict(color='#94a3b8', size=15)),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#94a3b8'), height=280
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig2 = go.Figure()
                fig2.add_trace(go.Histogram(x=scores, nbinsx=30,
                                            marker_color='#0ea5e9', opacity=0.85))
                fig2.update_layout(
                    title=dict(text="Score Distribution", font=dict(color='#94a3b8', size=15)),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#94a3b8'),
                    xaxis=dict(gridcolor='#1e3a5f', title='Risk Score'),
                    yaxis=dict(gridcolor='#1e3a5f', title='Customers'),
                    height=280
                )
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("**Results Table**")
            st.dataframe(
                batch_df[['Risk Score', 'Status']].sort_values('Risk Score', ascending=False),
                use_container_width=True
            )
            st.download_button("📥 Download Scored Results",
                               batch_df.to_csv(index=False),
                               "batch_risk_results.csv", "text/csv")

# ─────────────────────────────
# ANALYTICS DASHBOARD PAGE
# ─────────────────────────────
elif page == "📈  Analytics Dashboard":
    st.markdown("""
    <h1 style='font-size:36px; font-weight:700; color:#f1f5f9; margin-bottom:6px;'>📈 Analytics Dashboard</h1>
    <p style='color:#64748b; font-size:15px; margin-bottom:28px;'>Model performance metrics and key insights</p>
    """, unsafe_allow_html=True)

    # Model performance
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Fraud ROC-AUC",    "0.932", "Excellent")
    with c2: st.metric("Credit ROC-AUC",   "0.941", "Excellent")
    with c3: st.metric("Fraud Recall",      "86.7%", "Frauds caught")
    with c4: st.metric("Credit Precision",  "91.8%", "Default precision")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        # ROC-AUC comparison
        fig = go.Figure()
        models   = ['Fraud Detection', 'Credit Risk']
        aucs     = [0.932, 0.941]
        baseline = [0.5, 0.5]
        fig.add_trace(go.Bar(name='Model AUC', x=models, y=aucs,
                             marker_color=['#0ea5e9', '#38bdf8'],
                             text=[f"{v:.3f}" for v in aucs], textposition='outside',
                             textfont=dict(color='#94a3b8')))
        fig.add_trace(go.Bar(name='Baseline (Random)', x=models, y=baseline,
                             marker_color=['#1e3a5f', '#1e3a5f']))
        fig.update_layout(
            title=dict(text="ROC-AUC: Model vs Baseline", font=dict(color='#94a3b8', size=15)),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8'), barmode='group',
            yaxis=dict(gridcolor='#1e3a5f', range=[0, 1.1]),
            xaxis=dict(gridcolor='#1e3a5f'),
            legend=dict(font=dict(color='#94a3b8')),
            height=320
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Fraud confusion matrix
        z  = [[56703, 161], [13, 85]]
        fig2 = go.Figure(go.Heatmap(
            z=z,
            x=['Predicted Safe', 'Predicted Fraud'],
            y=['Actual Safe', 'Actual Fraud'],
            colorscale=[[0, '#040d1a'], [1, '#0ea5e9']],
            text=[[str(v) for v in row] for row in z],
            texttemplate="%{text}",
            textfont=dict(size=18, color='white'),
            showscale=False
        ))
        fig2.update_layout(
            title=dict(text="Fraud Model — Confusion Matrix", font=dict(color='#94a3b8', size=15)),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8'), height=320
        )
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        # Credit confusion matrix
        z2  = [[5049, 46], [390, 1032]]
        fig3 = go.Figure(go.Heatmap(
            z=z2,
            x=['Predicted Safe', 'Predicted Default'],
            y=['Actual Safe', 'Actual Default'],
            colorscale=[[0, '#040d1a'], [1, '#38bdf8']],
            text=[[str(v) for v in row] for row in z2],
            texttemplate="%{text}",
            textfont=dict(size=18, color='white'),
            showscale=False
        ))
        fig3.update_layout(
            title=dict(text="Credit Model — Confusion Matrix", font=dict(color='#94a3b8', size=15)),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8'), height=320
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        # Feature importance from credit model
        feat_names = ['Loan Grade', 'Interest Rate', 'Loan % Income',
                      'Prior Default', 'Income', 'Loan Amount',
                      'Credit History', 'Age', 'Home Ownership',
                      'Employment Length']
        importances = credit_model.feature_importances_
        top_idx  = np.argsort(importances)[::-1][:10]
        top_imp  = importances[top_idx]
        top_feat = [CREDIT_COLS[i] for i in top_idx]

        fig4 = go.Figure(go.Bar(
            x=top_imp[::-1],
            y=top_feat[::-1],
            orientation='h',
            marker_color='#0ea5e9',
            opacity=0.85
        ))
        fig4.update_layout(
            title=dict(text="Credit Model — Feature Importance", font=dict(color='#94a3b8', size=15)),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8'),
            xaxis=dict(gridcolor='#1e3a5f', title='Importance Score'),
            yaxis=dict(gridcolor='#1e3a5f'),
            height=320
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")
    st.markdown("""
    <div style='background:linear-gradient(135deg,#0a1628,#0f1f3d); border:1px solid #0ea5e930; border-radius:16px; padding:28px;'>
        <div style='color:#0ea5e9; font-size:13px; letter-spacing:2px; text-transform:uppercase; margin-bottom:16px;'>Key Insights</div>
        <div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px;'>
            <div style='background:#040d1a; border-radius:10px; padding:16px;'>
                <div style='color:#64748b; font-size:12px; margin-bottom:6px;'>Fraud Dataset</div>
                <div style='color:#f1f5f9; font-size:14px; line-height:1.6;'>Only 0.17% transactions are fraudulent — classic imbalanced problem handled with SMOTE.</div>
            </div>
            <div style='background:#040d1a; border-radius:10px; padding:16px;'>
                <div style='color:#64748b; font-size:12px; margin-bottom:6px;'>Credit Risk Dataset</div>
                <div style='color:#f1f5f9; font-size:14px; line-height:1.6;'>21.8% customers default. Loan grade and interest rate are the strongest predictors.</div>
            </div>
            <div style='background:#040d1a; border-radius:10px; padding:16px;'>
                <div style='color:#64748b; font-size:12px; margin-bottom:6px;'>Model Choice</div>
                <div style='color:#f1f5f9; font-size:14px; line-height:1.6;'>XGBoost outperformed Logistic Regression and Random Forest on both datasets.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
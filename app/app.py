import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
import shap
import warnings
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from fpdf import FPDF
try:
    from config import EMAIL_ADDRESS, EMAIL_PASSWORD
except:
    try:
        EMAIL_ADDRESS  = st.secrets["EMAIL_ADDRESS"]
        EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
    except:
        EMAIL_ADDRESS  = ""
        EMAIL_PASSWORD = ""

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
# SESSION STATE INIT
# ─────────────────────────────
for key, val in {
    'logged_in':       False,
    'username':        "",
    'theme':           'dark',
    'login_attempts':  0,
    'locked_until':    None,
    'last_activity':   datetime.now(),
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ─────────────────────────────
# SESSION TIMEOUT (10 minutes)
# ─────────────────────────────
TIMEOUT_MINUTES = 10
if st.session_state.logged_in:
    idle = datetime.now() - st.session_state.last_activity
    if idle > timedelta(minutes=TIMEOUT_MINUTES):
        st.session_state.logged_in   = False
        st.session_state.username    = ""
        st.session_state.last_activity = datetime.now()
        st.warning("⏱️ Session expired due to inactivity. Please login again.")
        st.rerun()
    else:
        st.session_state.last_activity = datetime.now()

# ─────────────────────────────
# USER DATABASE WITH ROLES
# ─────────────────────────────
USERS = {
    "admin":   {"password": "finrisk2024", "role": "admin"},
    "analyst": {"password": "analyst123",  "role": "analyst"},
    "demo":    {"password": "demo123",     "role": "analyst"},
}

# ─────────────────────────────
# THEME COLORS
# ─────────────────────────────
if st.session_state.theme == 'dark':
    BG       = "#040d1a"
    CARD     = "#0a1628"
    CARD2    = "#0f1f3d"
    BORDER   = "#1e3a5f"
    TXT      = "#e2e8f0"
    MUTED    = "#64748b"
    SUB      = "#94a3b8"
    ACCENT   = "#0ea5e9"
    SIDEBAR  = "#060f1f"
    PLOT_BG  = "rgba(0,0,0,0)"
    GRID     = "#1e3a5f"
else:
    BG       = "#f0f4f8"
    CARD     = "#ffffff"
    CARD2    = "#e8f0fe"
    BORDER   = "#cbd5e1"
    TXT      = "#0f172a"
    MUTED    = "#64748b"
    SUB      = "#475569"
    ACCENT   = "#0284c7"
    SIDEBAR  = "#e2eaf4"
    PLOT_BG  = "rgba(255,255,255,0)"
    GRID     = "#e2e8f0"

# ─────────────────────────────
# DYNAMIC CSS
# ─────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] {{ font-family: 'Space Grotesk', sans-serif; background-color: {BG}; color: {TXT}; }}
.stApp {{ background: {BG}; }}
section[data-testid="stSidebar"] {{ background: {SIDEBAR}; border-right: 1px solid {BORDER}; }}
[data-testid="metric-container"] {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 16px; padding: 20px !important; transition: all 0.3s ease; }}
[data-testid="metric-container"]:hover {{ border-color: {ACCENT}; transform: translateY(-2px); }}
[data-testid="metric-container"] label {{ color: {MUTED} !important; font-size: 12px !important; letter-spacing: 1px; text-transform: uppercase; font-family: 'JetBrains Mono', monospace !important; }}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{ color: {ACCENT} !important; font-size: 2rem !important; font-weight: 700 !important; }}
.stButton > button {{ background: linear-gradient(135deg, {ACCENT} 0%, #0284c7 100%); color: white !important; border: none; border-radius: 12px; padding: 14px 32px; font-size: 16px; font-weight: 600; width: 100%; transition: all 0.3s ease; box-shadow: 0 4px 20px {ACCENT}40; }}
.stButton > button:hover {{ box-shadow: 0 6px 30px {ACCENT}60; transform: translateY(-2px); }}
.stTextInput input, .stNumberInput input {{ background: {CARD} !important; border: 1px solid {BORDER} !important; border-radius: 10px !important; color: {TXT} !important; }}
div[data-baseweb="select"] > div {{ background: {CARD} !important; border: 1px solid {BORDER} !important; border-radius: 10px !important; color: {TXT} !important; }}
[data-testid="stFileUploader"] {{ background: {CARD}; border: 2px dashed {BORDER}; border-radius: 16px; padding: 20px; }}
hr {{ border-color: {BORDER} !important; margin: 24px 0 !important; }}
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 3px; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────
# LOGIN PAGE
# ─────────────────────────────
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(f"""
        <div style='text-align:center; padding:60px 0 40px 0;'>
            <div style='font-size:64px;'>🏦</div>
            <div style='font-size:28px; font-weight:700; color:{ACCENT}; margin-top:16px;'>FinRisk AI</div>
            <div style='font-size:13px; color:{MUTED}; letter-spacing:3px; text-transform:uppercase; margin-top:4px;'>Intelligence Platform</div>
        </div>
        """, unsafe_allow_html=True)

        # Check if locked
        locked = False
        if st.session_state.locked_until:
            if datetime.now() < st.session_state.locked_until:
                remaining = (st.session_state.locked_until - datetime.now()).seconds
                st.error(f"🔒 Account locked. Try again in {remaining} seconds.")
                locked = True
            else:
                st.session_state.locked_until  = None
                st.session_state.login_attempts = 0

        if not locked:
            st.markdown(f"<div style='background:{CARD}; border:1px solid {BORDER}; border-radius:20px; padding:36px;'>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:18px; font-weight:600; color:{TXT}; margin-bottom:24px; text-align:center;'>Secure Login</div>", unsafe_allow_html=True)

            attempts_left = 3 - st.session_state.login_attempts
            if st.session_state.login_attempts > 0:
                st.warning(f"⚠️ {attempts_left} attempt(s) remaining before lockout!")

            username = st.text_input("Username", placeholder="Enter username", key="login_user")
            password = st.text_input("Password", type="password", placeholder="Enter password", key="login_pass")

            if st.button("🔐 Login", key="login_btn"):
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state.logged_in     = True
                    st.session_state.username      = username
                    st.session_state.login_attempts = 0
                    st.session_state.last_activity = datetime.now()
                    st.rerun()
                else:
                    st.session_state.login_attempts += 1
                    if st.session_state.login_attempts >= 3:
                        st.session_state.locked_until = datetime.now() + timedelta(minutes=2)
                        st.error("🔒 Too many failed attempts! Account locked for 2 minutes.")
                    else:
                        st.error(f"❌ Invalid credentials. {3 - st.session_state.login_attempts} attempt(s) left.")

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style='text-align:center; margin-top:20px; background:{CARD}; border:1px solid {BORDER}; border-radius:10px; padding:12px; font-size:13px; color:{MUTED};'>
                Demo &nbsp;|&nbsp; username: <span style='color:{ACCENT};'>demo</span> &nbsp;|&nbsp; password: <span style='color:{ACCENT};'>demo123</span>
            </div>
            """, unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────
# LOAD MODELS
# ─────────────────────────────
@st.cache_resource
def load_models():
    fm = joblib.load('models/fraud_model.pkl')
    cm = joblib.load('models/credit_risk_model.pkl')
    cs = joblib.load('models/credit_scaler.pkl')
    return fm, cm, cs

@st.cache_resource
def load_shap(_model):
    return shap.TreeExplainer(_model)

fraud_model, credit_model, credit_scaler = load_models()
credit_explainer = load_shap(credit_model)

# ─────────────────────────────
# CONSTANTS & HELPERS
# ─────────────────────────────
CREDIT_COLS = ['person_age','person_income','person_home_ownership','person_emp_length',
               'loan_intent','loan_grade','loan_amnt','loan_int_rate','loan_percent_income',
               'cb_person_default_on_file','cb_person_cred_hist_length']
NUM_COLS    = ['person_age','person_income','person_emp_length','loan_amnt',
               'loan_int_rate','loan_percent_income','cb_person_cred_hist_length']
HOME_MAP    = {'RENT':0,'OWN':1,'MORTGAGE':2,'OTHER':3}
INTENT_MAP  = {'PERSONAL':0,'EDUCATION':1,'MEDICAL':2,'VENTURE':3,'HOMEIMPROVEMENT':4,'DEBTCONSOLIDATION':5}
GRADE_MAP   = {'A':1,'B':2,'C':3,'D':4,'E':5,'F':6,'G':7}
DEFAULT_MAP = {'N':0,'Y':1}

def encode_credit(df):
    d = df.copy()
    if d['person_home_ownership'].dtype == object:
        d['person_home_ownership'] = d['person_home_ownership'].map(HOME_MAP)
    if d['loan_intent'].dtype == object:
        d['loan_intent'] = d['loan_intent'].map(INTENT_MAP)
    if d['loan_grade'].dtype == object:
        d['loan_grade'] = d['loan_grade'].map(GRADE_MAP)
    if d['cb_person_default_on_file'].dtype == object:
        d['cb_person_default_on_file'] = d['cb_person_default_on_file'].map(DEFAULT_MAP)
    return d

def get_risk_meta(score):
    if score < 30:
        return "LOW RISK",    "#22c55e", "🟢", "Strong financial profile. Loan approval recommended."
    elif score < 60:
        return "MEDIUM RISK", "#f59e0b", "🟡", "Moderate risk. Consider additional verification before approval."
    else:
        return "HIGH RISK",   "#ef4444", "🔴", "High default probability. Approval not recommended without collateral."

def generate_pdf(info, risk_score, category, description):
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
        recs = ["Approve loan application - low default risk detected.",
                "Standard interest rate applicable.",
                "Regular monthly monitoring recommended."]
    elif risk_score < 60:
        recs = ["Conduct additional income verification before approval.",
                "Consider a slightly higher interest rate to offset moderate risk.",
                "Request recent 3-month bank statements.",
                "Monitor account quarterly."]
    else:
        recs = ["Do not approve without collateral or guarantor.",
                "Request full credit history report.",
                "Consider partial loan with strict repayment terms.",
                "Flag for manual review by senior credit officer."]

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

def send_email(to_email, subject, body, pdf_bytes=None, filename="risk_report.pdf"):
    try:
        msg = MIMEMultipart()
        msg['From']    = EMAIL_ADDRESS
        msg['To']      = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        if pdf_bytes:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(pdf_bytes)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email error: {e}")
        return False

# ─────────────────────────────
# SIDEBAR
# ─────────────────────────────
user_role = USERS[st.session_state.username]["role"]

with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center; padding:20px 0 24px 0;'>
        <div style='font-size:44px;'>🏦</div>
        <div style='font-size:18px; font-weight:700; color:{ACCENT}; margin-top:10px;'>FinRisk AI</div>
        <div style='font-size:11px; color:{MUTED}; letter-spacing:2px; text-transform:uppercase; margin-top:4px;'>Intelligence Platform</div>
        <div style='margin-top:12px; background:{CARD}; border:1px solid {BORDER}; border-radius:8px; padding:8px 12px; font-size:13px; color:{MUTED};'>
            👤 <span style='color:{ACCENT};'>{st.session_state.username}</span>
            &nbsp;|&nbsp;
            <span style='color:{"#22c55e" if user_role=="admin" else "#f59e0b"}; font-size:11px; text-transform:uppercase;'>{"👑 Admin" if user_role=="admin" else "🔍 Analyst"}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Theme toggle
    theme_label = "☀️ Light Mode" if st.session_state.theme == 'dark' else "🌙 Dark Mode"
    if st.button(theme_label, key="theme_btn"):
        st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Navigation based on role
    if user_role == "admin":
        nav_options = [
            "🏠  Home",
            "🔍  Fraud Detection",
            "📊  Credit Risk Scoring",
            "📦  Batch Credit Scoring",
            "📈  Analytics Dashboard",
            "👑  Admin Panel",
        ]
    else:
        nav_options = [
            "🏠  Home",
            "🔍  Fraud Detection",
            "📊  Credit Risk Scoring",
            "📦  Batch Credit Scoring",
            "📈  Analytics Dashboard",
        ]

    page = st.radio("", nav_options, label_visibility="collapsed")

    st.markdown("---")
    st.markdown(f"""
    <div style='padding:16px; background:{CARD}; border-radius:12px; border:1px solid {BORDER};'>
        <div style='color:{MUTED}; font-size:11px; text-transform:uppercase; letter-spacing:1px; margin-bottom:12px;'>Model Performance</div>
        <div style='display:flex; justify-content:space-between; margin-bottom:6px;'>
            <span style='color:{SUB}; font-size:13px;'>Fraud Detection</span>
            <span style='color:{ACCENT}; font-weight:600; font-size:13px;'>93.2%</span>
        </div>
        <div style='background:{BORDER}; border-radius:4px; height:4px; margin-bottom:12px;'>
            <div style='background:linear-gradient(90deg,{ACCENT},#38bdf8); width:93.2%; height:4px; border-radius:4px;'></div>
        </div>
        <div style='display:flex; justify-content:space-between; margin-bottom:6px;'>
            <span style='color:{SUB}; font-size:13px;'>Credit Risk</span>
            <span style='color:{ACCENT}; font-weight:600; font-size:13px;'>94.1%</span>
        </div>
        <div style='background:{BORDER}; border-radius:4px; height:4px;'>
            <div style='background:linear-gradient(90deg,{ACCENT},#38bdf8); width:94.1%; height:4px; border-radius:4px;'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Session timer
    idle_time = datetime.now() - st.session_state.last_activity
    remaining_mins = max(0, TIMEOUT_MINUTES - int(idle_time.total_seconds() / 60))
    st.markdown(f"""
    <div style='background:{CARD}; border:1px solid {BORDER}; border-radius:10px; padding:10px 14px; font-size:12px; color:{MUTED}; text-align:center; margin-bottom:12px;'>
        ⏱️ Session expires in <span style='color:{ACCENT};'>{remaining_mins} min</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Logout", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.username  = ""
        st.rerun()

# ─────────────────────────────
# HOME PAGE
# ─────────────────────────────
if page == "🏠  Home":
    st.markdown(f"""
    <div style='padding:50px 0 36px 0;'>
        <div style='font-size:12px; color:{ACCENT}; letter-spacing:3px; text-transform:uppercase; margin-bottom:14px;'>AI-Powered Financial Intelligence</div>
        <h1 style='font-size:50px; font-weight:700; color:{TXT}; line-height:1.1; margin:0;'>
            Financial Risk<br>
            <span style='background:linear-gradient(135deg,{ACCENT},#38bdf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>Intelligence Platform</span>
        </h1>
        <p style='color:{MUTED}; font-size:17px; margin-top:18px; max-width:600px; line-height:1.7;'>
            Enterprise-grade fraud detection and credit risk scoring powered by XGBoost. Built to protect financial institutions and their customers.
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Fraud Model AUC",     "93.2%", "+3.2% vs baseline")
    with c2: st.metric("Credit Model AUC",    "94.1%", "+4.1% vs baseline")
    with c3: st.metric("Transactions Trained","284K+",  "Real world data")
    with c4: st.metric("Risk Categories",     "3 Levels","Low / Med / High")

    st.markdown("---")
    cols = st.columns(4)
    features = [
        ("🔍","Fraud Detection",  "Upload transactions and flag suspicious activity instantly."),
        ("📊","Credit Scoring",   "AI-powered 0-100 risk score for any customer."),
        ("📦","Batch Scoring",    "Score hundreds of customers at once via CSV upload."),
        ("📈","Analytics",        "Deep insights into model performance and data patterns."),
    ]
    for col, (icon, title, desc) in zip(cols, features):
        with col:
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,{CARD},{CARD2}); border:1px solid {BORDER}; border-radius:16px; padding:24px; height:170px;'>
                <div style='font-size:30px; margin-bottom:10px;'>{icon}</div>
                <div style='font-size:16px; font-weight:700; color:{TXT}; margin-bottom:8px;'>{title}</div>
                <div style='color:{MUTED}; font-size:13px; line-height:1.5;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────
# FRAUD DETECTION
# ─────────────────────────────
elif page == "🔍  Fraud Detection":
    st.markdown(f"""
    <h1 style='font-size:36px; font-weight:700; color:{TXT}; margin-bottom:6px;'>🔍 Fraud Detection</h1>
    <p style='color:{MUTED}; font-size:15px; margin-bottom:28px;'>Upload a transaction CSV to identify fraudulent activity using AI</p>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Drop your transaction CSV here", type=['csv'], key="fraud_upload")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.markdown("**Data Preview**")
        st.dataframe(df.head(), use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🔍 Run Fraud Detection Analysis", key="fraud_btn"):
            with st.spinner("Analyzing transactions with AI..."):
                df_input    = df.drop(columns=['Class'], errors='ignore')
                predictions = fraud_model.predict(df_input)
                probs       = fraud_model.predict_proba(df_input)[:, 1]
                df['Fraud Probability %'] = (probs * 100).round(2)
                df['Prediction']          = predictions
                df['Status']              = df['Prediction'].apply(lambda x: '🚨 FRAUD' if x == 1 else '✅ SAFE')

            st.markdown("---")
            total       = len(df)
            fraud_count = int(df['Prediction'].sum())
            safe_count  = total - fraud_count
            fraud_rate  = round((fraud_count / total) * 100, 2)

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Total Transactions", f"{total:,}")
            with c2: st.metric("🚨 Fraudulent",       f"{fraud_count:,}")
            with c3: st.metric("✅ Safe",              f"{safe_count:,}")
            with c4: st.metric("Fraud Rate",           f"{fraud_rate}%")

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                fig = go.Figure(data=[go.Pie(
                    labels=['Safe','Fraud'], values=[safe_count, fraud_count],
                    hole=0.6, marker_colors=[ACCENT,'#ef4444'],
                    textfont=dict(color='white', size=13),
                )])
                fig.update_layout(
                    title=dict(text="Transaction Distribution", font=dict(color=SUB,size=15)),
                    paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
                    font=dict(color=SUB), legend=dict(font=dict(color=SUB)), height=300
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig2 = go.Figure()
                fig2.add_trace(go.Histogram(x=df['Fraud Probability %'], nbinsx=50, marker_color=ACCENT, opacity=0.8))
                fig2.update_layout(
                    title=dict(text="Fraud Probability Distribution", font=dict(color=SUB,size=15)),
                    paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
                    font=dict(color=SUB),
                    xaxis=dict(gridcolor=GRID, title='Probability %'),
                    yaxis=dict(gridcolor=GRID, title='Count'), height=300
                )
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("**🚨 Flagged Transactions**")
            st.dataframe(df[df['Prediction'] == 1][['Fraud Probability %','Status']].head(50), use_container_width=True)

            # Email report (admin only)
            if user_role == "admin":
                st.markdown("---")
                st.markdown("**📧 Email Fraud Report**")
                to_email = st.text_input("Send report to email:", key="fraud_email")
                if st.button("📧 Send Email Report", key="fraud_email_btn"):
                    with st.spinner("Sending email..."):
                        body = f"""
                        <h2 style='color:#0ea5e9;'>FinRisk AI - Fraud Analysis Report</h2>
                        <p>Analysis completed on {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
                        <h3>Summary:</h3>
                        <ul>
                            <li>Total Transactions: {total:,}</li>
                            <li>Fraudulent: {fraud_count:,}</li>
                            <li>Safe: {safe_count:,}</li>
                            <li>Fraud Rate: {fraud_rate}%</li>
                        </ul>
                        <p>Please find the detailed CSV report attached.</p>
                        <br><p style='color:gray; font-size:12px;'>Sent by FinRisk AI Platform</p>
                        """
                        csv_bytes = df.to_csv(index=False).encode()
                        if send_email(to_email, "FinRisk AI - Fraud Analysis Report", body):
                            st.success(f"✅ Report sent to {to_email}!")
                        else:
                            st.error("❌ Failed to send email. Check your config.py settings.")

            st.download_button("📥 Download Full Report", df.to_csv(index=False), "fraud_report.csv", "text/csv", key="fraud_dl")

# ─────────────────────────────
# CREDIT RISK SCORING
# ─────────────────────────────
elif page == "📊  Credit Risk Scoring":
    st.markdown(f"""
    <h1 style='font-size:36px; font-weight:700; color:{TXT}; margin-bottom:6px;'>📊 Credit Risk Scoring</h1>
    <p style='color:{MUTED}; font-size:15px; margin-bottom:28px;'>Enter customer profile for AI-powered risk assessment with SHAP explanation</p>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div style='color:{ACCENT};font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-bottom:14px;'>Personal Info</div>", unsafe_allow_html=True)
        age            = st.number_input("Age", 18, 100, 30)
        income         = st.number_input("Annual Income ($)", 1000, 1000000, 50000)
        emp_length     = st.number_input("Employment Length (years)", 0, 50, 5)
        home_ownership = st.selectbox("Home Ownership", ['RENT','OWN','MORTGAGE','OTHER'])
    with col2:
        st.markdown(f"<div style='color:{ACCENT};font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-bottom:14px;'>Loan Details</div>", unsafe_allow_html=True)
        loan_amnt           = st.number_input("Loan Amount ($)", 500, 100000, 10000)
        loan_int_rate       = st.number_input("Interest Rate (%)", 1.0, 30.0, 10.0)
        loan_percent_income = st.number_input("Loan % of Income", 0.0, 1.0, 0.2)
        loan_intent         = st.selectbox("Loan Intent", ['PERSONAL','EDUCATION','MEDICAL','VENTURE','HOMEIMPROVEMENT','DEBTCONSOLIDATION'])
    with col3:
        st.markdown(f"<div style='color:{ACCENT};font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-bottom:14px;'>Credit History</div>", unsafe_allow_html=True)
        loan_grade       = st.selectbox("Loan Grade", ['A','B','C','D','E','F','G'])
        cred_hist_length = st.number_input("Credit History Length (years)", 0, 50, 5)
        default_on_file  = st.selectbox("Previous Default?", ['N','Y'])

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("📊 Generate Risk Assessment", key="credit_btn"):
        raw_input = pd.DataFrame([[age, income, home_ownership, emp_length, loan_intent,
                                   loan_grade, loan_amnt, loan_int_rate, loan_percent_income,
                                   default_on_file, cred_hist_length]], columns=CREDIT_COLS)
        encoded           = encode_credit(raw_input.copy())
        encoded[NUM_COLS] = credit_scaler.transform(encoded[NUM_COLS])

        prob       = credit_model.predict_proba(encoded)[:, 1][0]
        risk_score = round(prob * 100, 2)
        category, color, emoji, description = get_risk_meta(risk_score)

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=risk_score,
                domain={'x':[0,1],'y':[0,1]},
                title={'text':"Risk Score",'font':{'color':SUB,'size':16}},
                number={'font':{'color':color,'size':44},'suffix':'/100'},
                gauge={
                    'axis':{'range':[0,100],'tickcolor':MUTED,'tickfont':{'color':MUTED}},
                    'bar':{'color':color,'thickness':0.3},
                    'bgcolor':CARD,'bordercolor':BORDER,
                    'steps':[
                        {'range':[0,30],  'color':'#052e16'},
                        {'range':[30,60], 'color':'#1c1000'},
                        {'range':[60,100],'color':'#1c0000'},
                    ],
                    'threshold':{'line':{'color':color,'width':4},'thickness':0.75,'value':risk_score}
                }
            ))
            fig.update_layout(paper_bgcolor=PLOT_BG, height=290,
                              font=dict(color=SUB), margin=dict(t=50,b=10))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,{CARD},{CARD2}); border:1px solid {color}40; border-radius:20px; padding:28px; margin-top:10px;'>
                <div style='font-size:11px; color:{MUTED}; letter-spacing:2px; text-transform:uppercase; margin-bottom:10px;'>Assessment Result</div>
                <div style='font-size:36px; font-weight:700; color:{color}; margin-bottom:8px;'>{emoji} {category}</div>
                <div style='font-size:14px; color:{SUB}; line-height:1.6; margin-bottom:20px;'>{description}</div>
                <div style='background:{BG}; border-radius:12px; padding:18px;'>
                    <div style='display:flex; justify-content:space-between; margin-bottom:8px;'>
                        <span style='color:{MUTED}; font-size:13px;'>Default Probability</span>
                        <span style='color:{color}; font-weight:600;'>{risk_score}%</span>
                    </div>
                    <div style='display:flex; justify-content:space-between; margin-bottom:8px;'>
                        <span style='color:{MUTED}; font-size:13px;'>Loan Grade</span>
                        <span style='color:{TXT}; font-weight:600;'>{loan_grade}</span>
                    </div>
                    <div style='display:flex; justify-content:space-between; margin-bottom:8px;'>
                        <span style='color:{MUTED}; font-size:13px;'>Loan / Income</span>
                        <span style='color:{TXT}; font-weight:600;'>{loan_percent_income:.0%}</span>
                    </div>
                    <div style='display:flex; justify-content:space-between;'>
                        <span style='color:{MUTED}; font-size:13px;'>Prior Default</span>
                        <span style='color:{TXT}; font-weight:600;'>{'Yes' if default_on_file=='Y' else 'No'}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # SHAP
        st.markdown("---")
        st.markdown("### 🧠 Why did the model give this score?")
        st.markdown(f"<p style='color:{MUTED}; font-size:14px;'>Red bars push risk UP. Green bars push risk DOWN.</p>", unsafe_allow_html=True)
        with st.spinner("Computing SHAP explanation..."):
            shap_vals   = credit_explainer.shap_values(encoded)[0]
            feat_labels = ['Age','Income','Home Ownership','Employment Length','Loan Intent',
                           'Loan Grade','Loan Amount','Interest Rate','Loan % Income',
                           'Prior Default','Credit History Length']
            shap_df = pd.DataFrame({'Feature':feat_labels,'SHAP Value':shap_vals})
            shap_df = shap_df.reindex(shap_df['SHAP Value'].abs().sort_values().index)
            fig_s = go.Figure(go.Bar(
                x=shap_df['SHAP Value'], y=shap_df['Feature'], orientation='h',
                marker_color=['#ef4444' if v > 0 else '#22c55e' for v in shap_df['SHAP Value']],
                text=[f"{v:+.3f}" for v in shap_df['SHAP Value']],
                textposition='outside', textfont=dict(color=SUB, size=11),
            ))
            fig_s.update_layout(
                paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
                font=dict(color=SUB),
                xaxis=dict(gridcolor=GRID, title='Impact on Risk Score', zerolinecolor=GRID),
                yaxis=dict(gridcolor=GRID),
                height=380, margin=dict(l=10,r=40,t=20,b=20)
            )
            st.plotly_chart(fig_s, use_container_width=True)

        # PDF + Email
        st.markdown("---")
        customer_info = {
            "Age": age, "Annual Income": f"${income:,}",
            "Home Ownership": home_ownership, "Employment Length": f"{emp_length} years",
            "Loan Intent": loan_intent, "Loan Grade": loan_grade,
            "Loan Amount": f"${loan_amnt:,}", "Interest Rate": f"{loan_int_rate}%",
            "Loan % of Income": f"{loan_percent_income:.0%}",
            "Previous Default": default_on_file,
            "Credit History Length": f"{cred_hist_length} years",
        }
        pdf_bytes = generate_pdf(customer_info, risk_score, category, description)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📄 Download PDF Report", data=pdf_bytes,
                file_name=f"credit_risk_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf", key="pdf_dl"
            )
        with col2:
            if user_role == "admin":
                to_email = st.text_input("Email report to:", key="credit_email")
                if st.button("📧 Send PDF via Email", key="credit_email_btn"):
                    with st.spinner("Sending..."):
                        body = f"""
                        <h2 style='color:#0ea5e9;'>FinRisk AI - Credit Risk Report</h2>
                        <p>Risk assessment completed on {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
                        <h3>Result: {emoji} {category}</h3>
                        <p><strong>Risk Score: {risk_score}/100</strong></p>
                        <p>{description}</p>
                        <p>Full PDF report is attached.</p>
                        <br><p style='color:gray; font-size:12px;'>Sent by FinRisk AI Platform</p>
                        """
                        if send_email(to_email, f"FinRisk AI - Credit Risk Report ({category})", body, pdf_bytes):
                            st.success(f"✅ Report sent to {to_email}!")
            else:
                st.info("📧 Email sending available for Admin only.")

# ─────────────────────────────
# BATCH CREDIT SCORING
# ─────────────────────────────
elif page == "📦  Batch Credit Scoring":
    st.markdown(f"""
    <h1 style='font-size:36px; font-weight:700; color:{TXT}; margin-bottom:6px;'>📦 Batch Credit Scoring</h1>
    <p style='color:{MUTED}; font-size:15px; margin-bottom:28px;'>Upload a CSV with multiple customers to score them all at once</p>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='background:{CARD}; border:1px solid {BORDER}; border-radius:14px; padding:20px; margin-bottom:24px;'>
        <div style='color:{ACCENT}; font-size:13px; font-weight:600; margin-bottom:10px;'>Required CSV Columns:</div>
        <div style='font-family:JetBrains Mono,monospace; font-size:12px; color:{MUTED}; line-height:2;'>
            person_age, person_income, person_home_ownership, person_emp_length,<br>
            loan_intent, loan_grade, loan_amnt, loan_int_rate,<br>
            loan_percent_income, cb_person_default_on_file, cb_person_cred_hist_length
        </div>
    </div>
    """, unsafe_allow_html=True)

    sample = pd.DataFrame([
        {'person_age':28,'person_income':45000,'person_home_ownership':'RENT','person_emp_length':3,
         'loan_intent':'PERSONAL','loan_grade':'C','loan_amnt':8000,'loan_int_rate':12.5,
         'loan_percent_income':0.18,'cb_person_default_on_file':'N','cb_person_cred_hist_length':4},
        {'person_age':45,'person_income':90000,'person_home_ownership':'MORTGAGE','person_emp_length':15,
         'loan_intent':'EDUCATION','loan_grade':'A','loan_amnt':20000,'loan_int_rate':7.2,
         'loan_percent_income':0.22,'cb_person_default_on_file':'N','cb_person_cred_hist_length':18},
        {'person_age':35,'person_income':30000,'person_home_ownership':'RENT','person_emp_length':1,
         'loan_intent':'MEDICAL','loan_grade':'F','loan_amnt':15000,'loan_int_rate':22.0,
         'loan_percent_income':0.50,'cb_person_default_on_file':'Y','cb_person_cred_hist_length':2},
    ])
    st.download_button("📥 Download Sample CSV", sample.to_csv(index=False),
                       "sample_customers.csv", "text/csv", key="sample_dl")

    st.markdown("<br>", unsafe_allow_html=True)
    batch_file = st.file_uploader("Upload Customer CSV", type=['csv'], key="batch_upload")

    if batch_file:
        batch_df = pd.read_csv(batch_file)
        st.markdown(f"**{len(batch_df)} customers loaded**")
        st.dataframe(batch_df.head(), use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("📦 Score All Customers", key="batch_btn"):
            missing_cols = [c for c in CREDIT_COLS if c not in batch_df.columns]
            if missing_cols:
                st.error(f"Missing columns: {missing_cols}")
                st.info("Please download the Sample CSV above and use it as a template!")
            else:
                with st.spinner(f"Scoring {len(batch_df)} customers..."):
                    enc               = encode_credit(batch_df[CREDIT_COLS].copy())
                    enc[NUM_COLS]     = credit_scaler.transform(enc[NUM_COLS])
                    probs             = credit_model.predict_proba(enc)[:, 1]
                    scores            = (probs * 100).round(2)
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
                with c2: st.metric("🟢 Low Risk",     low)
                with c3: st.metric("🟡 Medium Risk",  medium)
                with c4: st.metric("🔴 High Risk",    high)

                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    fig = go.Figure(data=[go.Pie(
                        labels=['Low Risk','Medium Risk','High Risk'],
                        values=[low, medium, high], hole=0.55,
                        marker_colors=['#22c55e','#f59e0b','#ef4444'],
                    )])
                    fig.update_layout(
                        title=dict(text="Risk Distribution", font=dict(color=SUB,size=15)),
                        paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
                        font=dict(color=SUB), height=280
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    fig2 = go.Figure()
                    fig2.add_trace(go.Histogram(x=scores, nbinsx=30, marker_color=ACCENT, opacity=0.85))
                    fig2.update_layout(
                        title=dict(text="Score Distribution", font=dict(color=SUB,size=15)),
                        paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
                        font=dict(color=SUB),
                        xaxis=dict(gridcolor=GRID, title='Risk Score'),
                        yaxis=dict(gridcolor=GRID, title='Customers'), height=280
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                st.markdown("**Results Table**")
                st.dataframe(
                    batch_df[['Risk Score','Status']].sort_values('Risk Score', ascending=False),
                    use_container_width=True
                )

                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("📥 Download Results",
                                       batch_df.to_csv(index=False),
                                       "batch_risk_results.csv", "text/csv", key="batch_dl")
                with col2:
                    if user_role == "admin":
                        to_email = st.text_input("Email results to:", key="batch_email")
                        if st.button("📧 Send Batch Report", key="batch_email_btn"):
                            with st.spinner("Sending..."):
                                body = f"""
                                <h2 style='color:#0ea5e9;'>FinRisk AI - Batch Credit Scoring Report</h2>
                                <p>Batch analysis on {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
                                <h3>Summary:</h3>
                                <ul>
                                    <li>Total Customers: {len(batch_df)}</li>
                                    <li>Low Risk: {low}</li>
                                    <li>Medium Risk: {medium}</li>
                                    <li>High Risk: {high}</li>
                                </ul>
                                <p>Full CSV results attached.</p>
                                """
                                if send_email(to_email, "FinRisk AI - Batch Credit Scoring Report", body):
                                    st.success(f"✅ Sent to {to_email}!")

# ─────────────────────────────
# ANALYTICS DASHBOARD
# ─────────────────────────────
elif page == "📈  Analytics Dashboard":
    st.markdown(f"""
    <h1 style='font-size:36px; font-weight:700; color:{TXT}; margin-bottom:6px;'>📈 Analytics Dashboard</h1>
    <p style='color:{MUTED}; font-size:15px; margin-bottom:28px;'>Model performance metrics and key insights</p>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Fraud ROC-AUC",    "0.932", "Excellent")
    with c2: st.metric("Credit ROC-AUC",   "0.941", "Excellent")
    with c3: st.metric("Fraud Recall",     "86.7%",  "Frauds caught")
    with c4: st.metric("Credit Precision", "91.8%",  "Default precision")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Model AUC', x=['Fraud Detection','Credit Risk'], y=[0.932,0.941],
                             marker_color=[ACCENT,'#38bdf8'],
                             text=['0.932','0.941'], textposition='outside', textfont=dict(color=SUB)))
        fig.add_trace(go.Bar(name='Baseline', x=['Fraud Detection','Credit Risk'], y=[0.5,0.5],
                             marker_color=[BORDER,BORDER]))
        fig.update_layout(
            title=dict(text="ROC-AUC: Model vs Baseline", font=dict(color=SUB,size=15)),
            paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
            font=dict(color=SUB), barmode='group',
            yaxis=dict(gridcolor=GRID, range=[0,1.1]),
            xaxis=dict(gridcolor=GRID),
            legend=dict(font=dict(color=SUB)), height=320
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        z = [[56703,161],[13,85]]
        fig2 = go.Figure(go.Heatmap(
            z=z, x=['Predicted Safe','Predicted Fraud'], y=['Actual Safe','Actual Fraud'],
            colorscale=[[0,CARD],[1,ACCENT]],
            text=[[str(v) for v in row] for row in z],
            texttemplate="%{text}", textfont=dict(size=18,color='white'), showscale=False
        ))
        fig2.update_layout(
            title=dict(text="Fraud Model - Confusion Matrix", font=dict(color=SUB,size=15)),
            paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
            font=dict(color=SUB), height=320
        )
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        z2 = [[5049,46],[390,1032]]
        fig3 = go.Figure(go.Heatmap(
            z=z2, x=['Predicted Safe','Predicted Default'], y=['Actual Safe','Actual Default'],
            colorscale=[[0,CARD],[1,'#38bdf8']],
            text=[[str(v) for v in row] for row in z2],
            texttemplate="%{text}", textfont=dict(size=18,color='white'), showscale=False
        ))
        fig3.update_layout(
            title=dict(text="Credit Model - Confusion Matrix", font=dict(color=SUB,size=15)),
            paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
            font=dict(color=SUB), height=320
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        importances = credit_model.feature_importances_
        top_idx  = np.argsort(importances)[::-1][:10]
        top_imp  = importances[top_idx]
        top_feat = [CREDIT_COLS[i] for i in top_idx]
        fig4 = go.Figure(go.Bar(
            x=top_imp[::-1], y=top_feat[::-1], orientation='h',
            marker_color=ACCENT, opacity=0.85
        ))
        fig4.update_layout(
            title=dict(text="Credit Model - Feature Importance", font=dict(color=SUB,size=15)),
            paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
            font=dict(color=SUB),
            xaxis=dict(gridcolor=GRID, title='Importance Score'),
            yaxis=dict(gridcolor=GRID), height=320
        )
        st.plotly_chart(fig4, use_container_width=True)

# ─────────────────────────────
# ADMIN PANEL (Admin only)
# ─────────────────────────────
elif page == "👑  Admin Panel":
    if user_role != "admin":
        st.error("🚫 Access Denied. Admin only!")
        st.stop()

    st.markdown(f"""
    <h1 style='font-size:36px; font-weight:700; color:{TXT}; margin-bottom:6px;'>👑 Admin Panel</h1>
    <p style='color:{MUTED}; font-size:15px; margin-bottom:28px;'>Manage users, system settings and platform configuration</p>
    """, unsafe_allow_html=True)

    st.markdown("### 👥 User Management")
    user_data = []
    for uname, uinfo in USERS.items():
        user_data.append({
            "Username": uname,
            "Role": "👑 Admin" if uinfo["role"] == "admin" else "🔍 Analyst",
            "Status": "✅ Active"
        })
    st.dataframe(pd.DataFrame(user_data), use_container_width=True)

    st.markdown("---")
    st.markdown("### ⚙️ System Settings")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div style='background:{CARD}; border:1px solid {BORDER}; border-radius:12px; padding:20px; text-align:center;'>
            <div style='font-size:24px;'>⏱️</div>
            <div style='color:{TXT}; font-weight:600; margin-top:8px;'>Session Timeout</div>
            <div style='color:{ACCENT}; font-size:24px; font-weight:700; margin-top:4px;'>{TIMEOUT_MINUTES} min</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style='background:{CARD}; border:1px solid {BORDER}; border-radius:12px; padding:20px; text-align:center;'>
            <div style='font-size:24px;'>🚫</div>
            <div style='color:{TXT}; font-weight:600; margin-top:8px;'>Max Login Attempts</div>
            <div style='color:{ACCENT}; font-size:24px; font-weight:700; margin-top:4px;'>3 tries</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div style='background:{CARD}; border:1px solid {BORDER}; border-radius:12px; padding:20px; text-align:center;'>
            <div style='font-size:24px;'>🔒</div>
            <div style='color:{TXT}; font-weight:600; margin-top:8px;'>Lockout Duration</div>
            <div style='color:{ACCENT}; font-size:24px; font-weight:700; margin-top:4px;'>2 min</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📧 Test Email Configuration")
    test_email = st.text_input("Send test email to:", key="test_email")
    if st.button("📧 Send Test Email", key="test_email_btn"):
        with st.spinner("Sending test email..."):
            body = """
            <h2 style='color:#0ea5e9;'>FinRisk AI - Test Email</h2>
            <p>Your email configuration is working correctly!</p>
            <p>You can now send reports from FinRisk AI Platform.</p>
            <br><p style='color:gray; font-size:12px;'>Sent by FinRisk AI Platform</p>
            """
            if send_email(test_email, "FinRisk AI - Test Email", body):
                st.success(f"✅ Test email sent to {test_email}!")
            else:
                st.error("❌ Failed. Check your config.py email settings.")
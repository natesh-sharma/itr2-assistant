import streamlit as st

st.set_page_config(
    page_title="ITR-2 Filing Assistant",
    page_icon="📋",
    layout="wide",
)

# ── Navigation ──────────────────────────────────────────────────────────────

upload = st.Page("pages/1_upload_documents.py", title="Upload Documents", icon=":material/upload_file:")
salary = st.Page("pages/2_salary.py", title="Salary", icon=":material/payments:")
capital_gains = st.Page("pages/3_capital_gains.py", title="Capital Gains", icon=":material/trending_up:")
other_sources = st.Page("pages/4_other_sources.py", title="Other Sources", icon=":material/account_balance:")
foreign_income = st.Page("pages/5_foreign_income.py", title="Foreign Dividends & DTAA", icon=":material/public:")
foreign_assets = st.Page("pages/6_foreign_assets.py", title="Foreign Assets", icon=":material/language:")
regime_comparison = st.Page("pages/7_regime_comparison.py", title="Regime Comparison", icon=":material/compare_arrows:")
review = st.Page("pages/8_review.py", title="Review & Validate", icon=":material/checklist:")
export = st.Page("pages/9_export.py", title="Download Reports", icon=":material/download:")

nav = st.navigation(
    {
        "Getting Started": [upload],
        "Income Schedules": [salary, capital_gains, other_sources],
        "Foreign Income": [foreign_income, foreign_assets],
        "Tax Computation": [regime_comparison, review],
        "Export": [export],
    }
)

# ── Sidebar progress indicator ──────────────────────────────────────────────

STEPS = [
    ("Upload Documents", "documents_uploaded"),
    ("Salary", "salary"),
    ("Capital Gains", "capital_gains"),
    ("Other Sources", "other_sources"),
    ("Foreign Income", "foreign_income"),
    ("Foreign Assets", "foreign_assets"),
    ("Regime Comparison", "regime_selected"),
    ("Review & Validate", "review_passed"),
]

with st.sidebar:
    st.markdown("### Filing Progress")
    completed = 0
    for label, key in STEPS:
        done = bool(st.session_state.get(key))
        icon = ":white_check_mark:" if done else ":black_medium_square:"
        st.markdown(f"{icon}  {label}")
        if done:
            completed += 1
    pct = int(completed / len(STEPS) * 100)
    st.progress(pct / 100, text=f"{completed}/{len(STEPS)} steps completed")

# ── Run selected page ───────────────────────────────────────────────────────

nav.run()

import streamlit as st

from utils.pdf_reader import read_pdf
from utils.form16_parser import parse_form16_part_a, parse_form16_part_b
from utils.form12ba_parser import parse_form12ba
from utils.broker_parser import parse_broker_pnl
from utils.morgan_stanley_parser import parse_morgan_stanley
from utils.form1042s_parser import parse_form1042s

st.header("Upload Your Tax Documents")
st.caption("Upload the relevant documents below. The assistant will parse them and auto-fill schedules.")

# ── Helpers ──────────────────────────────────────────────────────────────────

def _upload_section(label, key, file_type, parser_fn, description, password_needed=False):
    """Render an upload widget with optional password and expandable info."""
    with st.expander(f"What is *{label}*?", expanded=False):
        st.markdown(description)

    col1, col2 = st.columns([3, 1])
    uploaded = col1.file_uploader(f"Upload {label}", type=[file_type], key=f"uploader_{key}")
    password = None
    if password_needed:
        password = col2.text_input("PDF Password", type="password", key=f"pwd_{key}")

    if uploaded is not None:
        try:
            if file_type == "pdf":
                raw_text = read_pdf(uploaded, password=password)
                parsed = parser_fn(raw_text)
            else:
                parsed = parser_fn(uploaded)
            st.session_state[key] = parsed
            st.session_state.setdefault("documents_uploaded", {})[key] = True
            st.success(f"{label} parsed successfully.")
        except Exception as exc:
            st.error(f"Error parsing {label}: {exc}")

    if st.session_state.get("documents_uploaded", {}).get(key):
        st.markdown(f":white_check_mark: **{label}** — uploaded and parsed")


# ── 1. Form 16 Part A ───────────────────────────────────────────────────────

st.subheader("1. Form 16 Part A")
_upload_section(
    label="Form 16 Part A",
    key="form16a",
    file_type="pdf",
    parser_fn=parse_form16_part_a,
    description=(
        "Form 16 Part A is issued by your employer and contains TDS details — "
        "tax deducted from your salary each quarter, employer TAN, and PAN details."
    ),
    password_needed=True,
)

# ── 2. Form 16 Part B ───────────────────────────────────────────────────────

st.subheader("2. Form 16 Part B")
_upload_section(
    label="Form 16 Part B",
    key="form16b",
    file_type="pdf",
    parser_fn=parse_form16_part_b,
    description=(
        "Form 16 Part B contains the detailed salary breakup, exemptions, "
        "deductions under Chapter VI-A, and the total tax computation done by your employer."
    ),
    password_needed=True,
)

# ── 3. Form 12BA ─────────────────────────────────────────────────────────────

st.subheader("3. Form 12BA")
_upload_section(
    label="Form 12BA",
    key="form12ba",
    file_type="pdf",
    parser_fn=parse_form12ba,
    description=(
        "Form 12BA is a statement of perquisites provided by the employer. "
        "It includes RSU perquisite value, ESOP details, and other non-cash benefits "
        "taxable under Section 17(2)."
    ),
    password_needed=True,
)

# ── 4. Broker Tax P&L ───────────────────────────────────────────────────────

st.subheader("4. Broker Tax P&L (Zerodha / Groww)")
_upload_section(
    label="Broker Tax P&L",
    key="broker_pnl",
    file_type="xlsx",
    parser_fn=parse_broker_pnl,
    description=(
        "The Tax P&L statement from your broker (Zerodha Console or Groww) in Excel format. "
        "It contains trade-wise short-term and long-term capital gains, dividends, and STT paid."
    ),
    password_needed=False,
)

# ── 5. Morgan Stanley Statement (optional) ──────────────────────────────────

st.subheader("5. Morgan Stanley Statement (Optional)")
_upload_section(
    label="Morgan Stanley Statement",
    key="morgan_stanley",
    file_type="pdf",
    parser_fn=parse_morgan_stanley,
    description=(
        "If you hold RSUs or ESPP through Morgan Stanley (StockPlan Connect), upload your "
        "year-end statement. It provides share lot details, vesting dates, sale proceeds, "
        "and withholding tax information needed for Schedule FA."
    ),
    password_needed=False,
)

# ── 6. IRS Form 1042-S (optional) ───────────────────────────────────────────

st.subheader("6. IRS Form 1042-S (Optional)")
_upload_section(
    label="Form 1042-S",
    key="form1042s",
    file_type="pdf",
    parser_fn=parse_form1042s,
    description=(
        "Form 1042-S is issued by a US institution (e.g., Morgan Stanley, Schwab) for "
        "US-source income paid to non-resident aliens. It reports gross dividends from US stocks "
        "and the federal tax withheld. You need this for DTAA relief and Schedule FSI/TR."
    ),
    password_needed=False,
)

# ── Upload summary ──────────────────────────────────────────────────────────

st.divider()
uploaded_docs = st.session_state.get("documents_uploaded", {})
total = len(uploaded_docs)
if total > 0:
    st.info(f"{total} document(s) uploaded and parsed. Proceed to the next step.")
else:
    st.warning("No documents uploaded yet. Upload at least Form 16 to get started.")

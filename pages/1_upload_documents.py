import streamlit as st

from utils.pdf_reader import read_pdf
from utils.form16_parser import parse_form16
from utils.form12ba_parser import parse_form12ba
from utils.broker_parser import parse_zerodha_pnl
from utils.morgan_stanley_parser import parse_morgan_stanley
from utils.form1042s_parser import parse_1042s

st.header("Upload Your Tax Documents")
st.caption("Upload the relevant documents below. The assistant will parse them and auto-fill schedules.")


def _upload_pdf(label, key, parser_fn, description, password_needed=False):
    with st.expander(f"What is *{label}*?", expanded=False):
        st.markdown(description)

    col1, col2 = st.columns([3, 1])
    uploaded = col1.file_uploader(f"Upload {label}", type=["pdf"], key=f"uploader_{key}")
    password = None
    if password_needed:
        password = col2.text_input("PDF Password", type="password", key=f"pwd_{key}",
                                   help="Usually your DOB (DDMMYYYY) or PAN in lowercase")

    if uploaded is not None:
        try:
            pdf = read_pdf(uploaded, password=password)
            parsed = parser_fn(pdf)
            st.session_state[key] = parsed
            st.session_state.setdefault("documents_uploaded", {})[key] = True
            st.success(f"{label} parsed successfully.")
        except Exception as exc:
            st.error(f"Error parsing {label}: {exc}")

    if st.session_state.get("documents_uploaded", {}).get(key):
        st.markdown(f":white_check_mark: **{label}** — uploaded and parsed")


def _upload_excel(label, key, parser_fn, description):
    with st.expander(f"What is *{label}*?", expanded=False):
        st.markdown(description)

    uploaded = st.file_uploader(f"Upload {label}", type=["xlsx", "xls"], key=f"uploader_{key}")

    if uploaded is not None:
        try:
            parsed = parser_fn(uploaded)
            st.session_state[key] = parsed
            st.session_state.setdefault("documents_uploaded", {})[key] = True
            st.success(f"{label} parsed successfully.")
        except Exception as exc:
            st.error(f"Error parsing {label}: {exc}")

    if st.session_state.get("documents_uploaded", {}).get(key):
        st.markdown(f":white_check_mark: **{label}** — uploaded and parsed")


def _upload_ais_tis(label, key, description):
    with st.expander(f"What is *{label}*?", expanded=False):
        st.markdown(description)

    uploaded = st.file_uploader(f"Upload {label}", type=["pdf", "json", "csv"], key=f"uploader_{key}")

    if uploaded is not None:
        st.session_state.setdefault("documents_uploaded", {})[key] = True
        st.session_state[key] = {"raw_file": uploaded.name}
        st.success(f"{label} uploaded. Use this to cross-check auto-populated values on the income tax portal.")
        st.info("AIS/TIS/26AS are primarily for verification. The portal auto-populates data from these. "
                "Compare the parsed values from Form 16 and broker P&L against AIS data to avoid mismatch notices.")

    if st.session_state.get("documents_uploaded", {}).get(key):
        st.markdown(f":white_check_mark: **{label}** — uploaded")


# ── Required Documents ─────────────────────────────────────────────────────

st.subheader("Required Documents", divider="blue")

# 1. Form 16 Part A & B
st.markdown("#### 1. Form 16 (Part A & B)")
_upload_pdf(
    "Form 16",
    "form16",
    parse_form16,
    "**Form 16** is issued by your employer and contains:\n"
    "- **Part A**: TDS details — quarterly tax deducted, employer TAN, PAN\n"
    "- **Part B**: Salary breakup (Sec 17(1), 17(2), 17(3)), deductions, and tax computation\n\n"
    "If you have separate Part A and Part B files, upload the Part B (it has all the salary data).",
    password_needed=True,
)

# 2. Form 12BA
st.markdown("#### 2. Form 12BA")
_upload_pdf(
    "Form 12BA",
    "form12ba",
    parse_form12ba,
    "**Form 12BA** is a statement of perquisites provided by the employer. "
    "It includes RSU/ESOP perquisite value and other non-cash benefits taxable under Section 17(2).",
    password_needed=True,
)

# 3. Broker Tax P&L
st.markdown("#### 3. Broker Tax P&L (Zerodha / Groww)")
_upload_excel(
    "Broker Tax P&L",
    "broker_pnl",
    parse_zerodha_pnl,
    "The **Tax P&L statement** from your broker in Excel format. Download from:\n"
    "- **Zerodha**: Console → Reports → Tax P&L → Download\n"
    "- **Groww**: Profile → Reports → Tax P&L\n\n"
    "It contains trade-wise capital gains (STCG/LTCG), MF redemptions, and dividend details.",
)

# ── Verification Documents ─────────────────────────────────────────────────

st.subheader("Verification Documents", divider="green")
st.caption("These help cross-check your data against what the IT department has on record.")

# 4. AIS (Annual Information Statement)
st.markdown("#### 4. AIS — Annual Information Statement")
_upload_ais_tis(
    "AIS",
    "ais",
    "**AIS (Annual Information Statement)** is the most comprehensive document from the IT department. "
    "It shows ALL financial transactions reported to the department:\n"
    "- Salary, interest (savings/FD), dividends, stock transactions\n"
    "- Property purchases/sales, foreign remittances\n"
    "- TDS/TCS credits\n\n"
    "**Download from**: incometax.gov.in → Services → AIS → Download\n\n"
    "**Why it matters**: If your ITR data doesn't match AIS, you may get a mismatch notice. "
    "Always cross-check interest and dividend amounts with AIS before filing.",
)

# 5. TIS (Taxpayer Information Summary)
st.markdown("#### 5. TIS — Taxpayer Information Summary")
_upload_ais_tis(
    "TIS",
    "tis",
    "**TIS (Taxpayer Information Summary)** is a processed version of AIS. "
    "It shows the derived/computed values that the IT department will use:\n"
    "- Total salary, total interest, total dividends\n"
    "- Capital gains summary\n"
    "- TDS summary\n\n"
    "**Download from**: incometax.gov.in → Services → AIS → View TIS tab → Download\n\n"
    "**Use it to**: Verify that the totals match your Form 16 and broker P&L. "
    "If TIS shows higher interest than Form 16, your bank may have reported additional FD interest.",
)

# 6. Form 26AS
st.markdown("#### 6. Form 26AS — Tax Credit Statement")
_upload_ais_tis(
    "Form 26AS",
    "form26as",
    "**Form 26AS** is your annual tax credit statement showing:\n"
    "- All TDS deducted by employers, banks, and other deductors\n"
    "- TCS collected\n"
    "- Advance tax and self-assessment tax paid\n"
    "- High-value transactions (SFT)\n\n"
    "**Download from**: incometax.gov.in → e-File → View Form 26AS (redirects to TRACES)\n\n"
    "**Critical check**: The TDS amount in your ITR must match Form 26AS exactly. "
    "Any mismatch will result in rejected TDS credit and potential demand notice.",
)

# ── Optional Documents (Foreign Income) ────────────────────────────────────

st.subheader("Foreign Income Documents (Optional)", divider="orange")
st.caption("Required only if you hold foreign stocks, RSUs, or receive foreign dividends.")

# 7. US Brokerage Statement
st.markdown("#### 7. US Brokerage Statement")
_upload_pdf(
    "US Brokerage Statement",
    "morgan_stanley",
    parse_morgan_stanley,
    "Year-end statement from your US brokerage (Morgan Stanley, E*Trade, Schwab, Fidelity). "
    "It provides:\n"
    "- Share holdings with lot details (acquisition date, cost basis, current value)\n"
    "- RSU vesting details\n"
    "- Dividend payment history with US tax withheld\n"
    "- Closing portfolio value for Schedule FA\n\n"
    "**Download from**: Your brokerage portal → Statements → Annual Statement",
    password_needed=False,
)

# 8. IRS Form 1042-S
st.markdown("#### 8. IRS Form 1042-S")
_upload_pdf(
    "IRS Form 1042-S",
    "form1042s",
    parse_1042s,
    "**Form 1042-S** is issued by US financial institutions for US-source income "
    "paid to non-resident aliens. It reports:\n"
    "- Income code (06 = dividends from US corporations)\n"
    "- Gross income in USD\n"
    "- Federal tax withheld (usually 25% for dividends)\n\n"
    "**You need this for**: DTAA relief (Section 90), Schedule FSI, Schedule TR, and Form 67.\n\n"
    "**Download from**: Your US brokerage portal → Tax Documents → Form 1042-S\n\n"
    "**Note**: Form 1042-S follows the US calendar year (Jan-Dec), not the Indian financial year (Apr-Mar). "
    "You may need to use the Morgan Stanley activity statement for exact FY-wise dividend breakup.",
    password_needed=False,
)

# ── Upload Summary ─────────────────────────────────────────────────────────

st.divider()
uploaded_docs = st.session_state.get("documents_uploaded", {})
total = len(uploaded_docs)

if total > 0:
    st.subheader("Upload Status")
    required = {"form16": "Form 16", "form12ba": "Form 12BA", "broker_pnl": "Broker Tax P&L"}
    verification = {"ais": "AIS", "tis": "TIS", "form26as": "Form 26AS"}
    foreign = {"morgan_stanley": "US Brokerage Statement", "form1042s": "IRS Form 1042-S"}

    for group_name, group in [("Required", required), ("Verification", verification), ("Foreign Income", foreign)]:
        for key, label in group.items():
            if uploaded_docs.get(key):
                st.markdown(f":white_check_mark: {label}")
            else:
                st.markdown(f":black_square_button: {label} — not uploaded")

    st.divider()
    req_count = sum(1 for k in required if uploaded_docs.get(k))
    if req_count >= 2:
        st.success(f"{total} document(s) uploaded. Proceed to the next step.")
    else:
        st.warning("Upload at least Form 16 and Broker P&L to get started.")
else:
    st.warning("No documents uploaded yet. Upload at least Form 16 and Broker P&L to get started.")

import streamlit as st
import pandas as pd

st.header("Foreign Income -- DTAA Relief")
st.caption("Compute DTAA relief for US-source income and prepare Schedule FSI / TR data.")

# ── Load parsed data ────────────────────────────────────────────────────────

form1042s = st.session_state.get("form1042s", {})
fi = st.session_state.get("foreign_income", {})

# ── Warning banner ──────────────────────────────────────────────────────────

st.warning(
    "**Form 67 MUST be filed BEFORE submitting your ITR** to claim DTAA relief / "
    "foreign tax credit. File it on the income tax e-filing portal under "
    "'e-File > Income Tax Forms > Form 67'."
)

# ── 1042-S parsed data ─────────────────────────────────────────────────────

if form1042s:
    st.subheader("Form 1042-S Data")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**USD Values**")
        gross_usd = st.number_input(
            "Gross Dividend (USD)",
            value=fi.get("gross_dividend_usd", form1042s.get("gross_dividend_usd", 0.0)),
            min_value=0.0,
            step=0.01,
            format="%.2f",
        )
        tax_withheld_usd = st.number_input(
            "US Tax Withheld (USD)",
            value=fi.get("tax_withheld_usd", form1042s.get("tax_withheld_usd", 0.0)),
            min_value=0.0,
            step=0.01,
            format="%.2f",
        )

    with col2:
        st.markdown("**INR Conversion**")
        exchange_rate = st.number_input(
            "SBI TT Buying Rate (INR per USD)",
            value=fi.get("exchange_rate", form1042s.get("exchange_rate", 83.0)),
            min_value=0.0,
            step=0.01,
            format="%.2f",
            help="Use the SBI TT Buying Rate on the date of credit/receipt.",
        )
        rate_date = st.text_input(
            "Rate Date",
            value=fi.get("rate_date", form1042s.get("rate_date", "")),
            help="Date on which the SBI TT Buying Rate was picked.",
        )

        gross_inr = round(gross_usd * exchange_rate)
        tax_withheld_inr = round(tax_withheld_usd * exchange_rate)

        st.metric("Gross Dividend (INR)", f"{gross_inr:,.0f}")
        st.metric("US Tax Withheld (INR)", f"{tax_withheld_inr:,.0f}")

    # ── DTAA Relief Computation ─────────────────────────────────────────────

    st.subheader("DTAA Relief Computation (India-US DTAA Article 10)")

    st.markdown(
        "Under the India-US DTAA, dividend income is taxable in India but the US may "
        "withhold up to **25%** (or 15% under treaty). India allows credit for the "
        "**lower of**: tax paid in the US, or Indian tax on the foreign income."
    )

    indian_tax_rate = st.number_input(
        "Your average Indian tax rate (%)",
        value=fi.get("indian_tax_rate", 30.0),
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        format="%.1f",
        help="Approximate average rate of Indian tax applicable on this income.",
    )

    indian_tax_on_foreign = round(gross_inr * indian_tax_rate / 100)
    dtaa_relief = min(tax_withheld_inr, indian_tax_on_foreign)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Indian tax on foreign income", f"{indian_tax_on_foreign:,.0f}")
    col_b.metric("US tax withheld (INR)", f"{tax_withheld_inr:,.0f}")
    col_c.metric("DTAA Relief (lower of above)", f"{dtaa_relief:,.0f}")

else:
    st.info(
        "No Form 1042-S uploaded. Upload it on the Upload Documents page to auto-fill "
        "foreign income details, or enter values manually below."
    )
    gross_usd = st.number_input("Gross Dividend (USD)", value=fi.get("gross_dividend_usd", 0.0), min_value=0.0, step=0.01, format="%.2f")
    tax_withheld_usd = st.number_input("US Tax Withheld (USD)", value=fi.get("tax_withheld_usd", 0.0), min_value=0.0, step=0.01, format="%.2f")
    exchange_rate = st.number_input("SBI TT Buying Rate", value=fi.get("exchange_rate", 83.0), min_value=0.0, step=0.01, format="%.2f")
    rate_date = st.text_input("Rate Date", value=fi.get("rate_date", ""))

    gross_inr = round(gross_usd * exchange_rate)
    tax_withheld_inr = round(tax_withheld_usd * exchange_rate)
    indian_tax_rate = st.number_input("Your average Indian tax rate (%)", value=fi.get("indian_tax_rate", 30.0), min_value=0.0, max_value=100.0, step=0.1, format="%.1f")
    indian_tax_on_foreign = round(gross_inr * indian_tax_rate / 100)
    dtaa_relief = min(tax_withheld_inr, indian_tax_on_foreign)

# ── Schedule FSI Preview ────────────────────────────────────────────────────

st.divider()
st.subheader("Schedule FSI Preview")
st.caption("Details of income from outside India and tax relief claimed.")

fsi_data = {
    "Sl No": ["1"],
    "Country Code": ["US (1)"],
    "Taxpayer ID": [form1042s.get("taxpayer_id", "")],
    "Head of Income": ["Income from Other Sources"],
    "Income from outside India (INR)": [gross_inr],
    "Tax paid outside India (INR)": [tax_withheld_inr],
    "Tax relief available (INR)": [dtaa_relief],
    "Relevant DTAA Article": ["Article 10"],
}
st.dataframe(pd.DataFrame(fsi_data), use_container_width=True, hide_index=True)

# ── Schedule TR Preview ─────────────────────────────────────────────────────

st.subheader("Schedule TR Preview")
st.caption("Summary of tax relief claimed under section 90/91.")

tr_data = {
    "Sl No": ["1"],
    "Country Code": ["US (1)"],
    "Tax ID No": [form1042s.get("taxpayer_id", "")],
    "Total tax paid outside India": [tax_withheld_inr],
    "Total tax relief claimed": [dtaa_relief],
    "Section under which relief claimed": ["90"],
}
st.dataframe(pd.DataFrame(tr_data), use_container_width=True, hide_index=True)

# ── Form 67 Filing Guide ────────────────────────────────────────────────────

st.divider()
st.subheader("Form 67 Filing Guide")

with st.expander("Step-by-step instructions", expanded=True):
    st.markdown("""
**When to file:** Before submitting ITR-2 (can be filed on the same day).

**Steps:**

1. Log in to [incometax.gov.in](https://www.incometax.gov.in)
2. Go to **e-File** > **Income Tax Forms** > **Form 67**
3. Select **Assessment Year** and click **Continue**
4. Fill in the following:
   - **Country:** United States (1)
   - **Article of DTAA:** Article 10 (Dividends)
   - **Head of income:** Income from Other Sources
   - **Income outside India:** Enter the gross dividend in INR
   - **Tax paid outside India:** Enter US tax withheld in INR
   - **Tax relief claimed:** Enter the DTAA relief amount
   - **TRC:** Upload Tax Residency Certificate if available
5. Attach **Form 1042-S** as supporting document
6. **Preview** and **Submit** with e-verification (Aadhaar OTP / DSC)
7. Note the **Acknowledgement Number** for your records

**Documents to keep ready:**
- Form 1042-S (PDF)
- Tax Residency Certificate (if available)
- Proof of SBI TT Buying Rate on date of receipt
""")

# ── Persist ─────────────────────────────────────────────────────────────────

st.session_state["foreign_income"] = {
    "gross_dividend_usd": gross_usd,
    "tax_withheld_usd": tax_withheld_usd,
    "exchange_rate": exchange_rate,
    "rate_date": rate_date,
    "gross_dividend_inr": gross_inr,
    "tax_withheld_inr": tax_withheld_inr,
    "indian_tax_rate": indian_tax_rate,
    "indian_tax_on_foreign": indian_tax_on_foreign,
    "dtaa_relief": dtaa_relief,
}

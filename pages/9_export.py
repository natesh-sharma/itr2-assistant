import streamlit as st
import pandas as pd
import io
import csv
from datetime import date

st.header("Download Reports")
st.caption("Download generated reports and data files for your ITR-2 filing.")

# ── Gather all data ─────────────────────────────────────────────────────────

salary = st.session_state.get("salary", {})
cg = st.session_state.get("capital_gains", {})
os_data = st.session_state.get("other_sources", {})
fi = st.session_state.get("foreign_income", {})
fa = st.session_state.get("foreign_assets", {})
regime = st.session_state.get("regime_selected", {})
form16a = st.session_state.get("form16a", {})


# ── 1. Schedule 112A CSV ───────────────────────────────────────────────────

st.subheader("1. Schedule 112A CSV")
st.caption("CSV in the format accepted by the ITR e-filing portal for bulk upload of LTCG 112A trades.")

ltcg_trades = cg.get("ltcg_112a_trades", [])
if ltcg_trades:
    df_112a = pd.DataFrame(ltcg_trades)
    buf = io.StringIO()
    df_112a.to_csv(buf, index=False, quoting=csv.QUOTE_NONNUMERIC)
    st.download_button(
        label="Download Schedule 112A CSV",
        data=buf.getvalue(),
        file_name="schedule_112a.csv",
        mime="text/csv",
    )
    with st.expander("Preview"):
        st.dataframe(df_112a, use_container_width=True, hide_index=True)
else:
    st.info("No LTCG 112A trade data available. Complete the Capital Gains page first.")

# ── 2. Tax Computation Summary ──────────────────────────────────────────────

st.subheader("2. Tax Computation Summary")
st.caption("A text summary of your complete tax computation for reference.")

recommended = regime.get("recommendation", "New Regime")
chosen_tax = regime.get("new_regime_tax", 0) if "New" in recommended else regime.get("old_regime_tax", 0)

summary_lines = [
    f"ITR-2 Tax Computation Summary",
    f"Generated: {date.today().isoformat()}",
    f"{'=' * 50}",
    f"",
    f"INCOME SUMMARY",
    f"{'-' * 50}",
    f"  Salary (net):                {salary.get('net_salary', 0):>15,.0f}",
    f"  Capital Gains - STCG:        {cg.get('total_stcg', 0):>15,.0f}",
    f"  Capital Gains - LTCG:        {cg.get('total_ltcg_taxable', 0):>15,.0f}",
    f"  Other Sources:               {os_data.get('total', 0):>15,.0f}",
    f"{'-' * 50}",
    f"  Gross Total Income:          {salary.get('net_salary', 0) + cg.get('total_stcg', 0) + cg.get('total_ltcg_taxable', 0) + os_data.get('total', 0):>15,.0f}",
    f"",
    f"TAX COMPUTATION ({recommended})",
    f"{'-' * 50}",
    f"  Slab tax:                    {regime.get('new_slab_tax' if 'New' in recommended else 'old_slab_tax', 0):>15,.0f}",
    f"  STCG 111A @20%:             {cg.get('stcg_111a_total', 0) * 0.20 if cg.get('stcg_111a_total', 0) > 0 else 0:>15,.0f}",
    f"  LTCG 112A @12.5%:           {cg.get('ltcg_112a_taxable', 0) * 0.125 if cg.get('ltcg_112a_taxable', 0) > 0 else 0:>15,.0f}",
    f"  LTCG 112 @12.5%:            {cg.get('ltcg_112_total', 0) * 0.125 if cg.get('ltcg_112_total', 0) > 0 else 0:>15,.0f}",
    f"  Surcharge:                   {regime.get('new_surcharge' if 'New' in recommended else 'old_surcharge', 0):>15,.0f}",
    f"  Cess @4%:                    {regime.get('new_cess' if 'New' in recommended else 'old_cess', 0):>15,.0f}",
    f"  DTAA Relief:                 {fi.get('dtaa_relief', 0):>15,.0f}",
    f"{'-' * 50}",
    f"  Net Tax Liability:           {chosen_tax:>15,.0f}",
    f"",
    f"REGIME COMPARISON",
    f"{'-' * 50}",
    f"  New Regime Tax:              {regime.get('new_regime_tax', 0):>15,.0f}",
    f"  Old Regime Tax:              {regime.get('old_regime_tax', 0):>15,.0f}",
    f"  Recommended:                 {recommended:>15}",
    f"",
]

summary_text = "\n".join(summary_lines)

st.download_button(
    label="Download Tax Computation Summary",
    data=summary_text,
    file_name="tax_computation_summary.txt",
    mime="text/plain",
)
with st.expander("Preview"):
    st.code(summary_text, language=None)

# ── 3. Filing Guide ─────────────────────────────────────────────────────────

st.subheader("3. Filing Guide (with your values)")
st.caption("Step-by-step guide for filing ITR-2 on the portal, pre-filled with your computed values.")

guide_lines = [
    f"ITR-2 Filing Guide — Pre-filled Values",
    f"Generated: {date.today().isoformat()}",
    f"{'=' * 60}",
    f"",
    f"STEP 1: Login to incometax.gov.in",
    f"  - Go to e-File > Income Tax Returns > File Income Tax Return",
    f"  - Select AY and ITR-2",
    f"",
    f"STEP 2: Schedule Salary",
    f"  - Sec 17(1): {salary.get('sec17_1', 0):,.0f}",
    f"  - Sec 17(2): {salary.get('sec17_2', 0):,.0f}",
    f"  - Sec 17(3): {salary.get('sec17_3', 0):,.0f}",
    f"  - Gross Salary: {salary.get('gross_salary', 0):,.0f}",
    f"  - Standard Deduction: {salary.get('standard_deduction', 0):,.0f}",
    f"  - Net Salary: {salary.get('net_salary', 0):,.0f}",
    f"",
    f"STEP 3: Schedule CG",
    f"  - STCG 111A: {cg.get('stcg_111a_total', 0):,.0f}",
    f"  - STCG Other: {cg.get('stcg_other_total', 0):,.0f}",
    f"  - LTCG 112A (gross): {cg.get('ltcg_112a_gross', 0):,.0f}",
    f"  - LTCG 112A (exemption): {cg.get('ltcg_112a_exemption', 0):,.0f}",
    f"  - LTCG 112A (taxable): {cg.get('ltcg_112a_taxable', 0):,.0f}",
    f"  - LTCG 112: {cg.get('ltcg_112_total', 0):,.0f}",
    f"  - Upload Schedule 112A CSV in the portal",
    f"",
    f"STEP 4: Schedule OS",
    f"  - Dividend (Indian): {os_data.get('dividend_indian', 0):,.0f}",
    f"  - Dividend (Foreign): {os_data.get('dividend_foreign', 0):,.0f}",
    f"  - Savings Interest: {os_data.get('savings_interest', 0):,.0f}",
    f"  - FD/RD Interest: {os_data.get('fd_interest', 0):,.0f}",
    f"  - Total OS: {os_data.get('total', 0):,.0f}",
    f"",
    f"STEP 5: Schedule FSI (Foreign Source Income)",
    f"  - Country: US (1)",
    f"  - Head: Income from Other Sources",
    f"  - Income: {fi.get('gross_dividend_inr', 0):,.0f}",
    f"  - Tax paid outside India: {fi.get('tax_withheld_inr', 0):,.0f}",
    f"  - Relief: {fi.get('dtaa_relief', 0):,.0f}",
    f"",
    f"STEP 6: Schedule TR (Tax Relief)",
    f"  - Country: US (1)",
    f"  - Tax paid: {fi.get('tax_withheld_inr', 0):,.0f}",
    f"  - Relief claimed: {fi.get('dtaa_relief', 0):,.0f}",
    f"  - Section: 90",
    f"",
    f"STEP 7: Schedule FA (Foreign Assets)",
    f"  - Fill details as per the Foreign Assets page",
    f"  - Ensure closing values are as of 31 March",
    f"",
    f"IMPORTANT REMINDERS:",
    f"  * File Form 67 BEFORE submitting ITR",
    f"  * Verify AIS/TIS for completeness",
    f"  * Cross-check 26AS TDS amounts",
    f"  * Keep all documents for 7 years",
    f"",
]

guide_text = "\n".join(guide_lines)

st.download_button(
    label="Download Filing Guide",
    data=guide_text,
    file_name="itr2_filing_guide.txt",
    mime="text/plain",
)
with st.expander("Preview"):
    st.code(guide_text, language=None)

# ── 4. Form 67 Data Summary ────────────────────────────────────────────────

st.subheader("4. Form 67 Data Summary")
st.caption("Key values needed when filing Form 67 on the e-filing portal.")

if fi.get("gross_dividend_inr", 0) > 0:
    form67_lines = [
        f"Form 67 — Data for Filing",
        f"Generated: {date.today().isoformat()}",
        f"{'=' * 50}",
        f"",
        f"Country of income:       United States",
        f"Country Code:            1 (US)",
        f"DTAA Article:            Article 10 (Dividends)",
        f"",
        f"Gross income (USD):      {fi.get('gross_dividend_usd', 0):.2f}",
        f"Gross income (INR):      {fi.get('gross_dividend_inr', 0):,.0f}",
        f"",
        f"Tax paid in US (USD):    {fi.get('tax_withheld_usd', 0):.2f}",
        f"Tax paid in US (INR):    {fi.get('tax_withheld_inr', 0):,.0f}",
        f"",
        f"Exchange rate used:      {fi.get('exchange_rate', 0):.2f} (SBI TT Buying)",
        f"Rate date:               {fi.get('rate_date', 'N/A')}",
        f"",
        f"Head of income:          Income from Other Sources",
        f"Section for relief:      90 (DTAA)",
        f"Relief claimed (INR):    {fi.get('dtaa_relief', 0):,.0f}",
        f"",
        f"Attach: Form 1042-S, TRC (if available)",
        f"",
    ]

    form67_text = "\n".join(form67_lines)

    st.download_button(
        label="Download Form 67 Data Summary",
        data=form67_text,
        file_name="form67_data_summary.txt",
        mime="text/plain",
    )
    with st.expander("Preview"):
        st.code(form67_text, language=None)
else:
    st.info("No foreign income data. Form 67 is not required if you have no DTAA relief to claim.")

import streamlit as st
import pandas as pd

st.header("Review & Validate")
st.caption("Final review of your ITR-2 computation and pre-filing validation checks.")

# ── Gather all data ─────────────────────────────────────────────────────────

salary = st.session_state.get("salary", {})
cg = st.session_state.get("capital_gains", {})
os_data = st.session_state.get("other_sources", {})
fi = st.session_state.get("foreign_income", {})
fa = st.session_state.get("foreign_assets", {})
regime = st.session_state.get("regime_selected", {})
form16a = st.session_state.get("form16a", {})

# ── 1. Income Summary ──────────────────────────────────────────────────────

st.subheader("1. Income Summary (All Heads)")

income_heads = {
    "Head of Income": [
        "Salaries",
        "Capital Gains — STCG",
        "Capital Gains — LTCG",
        "Other Sources",
    ],
    "Amount (Rs)": [
        salary.get("net_salary", 0),
        cg.get("total_stcg", 0),
        cg.get("total_ltcg_taxable", 0),
        os_data.get("total", 0),
    ],
}

df_income = pd.DataFrame(income_heads)
gross_total = df_income["Amount (Rs)"].sum()
total_row = pd.DataFrame({"Head of Income": ["Gross Total Income"], "Amount (Rs)": [gross_total]})
df_income = pd.concat([df_income, total_row], ignore_index=True)

st.dataframe(df_income, use_container_width=True, hide_index=True)

# ── 2. Tax Computation ─────────────────────────────────────────────────────

st.subheader("2. Tax Computation")

recommended = regime.get("recommendation", "New Regime")
chosen_tax = regime.get("new_regime_tax", 0) if "New" in recommended else regime.get("old_regime_tax", 0)

tax_rows = {
    "Item": [
        f"Tax on normal income ({recommended} slabs)",
        "Tax on STCG 111A @20%",
        "Tax on LTCG 112A @12.5%",
        "Tax on LTCG 112 @12.5%",
        "Surcharge",
        "Health & Education Cess @4%",
        "Total Tax",
        "Less: DTAA Relief (Sec 90/91)",
        "Net Tax Liability",
    ],
    "Amount (Rs)": [
        regime.get("new_slab_tax", 0) if "New" in recommended else regime.get("old_slab_tax", 0),
        cg.get("stcg_111a_total", 0) * 0.20 if cg.get("stcg_111a_total", 0) > 0 else 0,
        cg.get("ltcg_112a_taxable", 0) * 0.125 if cg.get("ltcg_112a_taxable", 0) > 0 else 0,
        cg.get("ltcg_112_total", 0) * 0.125 if cg.get("ltcg_112_total", 0) > 0 else 0,
        regime.get("new_surcharge", 0) if "New" in recommended else regime.get("old_surcharge", 0),
        regime.get("new_cess", 0) if "New" in recommended else regime.get("old_cess", 0),
        chosen_tax + fi.get("dtaa_relief", 0),
        fi.get("dtaa_relief", 0),
        chosen_tax,
    ],
}

st.dataframe(pd.DataFrame(tax_rows), use_container_width=True, hide_index=True)

# ── 3. TDS, Relief, and Refund ──────────────────────────────────────────────

st.subheader("3. TDS & Refund Computation")

tds_salary = st.number_input(
    "TDS on Salary (from Form 16 Part A / 26AS)",
    value=form16a.get("total_tds", 0),
    min_value=0,
    step=1,
)

tds_other = st.number_input(
    "TDS on other income (FD, dividend, etc.)",
    value=0,
    min_value=0,
    step=1,
)

advance_tax = st.number_input(
    "Advance Tax / Self-Assessment Tax paid",
    value=0,
    min_value=0,
    step=1,
)

total_prepaid = tds_salary + tds_other + advance_tax
balance = chosen_tax - total_prepaid

col1, col2, col3 = st.columns(3)
col1.metric("Total Tax Liability", f"{chosen_tax:,.0f}")
col2.metric("Total TDS / Tax Paid", f"{total_prepaid:,.0f}")

if balance > 0:
    col3.metric("Tax Payable", f"{balance:,.0f}", delta="Due", delta_color="inverse")
else:
    col3.metric("Refund", f"{abs(balance):,.0f}", delta="Refund")

# ── 4. Validation Checks ───────────────────────────────────────────────────

st.divider()
st.subheader("4. Validation Checks")

warnings = []
passes = []

# Check: All schedules filled
if salary.get("net_salary") is not None:
    passes.append("Salary schedule is filled.")
else:
    warnings.append("Salary schedule is not filled. Complete it before filing.")

if cg:
    passes.append("Capital gains schedule is filled.")
else:
    warnings.append("Capital gains schedule is empty. Fill it or confirm zero CG.")

if os_data:
    passes.append("Other sources schedule is filled.")
else:
    warnings.append("Other sources schedule is empty.")

if regime:
    passes.append(f"Regime comparison done. Recommended: {recommended}.")
else:
    warnings.append("Regime comparison not done. Complete it to determine optimal regime.")

# Check: FSI income matches OS foreign dividend
fsi_income = fi.get("gross_dividend_inr", 0)
os_foreign = os_data.get("dividend_foreign", 0)
if fsi_income > 0 and os_foreign > 0:
    if abs(fsi_income - os_foreign) > 1:
        warnings.append(
            f"Mismatch: FSI foreign income ({fsi_income:,.0f}) does not match "
            f"Other Sources foreign dividend ({os_foreign:,.0f}). Ensure they are consistent."
        )
    else:
        passes.append("FSI foreign income matches Other Sources foreign dividend.")

# Check: DTAA relief < Indian tax on foreign income
dtaa = fi.get("dtaa_relief", 0)
indian_tax_on_foreign = fi.get("indian_tax_on_foreign", 0)
if dtaa > 0:
    if dtaa > indian_tax_on_foreign:
        warnings.append(
            f"DTAA relief ({dtaa:,.0f}) exceeds Indian tax on foreign income "
            f"({indian_tax_on_foreign:,.0f}). This is not allowed."
        )
    else:
        passes.append("DTAA relief is within allowed limits.")

# Check: Schedule FA filled if foreign income present
has_foreign_income = fi.get("gross_dividend_inr", 0) > 0
has_fa = bool(fa)
if has_foreign_income and not has_fa:
    warnings.append(
        "Foreign income is present but Schedule FA (Foreign Assets) is not filled. "
        "Schedule FA is mandatory when you have foreign income or assets."
    )
elif has_foreign_income and has_fa:
    passes.append("Schedule FA is filled (foreign income is present).")

# Check: Form 67 reminder
if dtaa > 0:
    warnings.append(
        "REMINDER: Form 67 must be filed on the e-filing portal BEFORE submitting ITR-2 "
        "to claim DTAA relief / foreign tax credit."
    )

# Display results
for msg in passes:
    st.markdown(f":white_check_mark: {msg}")

for msg in warnings:
    st.warning(msg)

# ── Overall status ──────────────────────────────────────────────────────────

st.divider()

blocking = [w for w in warnings if "REMINDER" not in w]

if not blocking:
    st.success("All validation checks passed. Your ITR-2 is ready to file!")
    st.session_state["review_passed"] = True
else:
    st.error(f"{len(blocking)} issue(s) found. Resolve them before filing.")
    st.session_state["review_passed"] = False

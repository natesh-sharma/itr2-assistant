import streamlit as st

st.header("Schedule Salary")
st.caption("Salary income details as per Form 16 and Form 12BA. All fields are editable.")

# ── Load parsed data ────────────────────────────────────────────────────────

form16b = st.session_state.get("form16b", {})
form12ba = st.session_state.get("form12ba", {})

salary = st.session_state.get("salary", {})

# ── Section 17 breakup ──────────────────────────────────────────────────────

st.subheader("Salary Breakup (Section 17)")

col1, col2, col3 = st.columns(3)

sec17_1 = col1.number_input(
    "Sec 17(1) — Salary",
    value=salary.get("sec17_1", form16b.get("sec17_1", 0)),
    min_value=0,
    step=1,
    help="Basic salary, DA, bonus, commission, leave encashment, etc.",
)

sec17_2 = col2.number_input(
    "Sec 17(2) — Perquisites",
    value=salary.get("sec17_2", form16b.get("sec17_2", 0)),
    min_value=0,
    step=1,
    help="Value of perquisites including RSU perquisite, rent-free accommodation, etc.",
)

sec17_3 = col3.number_input(
    "Sec 17(3) — Profits in lieu of salary",
    value=salary.get("sec17_3", form16b.get("sec17_3", 0)),
    min_value=0,
    step=1,
    help="Compensation, gratuity, commutation of pension, etc.",
)

gross_salary = sec17_1 + sec17_2 + sec17_3
st.metric("Gross Salary", f"{gross_salary:,.0f}")

# ── RSU perquisite breakup (from Form 12BA) ─────────────────────────────────

if form12ba:
    st.subheader("RSU / ESOP Perquisite Breakup (Form 12BA)")
    rsu_entries = form12ba.get("rsu_entries", [])
    if rsu_entries:
        import pandas as pd

        df = pd.DataFrame(rsu_entries)
        st.dataframe(df, use_container_width=True)
        rsu_total = form12ba.get("total_perquisite", 0)
        st.info(f"Total RSU perquisite from Form 12BA: {rsu_total:,.0f}")
    else:
        st.info("No RSU/ESOP entries found in Form 12BA.")

# ── Deductions ──────────────────────────────────────────────────────────────

st.subheader("Deductions from Salary")

regime = st.radio(
    "Tax regime for standard deduction",
    ["New Regime", "Old Regime"],
    horizontal=True,
    key="salary_regime_toggle",
)

default_std_deduction = 75000 if regime == "New Regime" else 50000
std_deduction = st.number_input(
    "Standard Deduction (u/s 16(ia))",
    value=salary.get("standard_deduction", default_std_deduction),
    min_value=0,
    step=1,
)

entertainment_allowance = st.number_input(
    "Entertainment Allowance (u/s 16(ii)) — Govt employees only",
    value=salary.get("entertainment_allowance", 0),
    min_value=0,
    step=1,
)

prof_tax = st.number_input(
    "Professional Tax (u/s 16(iii))",
    value=salary.get("prof_tax", form16b.get("prof_tax", 0)),
    min_value=0,
    step=1,
)

total_deductions = std_deduction + entertainment_allowance + prof_tax
net_salary = max(gross_salary - total_deductions, 0)

# ── Summary ─────────────────────────────────────────────────────────────────

st.divider()
st.subheader("Summary")

col_a, col_b, col_c = st.columns(3)
col_a.metric("Gross Salary", f"{gross_salary:,.0f}")
col_b.metric("Total Deductions", f"{total_deductions:,.0f}")
col_c.metric("Net Salary (Head: Salaries)", f"{net_salary:,.0f}")

# ── Persist ─────────────────────────────────────────────────────────────────

st.session_state["salary"] = {
    "sec17_1": sec17_1,
    "sec17_2": sec17_2,
    "sec17_3": sec17_3,
    "gross_salary": gross_salary,
    "standard_deduction": std_deduction,
    "entertainment_allowance": entertainment_allowance,
    "prof_tax": prof_tax,
    "total_deductions": total_deductions,
    "net_salary": net_salary,
}

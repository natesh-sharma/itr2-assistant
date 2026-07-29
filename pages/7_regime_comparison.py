import streamlit as st

st.header("Old vs New Regime Comparison")
st.caption("Compare your tax liability under both regimes and pick the better one.")

# ── Gather income from session state ────────────────────────────────────────

salary = st.session_state.get("salary", {})
cg = st.session_state.get("capital_gains", {})
os_data = st.session_state.get("other_sources", {})
fi = st.session_state.get("foreign_income", {})

net_salary_new = salary.get("net_salary", 0)
gross_salary = salary.get("gross_salary", 0)
total_stcg = cg.get("total_stcg", 0)
total_ltcg_taxable = cg.get("total_ltcg_taxable", 0)
stcg_111a = cg.get("stcg_111a_total", 0)
ltcg_112a_taxable = cg.get("ltcg_112a_taxable", 0)
total_os = os_data.get("total", 0)
dtaa_relief = fi.get("dtaa_relief", 0)


# ── Tax slab functions ──────────────────────────────────────────────────────

def _new_regime_tax(taxable_income):
    """FY 2024-25 new regime slabs (Budget 2024)."""
    slabs = [
        (400000, 0.00),
        (400000, 0.05),
        (400000, 0.10),
        (400000, 0.15),
        (400000, 0.20),
        (float("inf"), 0.30),
    ]
    tax = 0
    remaining = taxable_income
    for width, rate in slabs:
        chunk = min(remaining, width)
        tax += chunk * rate
        remaining -= chunk
        if remaining <= 0:
            break
    # Section 87A rebate: if total income <= 12,00,000 (after std ded) under new
    # regime, tax is nil (up to 60,000 rebate effectively). Budget 2025 extended.
    if taxable_income <= 1200000:
        tax = 0
    return tax


def _old_regime_tax(taxable_income):
    """FY 2024-25 old regime slabs."""
    slabs = [
        (250000, 0.00),
        (250000, 0.05),
        (500000, 0.20),
        (float("inf"), 0.30),
    ]
    tax = 0
    remaining = taxable_income
    for width, rate in slabs:
        chunk = min(remaining, width)
        tax += chunk * rate
        remaining -= chunk
        if remaining <= 0:
            break
    # Section 87A rebate for old regime: income <= 5,00,000
    if taxable_income <= 500000:
        tax = 0
    return tax


def _surcharge(tax, taxable_income):
    """Compute surcharge on income tax."""
    if taxable_income <= 5000000:
        return 0
    elif taxable_income <= 10000000:
        return tax * 0.10
    elif taxable_income <= 20000000:
        return tax * 0.15
    elif taxable_income <= 50000000:
        return tax * 0.25
    else:
        return tax * 0.37


def _full_tax(tax, taxable_income):
    """Tax + surcharge + 4% cess."""
    sc = _surcharge(tax, taxable_income)
    total = tax + sc
    cess = total * 0.04
    return tax, sc, cess, total + cess


# ── Old regime deduction inputs ────────────────────────────────────────────

st.subheader("Old Regime Deductions")
st.caption("Enter deduction amounts you can claim under the old regime.")

col_ded1, col_ded2, col_ded3 = st.columns(3)

hra_exemption = col_ded1.number_input(
    "HRA Exemption (u/s 10(13A))",
    value=st.session_state.get("old_regime_hra", 0),
    min_value=0,
    step=1,
    help="House Rent Allowance exemption as per Section 10(13A) rules.",
)

sec_80c = col_ded2.number_input(
    "Section 80C (max 1.5L)",
    value=st.session_state.get("old_regime_80c", 0),
    min_value=0,
    max_value=150000,
    step=1,
    help="EPF, PPF, ELSS, LIC, tuition fees, home loan principal, etc.",
)

sec_80d = col_ded3.number_input(
    "Section 80D — Medical Insurance",
    value=st.session_state.get("old_regime_80d", 0),
    min_value=0,
    max_value=100000,
    step=1,
    help="Health insurance premium (self: 25K, parents: 25-50K).",
)

other_deductions = st.number_input(
    "Other deductions (80E, 80G, 80TTA, NPS 80CCD(1B), etc.)",
    value=st.session_state.get("old_regime_other_ded", 0),
    min_value=0,
    step=1,
)

st.session_state["old_regime_hra"] = hra_exemption
st.session_state["old_regime_80c"] = sec_80c
st.session_state["old_regime_80d"] = sec_80d
st.session_state["old_regime_other_ded"] = other_deductions

total_old_deductions = hra_exemption + sec_80c + sec_80d + other_deductions

# ── Compute old regime salary ──────────────────────────────────────────────

old_std_deduction = 50000
old_net_salary = max(gross_salary - old_std_deduction - salary.get("entertainment_allowance", 0) - salary.get("prof_tax", 0) - hra_exemption, 0)

# ── Compute taxable income under each regime ────────────────────────────────

# Normal income (taxed at slab rate)
new_normal = net_salary_new + total_os + cg.get("stcg_other_total", 0)
old_normal = old_net_salary + total_os + cg.get("stcg_other_total", 0) - total_old_deductions
old_normal = max(old_normal, 0)

# Special rate income
stcg_111a_tax_new = stcg_111a * 0.20 if stcg_111a > 0 else 0
stcg_111a_tax_old = stcg_111a * 0.20 if stcg_111a > 0 else 0
ltcg_112a_tax = ltcg_112a_taxable * 0.125 if ltcg_112a_taxable > 0 else 0
ltcg_112_tax = cg.get("ltcg_112_total", 0) * 0.125 if cg.get("ltcg_112_total", 0) > 0 else 0

# ── Side-by-side comparison ─────────────────────────────────────────────────

st.divider()
st.subheader("Tax Computation")

col_new, col_old = st.columns(2)

with col_new:
    st.markdown("### New Regime")
    st.markdown(f"**Net Salary:** {net_salary_new:,.0f}")
    st.markdown(f"**Other Sources:** {total_os:,.0f}")
    st.markdown(f"**STCG (other):** {cg.get('stcg_other_total', 0):,.0f}")
    st.markdown(f"**Normal Taxable Income:** {new_normal:,.0f}")
    st.markdown("---")

    new_slab_tax = _new_regime_tax(new_normal)
    new_special = stcg_111a_tax_new + ltcg_112a_tax + ltcg_112_tax
    new_total_tax_before = new_slab_tax + new_special
    new_tax, new_sc, new_cess, new_total = _full_tax(new_total_tax_before, new_normal + stcg_111a + total_ltcg_taxable)

    st.markdown(f"Slab tax on normal income: {new_slab_tax:,.0f}")
    st.markdown(f"STCG 111A tax @20%: {stcg_111a_tax_new:,.0f}")
    st.markdown(f"LTCG 112A tax @12.5%: {ltcg_112a_tax:,.0f}")
    st.markdown(f"LTCG 112 tax @12.5%: {ltcg_112_tax:,.0f}")
    st.markdown(f"Surcharge: {new_sc:,.0f}")
    st.markdown(f"Cess @4%: {new_cess:,.0f}")
    st.markdown(f"DTAA Relief: -{dtaa_relief:,.0f}")
    new_final = max(new_total - dtaa_relief, 0)
    st.metric("Total Tax (New)", f"{new_final:,.0f}")

with col_old:
    st.markdown("### Old Regime")
    st.markdown(f"**Net Salary (after HRA):** {old_net_salary:,.0f}")
    st.markdown(f"**Other Sources:** {total_os:,.0f}")
    st.markdown(f"**STCG (other):** {cg.get('stcg_other_total', 0):,.0f}")
    st.markdown(f"**Chapter VI-A deductions:** -{sec_80c + sec_80d + other_deductions:,.0f}")
    st.markdown(f"**Normal Taxable Income:** {old_normal:,.0f}")
    st.markdown("---")

    old_slab_tax = _old_regime_tax(old_normal)
    old_special = stcg_111a_tax_old + ltcg_112a_tax + ltcg_112_tax
    old_total_tax_before = old_slab_tax + old_special
    old_tax, old_sc, old_cess, old_total = _full_tax(old_total_tax_before, old_normal + stcg_111a + total_ltcg_taxable)

    st.markdown(f"Slab tax on normal income: {old_slab_tax:,.0f}")
    st.markdown(f"STCG 111A tax @20%: {stcg_111a_tax_old:,.0f}")
    st.markdown(f"LTCG 112A tax @12.5%: {ltcg_112a_tax:,.0f}")
    st.markdown(f"LTCG 112 tax @12.5%: {ltcg_112_tax:,.0f}")
    st.markdown(f"Surcharge: {old_sc:,.0f}")
    st.markdown(f"Cess @4%: {old_cess:,.0f}")
    st.markdown(f"DTAA Relief: -{dtaa_relief:,.0f}")
    old_final = max(old_total - dtaa_relief, 0)
    st.metric("Total Tax (Old)", f"{old_final:,.0f}")

# ── Recommendation ──────────────────────────────────────────────────────────

st.divider()
st.subheader("Recommendation")

diff = old_final - new_final

if new_final < old_final:
    st.success(f"**New Regime is better** -- you save Rs {diff:,.0f}")
    recommendation = "New Regime"
elif old_final < new_final:
    st.success(f"**Old Regime is better** -- you save Rs {-diff:,.0f}")
    recommendation = "Old Regime"
else:
    st.info("Both regimes result in the same tax. New Regime is the default.")
    recommendation = "Either"

col_r1, col_r2, col_r3 = st.columns(3)
col_r1.metric("New Regime Tax", f"{new_final:,.0f}")
col_r2.metric("Old Regime Tax", f"{old_final:,.0f}")
col_r3.metric("Difference", f"{abs(diff):,.0f}", delta=f"{'Save' if diff != 0 else 'Same'}")

# ── Persist ─────────────────────────────────────────────────────────────────

st.session_state["regime_selected"] = {
    "recommendation": recommendation,
    "new_regime_tax": new_final,
    "old_regime_tax": old_final,
    "new_normal_income": new_normal,
    "old_normal_income": old_normal,
    "new_slab_tax": new_slab_tax,
    "old_slab_tax": old_slab_tax,
    "new_surcharge": new_sc,
    "old_surcharge": old_sc,
    "new_cess": new_cess,
    "old_cess": old_cess,
    "dtaa_relief": dtaa_relief,
}

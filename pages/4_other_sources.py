import streamlit as st

st.header("Schedule OS -- Other Sources")
st.caption("Income from sources other than salary and capital gains.")

# ── Load parsed data ────────────────────────────────────────────────────────

broker = st.session_state.get("broker_pnl", {})
form1042s = st.session_state.get("form1042s", {})
os_data = st.session_state.get("other_sources", {})

# ── Dividend Income ─────────────────────────────────────────────────────────

st.subheader("Dividend Income")

col1, col2 = st.columns(2)

dividend_indian = col1.number_input(
    "Dividend Income (Indian)",
    value=os_data.get("dividend_indian", broker.get("total_dividend", 0)),
    min_value=0,
    step=1,
    help="Dividend from Indian stocks and mutual funds as per broker P&L.",
)

dividend_foreign = col2.number_input(
    "Dividend Income (Foreign) in INR",
    value=os_data.get("dividend_foreign", form1042s.get("gross_dividend_inr", 0)),
    min_value=0,
    step=1,
    help="Dividend from foreign stocks (e.g., US ESPP/RSU), converted to INR. Auto-filled from Form 1042-S.",
)

if form1042s:
    with st.expander("Foreign dividend auto-fill details"):
        st.markdown(
            f"- **Gross dividend (USD):** {form1042s.get('gross_dividend_usd', 'N/A')}\n"
            f"- **Exchange rate used:** {form1042s.get('exchange_rate', 'N/A')}\n"
            f"- **Gross dividend (INR):** {form1042s.get('gross_dividend_inr', 'N/A')}"
        )

# ── Interest Income ─────────────────────────────────────────────────────────

st.subheader("Interest Income")

col3, col4 = st.columns(2)

savings_interest = col3.number_input(
    "Savings Account Interest",
    value=os_data.get("savings_interest", 0),
    min_value=0,
    step=1,
    help="Interest from savings accounts (eligible for 80TTA deduction up to Rs 10,000).",
)

fd_interest = col4.number_input(
    "FD / RD Interest",
    value=os_data.get("fd_interest", 0),
    min_value=0,
    step=1,
    help="Interest from fixed deposits, recurring deposits, and other term deposits.",
)

# ── Other income ────────────────────────────────────────────────────────────

st.subheader("Other Income")

other_income = st.number_input(
    "Any other income under this head",
    value=os_data.get("other_income", 0),
    min_value=0,
    step=1,
    help="Interest from IT refund, family pension, gifts, etc.",
)

# ── Summary ─────────────────────────────────────────────────────────────────

st.divider()
st.subheader("Summary")

total_os = dividend_indian + dividend_foreign + savings_interest + fd_interest + other_income

summary_data = {
    "Component": [
        "Dividend (Indian)",
        "Dividend (Foreign)",
        "Savings Interest",
        "FD/RD Interest",
        "Other Income",
    ],
    "Amount": [
        dividend_indian,
        dividend_foreign,
        savings_interest,
        fd_interest,
        other_income,
    ],
}

import pandas as pd

st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
st.metric("Total Income from Other Sources", f"{total_os:,.0f}")

# ── Persist ─────────────────────────────────────────────────────────────────

st.session_state["other_sources"] = {
    "dividend_indian": dividend_indian,
    "dividend_foreign": dividend_foreign,
    "savings_interest": savings_interest,
    "fd_interest": fd_interest,
    "other_income": other_income,
    "total": total_os,
}

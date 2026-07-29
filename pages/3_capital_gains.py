import streamlit as st
import pandas as pd
import io
import csv

st.header("Schedule CG -- Capital Gains")
st.caption("Capital gains computed from your broker Tax P&L. Review and edit as needed.")

# ── Load parsed data ────────────────────────────────────────────────────────

broker = st.session_state.get("broker_pnl", {})
cg = st.session_state.get("capital_gains", {})

LTCG_112A_EXEMPTION = 125000  # Rs 1.25 lakh

# ── Helper to show a trade table ────────────────────────────────────────────

def _show_trade_table(title, data_key, broker_key):
    """Display an editable trade table and return the dataframe."""
    trades = cg.get(data_key, broker.get(broker_key, []))
    if trades:
        df = pd.DataFrame(trades)
        st.dataframe(df, use_container_width=True, hide_index=True)
        total = df["pnl"].sum() if "pnl" in df.columns else 0
        return df, total
    else:
        st.info(f"No {title.lower()} trades found. Add manually or upload a broker P&L.")
        return pd.DataFrame(), 0


# ── STCG Section ────────────────────────────────────────────────────────────

st.subheader("Short-Term Capital Gains (STCG)")

with st.expander("STCG 111A — Listed equity / equity MF (15%)", expanded=True):
    stcg_111a_df, stcg_111a_total = _show_trade_table(
        "STCG 111A", "stcg_111a_trades", "stcg_111a"
    )
    stcg_111a_override = st.number_input(
        "STCG 111A Total",
        value=int(cg.get("stcg_111a_total", stcg_111a_total)),
        step=1,
        key="stcg_111a_val",
    )

with st.expander("STCG — Other (slab rate)", expanded=False):
    stcg_other_df, stcg_other_total = _show_trade_table(
        "STCG Other", "stcg_other_trades", "stcg_other"
    )
    stcg_other_override = st.number_input(
        "STCG Other Total",
        value=int(cg.get("stcg_other_total", stcg_other_total)),
        step=1,
        key="stcg_other_val",
    )

total_stcg = stcg_111a_override + stcg_other_override

# ── LTCG Section ────────────────────────────────────────────────────────────

st.subheader("Long-Term Capital Gains (LTCG)")

with st.expander("LTCG 112A — Listed equity / equity MF (12.5%)", expanded=True):
    ltcg_112a_df, ltcg_112a_total = _show_trade_table(
        "LTCG 112A", "ltcg_112a_trades", "ltcg_112a"
    )
    ltcg_112a_gross = st.number_input(
        "LTCG 112A Gross",
        value=int(cg.get("ltcg_112a_gross", ltcg_112a_total)),
        step=1,
        key="ltcg_112a_gross_val",
    )
    exemption = min(LTCG_112A_EXEMPTION, max(ltcg_112a_gross, 0))
    ltcg_112a_taxable = max(ltcg_112a_gross - exemption, 0)
    st.info(f"Exemption u/s 112A: {exemption:,.0f} | Taxable LTCG 112A: {ltcg_112a_taxable:,.0f}")

with st.expander("LTCG 112 — Debt MF / unlisted / others (12.5%)", expanded=False):
    ltcg_112_df, ltcg_112_total = _show_trade_table(
        "LTCG 112", "ltcg_112_trades", "ltcg_112"
    )
    ltcg_112_override = st.number_input(
        "LTCG 112 Total",
        value=int(cg.get("ltcg_112_total", ltcg_112_total)),
        step=1,
        key="ltcg_112_val",
    )

total_ltcg_taxable = ltcg_112a_taxable + ltcg_112_override

# ── Loss Setoff ─────────────────────────────────────────────────────────────

st.subheader("Loss Setoff")

stcg_loss = min(total_stcg, 0)
ltcg_loss = min(total_ltcg_taxable, 0)

if stcg_loss < 0 or ltcg_loss < 0:
    st.warning(
        f"STCG loss: {stcg_loss:,.0f} | LTCG loss: {ltcg_loss:,.0f}. "
        "Losses will be set off as per IT Act rules (STCG loss against STCG/LTCG, "
        "LTCG loss only against LTCG). Remaining losses can be carried forward."
    )
    carry_forward = st.number_input(
        "Loss to carry forward (Schedule CFL)",
        value=int(cg.get("carry_forward_loss", 0)),
        step=1,
    )
else:
    st.success("No capital losses to set off.")
    carry_forward = 0

# ── Summary ─────────────────────────────────────────────────────────────────

st.divider()
st.subheader("Capital Gains Summary")

col1, col2 = st.columns(2)
col1.metric("Total STCG", f"{total_stcg:,.0f}")
col2.metric("Total LTCG (taxable)", f"{total_ltcg_taxable:,.0f}")

# ── Schedule 112A CSV Download ──────────────────────────────────────────────

st.divider()
st.subheader("Schedule 112A CSV")
st.caption("Generate a CSV file in the format accepted by the ITR portal for Schedule 112A.")

if not ltcg_112a_df.empty:
    buf = io.StringIO()
    ltcg_112a_df.to_csv(buf, index=False, quoting=csv.QUOTE_NONNUMERIC)
    st.download_button(
        label="Download Schedule 112A CSV",
        data=buf.getvalue(),
        file_name="schedule_112a.csv",
        mime="text/csv",
    )
else:
    st.info("No LTCG 112A trades available. Upload a broker P&L to generate the CSV.")

# ── Persist ─────────────────────────────────────────────────────────────────

st.session_state["capital_gains"] = {
    "stcg_111a_total": stcg_111a_override,
    "stcg_other_total": stcg_other_override,
    "total_stcg": total_stcg,
    "ltcg_112a_gross": ltcg_112a_gross,
    "ltcg_112a_exemption": exemption,
    "ltcg_112a_taxable": ltcg_112a_taxable,
    "ltcg_112_total": ltcg_112_override,
    "total_ltcg_taxable": total_ltcg_taxable,
    "carry_forward_loss": carry_forward,
    "stcg_111a_trades": stcg_111a_df.to_dict("records") if not stcg_111a_df.empty else [],
    "stcg_other_trades": stcg_other_df.to_dict("records") if not stcg_other_df.empty else [],
    "ltcg_112a_trades": ltcg_112a_df.to_dict("records") if not ltcg_112a_df.empty else [],
    "ltcg_112_trades": ltcg_112_df.to_dict("records") if not ltcg_112_df.empty else [],
}

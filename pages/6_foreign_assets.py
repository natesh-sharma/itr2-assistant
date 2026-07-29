import streamlit as st
import pandas as pd

st.header("Schedule FA -- Foreign Assets")
st.caption(
    "Details of foreign assets held at any time during the previous year. "
    "Mandatory if you have any foreign income or assets."
)

# ── Load parsed data ────────────────────────────────────────────────────────

ms = st.session_state.get("morgan_stanley", {})
fa = st.session_state.get("foreign_assets", {})

# ── Auto-filled entries from Morgan Stanley ─────────────────────────────────

if ms:
    st.success("Morgan Stanley statement parsed. Entries auto-filled below.")

    st.subheader("Entry A1 -- Equity Shares Held")
    with st.expander("A1: Foreign equity shares (RSU vested shares)", expanded=True):
        col1, col2 = st.columns(2)
        a1_country = col1.text_input("Country", value=fa.get("a1_country", "United States"), key="a1_country")
        a1_entity = col2.text_input("Name of Entity", value=fa.get("a1_entity", ms.get("entity_name", "")), key="a1_entity")

        col3, col4 = st.columns(2)
        a1_institution = col3.text_input("Name of Institution", value=fa.get("a1_institution", ms.get("institution", "Morgan Stanley")), key="a1_inst")
        a1_account = col4.text_input("Account Number", value=fa.get("a1_account", ms.get("account_number", "")), key="a1_acct")

        a1_nature = st.selectbox("Nature of Asset", ["Equity Shares", "Debt Securities", "Other"], index=0, key="a1_nature")

        col5, col6 = st.columns(2)
        a1_date_acquired = col5.text_input("Date Acquired", value=fa.get("a1_date_acquired", ms.get("date_acquired", "")), key="a1_date")
        a1_initial_value = col6.number_input("Initial Value (INR)", value=fa.get("a1_initial_value", ms.get("initial_value", 0)), min_value=0, step=1, key="a1_init")

        col7, col8, col9 = st.columns(3)
        a1_peak_value = col7.number_input("Peak Value (INR)", value=fa.get("a1_peak_value", ms.get("peak_value_shares", 0)), min_value=0, step=1, key="a1_peak")
        a1_closing_value = col8.number_input("Closing Value (INR)", value=fa.get("a1_closing_value", ms.get("closing_value_shares", 0)), min_value=0, step=1, key="a1_close")
        a1_income = col9.number_input("Total Gross Income (INR)", value=fa.get("a1_income", ms.get("dividend_income", 0)), min_value=0, step=1, key="a1_income")

    st.subheader("Entry A2 -- RSU Outstanding")
    with st.expander("A2: RSU outstanding / unvested shares", expanded=True):
        col1b, col2b = st.columns(2)
        a2_country = col1b.text_input("Country", value=fa.get("a2_country", "United States"), key="a2_country")
        a2_entity = col2b.text_input("Name of Entity", value=fa.get("a2_entity", ms.get("entity_name", "")), key="a2_entity")

        col3b, col4b = st.columns(2)
        a2_institution = col3b.text_input("Name of Institution", value=fa.get("a2_institution", "Morgan Stanley"), key="a2_inst")
        a2_account = col4b.text_input("Account Number", value=fa.get("a2_account", ms.get("account_number", "")), key="a2_acct")

        col5b, col6b = st.columns(2)
        a2_peak_value = col5b.number_input("Peak Value (INR)", value=fa.get("a2_peak_value", ms.get("peak_value_rsu", 0)), min_value=0, step=1, key="a2_peak")
        a2_closing_value = col6b.number_input("Closing Value (INR)", value=fa.get("a2_closing_value", ms.get("closing_value_rsu", 0)), min_value=0, step=1, key="a2_close")

else:
    st.info(
        "No Morgan Stanley statement uploaded. Enter Schedule FA details manually below."
    )
    a1_country = ""
    a1_entity = ""
    a1_institution = ""
    a1_account = ""
    a1_nature = "Equity Shares"
    a1_date_acquired = ""
    a1_initial_value = 0
    a1_peak_value = 0
    a1_closing_value = 0
    a1_income = 0
    a2_country = ""
    a2_entity = ""
    a2_institution = ""
    a2_account = ""
    a2_peak_value = 0
    a2_closing_value = 0

# ── Manual entry section ────────────────────────────────────────────────────

st.divider()
st.subheader("Add / Edit Foreign Asset Entries")

num_entries = st.number_input(
    "Number of additional foreign asset entries",
    value=len(fa.get("manual_entries", [])),
    min_value=0,
    max_value=20,
    step=1,
    key="fa_num_entries",
)

manual_entries = fa.get("manual_entries", [])

for i in range(int(num_entries)):
    existing = manual_entries[i] if i < len(manual_entries) else {}
    with st.expander(f"Entry {i + 1}", expanded=(i == 0)):
        col_a, col_b = st.columns(2)
        country = col_a.text_input("Country", value=existing.get("country", ""), key=f"me_country_{i}")
        entity = col_b.text_input("Entity Name", value=existing.get("entity", ""), key=f"me_entity_{i}")

        col_c, col_d = st.columns(2)
        institution = col_c.text_input("Institution", value=existing.get("institution", ""), key=f"me_inst_{i}")
        account_no = col_d.text_input("Account No", value=existing.get("account_no", ""), key=f"me_acct_{i}")

        nature = st.selectbox(
            "Nature of Asset",
            ["Equity Shares", "Debt Securities", "Bank Account", "Immovable Property", "Other"],
            index=0,
            key=f"me_nature_{i}",
        )

        col_e, col_f = st.columns(2)
        date_acq = col_e.text_input("Date Acquired", value=existing.get("date_acquired", ""), key=f"me_date_{i}")
        init_val = col_f.number_input("Initial Value (INR)", value=existing.get("initial_value", 0), min_value=0, step=1, key=f"me_init_{i}")

        col_g, col_h, col_i = st.columns(3)
        peak_val = col_g.number_input("Peak Value (INR)", value=existing.get("peak_value", 0), min_value=0, step=1, key=f"me_peak_{i}")
        close_val = col_h.number_input("Closing Value (INR)", value=existing.get("closing_value", 0), min_value=0, step=1, key=f"me_close_{i}")
        income_val = col_i.number_input("Income (INR)", value=existing.get("income", 0), min_value=0, step=1, key=f"me_income_{i}")

        sale_proceeds = st.number_input("Sale Proceeds (INR)", value=existing.get("sale_proceeds", 0), min_value=0, step=1, key=f"me_sale_{i}")

        if len(manual_entries) <= i:
            manual_entries.append({})
        manual_entries[i] = {
            "country": country,
            "entity": entity,
            "institution": institution,
            "account_no": account_no,
            "nature": nature,
            "date_acquired": date_acq,
            "initial_value": init_val,
            "peak_value": peak_val,
            "closing_value": close_val,
            "income": income_val,
            "sale_proceeds": sale_proceeds,
        }

# Trim excess entries if user reduced the count
manual_entries = manual_entries[: int(num_entries)]

# ── Summary table ───────────────────────────────────────────────────────────

st.divider()
st.subheader("Schedule FA Summary")

all_entries = []
if ms:
    all_entries.append({
        "Sl": "A1",
        "Country": a1_country,
        "Entity": a1_entity,
        "Nature": a1_nature,
        "Closing Value": a1_closing_value,
        "Peak Value": a1_peak_value,
        "Income": a1_income,
    })
    all_entries.append({
        "Sl": "A2",
        "Country": a2_country,
        "Entity": a2_entity,
        "Nature": "RSU Outstanding",
        "Closing Value": a2_closing_value,
        "Peak Value": a2_peak_value,
        "Income": 0,
    })

for idx, me in enumerate(manual_entries):
    all_entries.append({
        "Sl": f"M{idx + 1}",
        "Country": me["country"],
        "Entity": me["entity"],
        "Nature": me["nature"],
        "Closing Value": me["closing_value"],
        "Peak Value": me["peak_value"],
        "Income": me["income"],
    })

if all_entries:
    st.dataframe(pd.DataFrame(all_entries), use_container_width=True, hide_index=True)
else:
    st.info("No foreign asset entries added yet.")

# ── Persist ─────────────────────────────────────────────────────────────────

fa_state = {"manual_entries": manual_entries}
if ms:
    fa_state.update({
        "a1_country": a1_country,
        "a1_entity": a1_entity,
        "a1_institution": a1_institution,
        "a1_account": a1_account,
        "a1_nature": a1_nature,
        "a1_date_acquired": a1_date_acquired,
        "a1_initial_value": a1_initial_value,
        "a1_peak_value": a1_peak_value,
        "a1_closing_value": a1_closing_value,
        "a1_income": a1_income,
        "a2_country": a2_country,
        "a2_entity": a2_entity,
        "a2_institution": a2_institution,
        "a2_account": a2_account,
        "a2_peak_value": a2_peak_value,
        "a2_closing_value": a2_closing_value,
    })

st.session_state["foreign_assets"] = fa_state

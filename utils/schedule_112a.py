import csv
import io
from pathlib import Path
from typing import Any, Dict, List, Optional

PORTAL_HEADER = [
    "Sl. No.",
    "ISIN Code",
    "Name of the Share/Unit",
    "No. of Shares/Units",
    "Sale price per Share/Unit",
    "Total Sale Value",
    "Cost of acquisition without\xa0indexation per Share/Unit\xa0If\xa0shares/unit acquired before 01.02.2018",
    "Total cost of acquisition without indexation",
    "FMV per share/unit as on 31st January 2018",
    "Expenditure wholly and exclusively in connection with transfer",
    "Total deductions",
    "Balance",
]


def generate_112a_csv(
    transactions: List[Dict[str, Any]],
    output_path: Optional[str] = None,
    template_header: Optional[List[str]] = None,
) -> str:
    header = template_header or PORTAL_HEADER

    be_rows: List[Dict[str, Any]] = []
    ae_rows: List[Dict[str, Any]] = []

    for txn in transactions:
        if txn.get("acquired_before_jan2018", False):
            be_rows.append(txn)
        else:
            ae_rows.append(txn)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)

    sl_no = 1

    for txn in be_rows:
        total_sale = txn.get("total_sale", txn["qty"] * txn["sale_price_per_unit"])
        cost_per_unit = txn.get("cost_per_unit", 0)
        total_cost = txn.get("total_cost", txn["qty"] * cost_per_unit)
        fmv = txn.get("fmv_per_unit", 0)

        grandfathered_cost = max(cost_per_unit, min(fmv, txn["sale_price_per_unit"]))
        total_grandfathered = round(grandfathered_cost * txn["qty"], 2)

        expenditure = txn.get("expenditure", 0)
        total_deductions = round(total_grandfathered + expenditure, 2)
        balance = round(total_sale - total_deductions, 2)

        writer.writerow([
            sl_no,
            txn["isin"],
            txn["name"],
            txn["qty"],
            round(txn["sale_price_per_unit"], 2),
            round(total_sale, 2),
            round(grandfathered_cost, 2),
            round(total_grandfathered, 2),
            round(fmv, 2),
            round(expenditure, 2),
            round(total_deductions, 2),
            balance,
        ])
        sl_no += 1

    if ae_rows:
        total_qty = sum(t["qty"] for t in ae_rows)
        total_sale_ae = sum(
            t.get("total_sale", t["qty"] * t["sale_price_per_unit"]) for t in ae_rows
        )
        total_cost_ae = sum(
            t.get("total_cost", t["qty"] * t.get("cost_per_unit", 0)) for t in ae_rows
        )

        avg_sale_price = round(total_sale_ae / total_qty, 2) if total_qty else 0
        avg_cost = round(total_cost_ae / total_qty, 2) if total_qty else 0
        expenditure_ae = sum(t.get("expenditure", 0) for t in ae_rows)
        total_deductions_ae = round(total_cost_ae + expenditure_ae, 2)
        balance_ae = round(total_sale_ae - total_deductions_ae, 2)

        writer.writerow([
            sl_no,
            "INNOTREQUIRD",
            "CONSOLIDATED",
            total_qty,
            avg_sale_price,
            round(total_sale_ae, 2),
            avg_cost,
            round(total_cost_ae, 2),
            "",
            round(expenditure_ae, 2),
            round(total_deductions_ae, 2),
            balance_ae,
        ])

    csv_string = output.getvalue()

    if output_path:
        Path(output_path).write_text(csv_string, encoding="utf-8")

    return csv_string

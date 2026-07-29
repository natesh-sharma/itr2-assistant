import json
from pathlib import Path
from typing import Any, Dict, List, Optional

SLABS_PATH = Path(__file__).resolve().parent.parent / "data" / "tax_slabs.json"

_slabs_cache: Optional[Dict[str, Any]] = None


def _load_slabs() -> Dict[str, Any]:
    global _slabs_cache
    if _slabs_cache is None:
        _slabs_cache = json.loads(SLABS_PATH.read_text())
    return _slabs_cache


def _compute_slab_tax(taxable_income: float, slabs: List[Dict]) -> float:
    tax = 0.0
    for slab in slabs:
        lower = slab["from"]
        upper = slab["to"]
        rate = slab["rate"] / 100

        if taxable_income <= 0:
            break

        if upper is None:
            tax += max(taxable_income - lower + 1, 0) * rate
            break

        slab_width = upper - lower + 1
        taxable_in_slab = min(max(taxable_income - lower + 1, 0), slab_width)
        tax += taxable_in_slab * rate

    return round(tax, 2)


def _find_surcharge_rate(total_income: float, surcharge_slabs: List[Dict]) -> float:
    applicable_rate = 0.0
    for slab in surcharge_slabs:
        if total_income > slab["from"]:
            applicable_rate = slab["rate"] / 100
    return applicable_rate


def _compute_surcharge_with_marginal_relief(
    base_tax: float,
    total_income: float,
    surcharge_slabs: List[Dict],
) -> Dict[str, float]:
    surcharge_rate = _find_surcharge_rate(total_income, surcharge_slabs)

    if surcharge_rate == 0:
        return {"surcharge": 0.0, "marginal_relief": 0.0}

    surcharge = round(base_tax * surcharge_rate, 2)

    threshold = 0.0
    prev_rate = 0.0
    for slab in surcharge_slabs:
        if total_income > slab["from"]:
            threshold = slab["from"]
            prev_rate_val = 0.0
            for prev_slab in surcharge_slabs:
                if threshold > prev_slab["from"] and prev_slab["from"] < slab["from"]:
                    prev_rate_val = prev_slab["rate"] / 100
            prev_rate = prev_rate_val

    tax_at_threshold = base_tax * (total_income / max(total_income, 1))
    excess_income = total_income - threshold

    tax_plus_surcharge = base_tax + surcharge
    tax_at_threshold_with_prev_surcharge = base_tax * (threshold / max(total_income, 1))
    tax_at_threshold_with_prev_surcharge += (
        tax_at_threshold_with_prev_surcharge * prev_rate
    )

    marginal_relief = max(
        tax_plus_surcharge - tax_at_threshold_with_prev_surcharge - excess_income, 0
    )
    marginal_relief = round(min(marginal_relief, surcharge), 2)

    return {
        "surcharge": surcharge,
        "marginal_relief": marginal_relief,
    }


def compute_tax_new_regime(
    normal_income: float,
    stcg_111a: float = 0,
    ltcg_112a_gross: float = 0,
    ltcg_112: float = 0,
    fy: str = "2025-26",
) -> Dict[str, float]:
    config = _load_slabs()[fy]
    new_regime = config["new_regime"]
    special = config["special_rates"]
    surcharge_slabs = config["surcharge"]
    cess_rate = config["cess_rate"] / 100

    std_deduction = new_regime["standard_deduction"]
    taxable_normal = max(normal_income - std_deduction, 0)

    tax_normal = _compute_slab_tax(taxable_normal, new_regime["slabs"])

    rebate_limit = new_regime["rebate_87a_limit"]
    rebate_max = new_regime["rebate_87a_max"]
    total_income_for_rebate = taxable_normal + stcg_111a + max(ltcg_112a_gross - special["ltcg_112a_exemption"], 0) + ltcg_112

    if total_income_for_rebate <= rebate_limit:
        tax_normal = max(tax_normal - min(tax_normal, rebate_max), 0)

    tax_stcg = round(stcg_111a * special["stcg_111a"] / 100, 2)

    ltcg_112a_taxable = max(ltcg_112a_gross - special["ltcg_112a_exemption"], 0)
    tax_ltcg_112a = round(ltcg_112a_taxable * special["ltcg_112a"] / 100, 2)

    tax_ltcg_112 = round(ltcg_112 * special["ltcg_112"] / 100, 2)

    base_tax = tax_normal + tax_stcg + tax_ltcg_112a + tax_ltcg_112

    total_income = taxable_normal + stcg_111a + ltcg_112a_gross + ltcg_112
    sr = _compute_surcharge_with_marginal_relief(base_tax, total_income, surcharge_slabs)

    net_surcharge = sr["surcharge"] - sr["marginal_relief"]
    cess = round((base_tax + net_surcharge) * cess_rate, 2)
    gross_tax = round(base_tax + net_surcharge + cess, 2)

    return {
        "regime": "new",
        "fy": fy,
        "taxable_normal_income": taxable_normal,
        "tax_normal": tax_normal,
        "tax_stcg": tax_stcg,
        "tax_ltcg_112a": tax_ltcg_112a,
        "tax_ltcg_112": tax_ltcg_112,
        "total_tax": base_tax,
        "surcharge": sr["surcharge"],
        "marginal_relief": sr["marginal_relief"],
        "cess": cess,
        "gross_tax": gross_tax,
    }


def compute_tax_old_regime(
    normal_income: float,
    stcg_111a: float = 0,
    ltcg_112a_gross: float = 0,
    ltcg_112: float = 0,
    deductions_80c: float = 0,
    deductions_80d: float = 0,
    deductions_80tta: float = 0,
    hra_exemption: float = 0,
    fy: str = "2025-26",
) -> Dict[str, float]:
    config = _load_slabs()[fy]
    old_regime = config["old_regime"]
    special = config["special_rates"]
    surcharge_slabs = config["surcharge"]
    cess_rate = config["cess_rate"] / 100

    std_deduction = old_regime["standard_deduction"]
    capped_80c = min(deductions_80c, old_regime["section_80c_limit"])
    capped_80tta = min(deductions_80tta, old_regime["section_80tta_limit"])

    total_deductions = std_deduction + capped_80c + deductions_80d + capped_80tta + hra_exemption
    taxable_normal = max(normal_income - total_deductions, 0)

    tax_normal = _compute_slab_tax(taxable_normal, old_regime["slabs"])

    rebate_limit = old_regime["rebate_87a_limit"]
    rebate_max = old_regime["rebate_87a_max"]
    if taxable_normal <= rebate_limit:
        tax_normal = max(tax_normal - min(tax_normal, rebate_max), 0)

    tax_stcg = round(stcg_111a * special["stcg_111a"] / 100, 2)

    ltcg_112a_taxable = max(ltcg_112a_gross - special["ltcg_112a_exemption"], 0)
    tax_ltcg_112a = round(ltcg_112a_taxable * special["ltcg_112a"] / 100, 2)

    tax_ltcg_112 = round(ltcg_112 * special["ltcg_112"] / 100, 2)

    base_tax = tax_normal + tax_stcg + tax_ltcg_112a + tax_ltcg_112

    total_income = taxable_normal + stcg_111a + ltcg_112a_gross + ltcg_112
    sr = _compute_surcharge_with_marginal_relief(base_tax, total_income, surcharge_slabs)

    net_surcharge = sr["surcharge"] - sr["marginal_relief"]
    cess = round((base_tax + net_surcharge) * cess_rate, 2)
    gross_tax = round(base_tax + net_surcharge + cess, 2)

    return {
        "regime": "old",
        "fy": fy,
        "total_deductions": total_deductions,
        "taxable_normal_income": taxable_normal,
        "tax_normal": tax_normal,
        "tax_stcg": tax_stcg,
        "tax_ltcg_112a": tax_ltcg_112a,
        "tax_ltcg_112": tax_ltcg_112,
        "total_tax": base_tax,
        "surcharge": sr["surcharge"],
        "marginal_relief": sr["marginal_relief"],
        "cess": cess,
        "gross_tax": gross_tax,
    }


def compare_regimes(
    normal_income: float,
    stcg_111a: float = 0,
    ltcg_112a_gross: float = 0,
    ltcg_112: float = 0,
    deductions_80c: float = 0,
    deductions_80d: float = 0,
    deductions_80tta: float = 0,
    hra_exemption: float = 0,
    fy: str = "2025-26",
) -> Dict[str, Any]:
    new = compute_tax_new_regime(normal_income, stcg_111a, ltcg_112a_gross, ltcg_112, fy)
    old = compute_tax_old_regime(
        normal_income, stcg_111a, ltcg_112a_gross, ltcg_112,
        deductions_80c, deductions_80d, deductions_80tta, hra_exemption, fy,
    )

    savings = round(old["gross_tax"] - new["gross_tax"], 2)
    recommendation = "new" if savings >= 0 else "old"

    return {
        "new_regime": new,
        "old_regime": old,
        "savings_with_new": savings,
        "recommendation": recommendation,
    }

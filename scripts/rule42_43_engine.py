"""
Rule 42 & Rule 43 Pro-Rata Input Tax Credit Reversal Engine.
Statutory calculations under CGST Rules for businesses with mixed supplies
(taxable, zero-rated, exempt, and non-business).
"""

from typing import Dict, Any, Optional


def compute_rule42_reversal(
    total_input_tax: float,
    t1_non_business: float,
    t2_exempt_exclusive: float,
    t3_blocked_sec17_5: float,
    t4_taxable_exclusive: float,
    exempt_turnover_e: float,
    total_turnover_f: float,
    has_non_business_common_use: bool = True
) -> Dict[str, Any]:
    """
    Computes Rule 42 proportionate reversal on inputs & input services.
    - C1 = T - (T1 + T2 + T3)
    - C2 (Common Credit) = C1 - T4
    - D1 (Exempt Reversal) = (E / F) * C2
    - D2 (Non-business Reversal) = 5% of C2 (if applicable)
    - C3 (Net Eligible Common Credit) = C2 - (D1 + D2)
    """
    t = float(total_input_tax)
    t1 = float(t1_non_business)
    t2 = float(t2_exempt_exclusive)
    t3 = float(t3_blocked_sec17_5)
    t4 = float(t4_taxable_exclusive)
    e = float(exempt_turnover_e)
    f = float(total_turnover_f)
    
    if f <= 0:
        raise ValueError("Total turnover (F) must be greater than zero.")
        
    c1 = max(0.0, round(t - (t1 + t2 + t3), 2))
    c2 = max(0.0, round(c1 - t4, 2))
    
    exempt_ratio = min(1.0, max(0.0, e / f))
    d1_exempt_reversal = round(exempt_ratio * c2, 2)
    d2_non_business_reversal = round(0.05 * c2, 2) if has_non_business_common_use else 0.0
    
    total_reversal = round(d1_exempt_reversal + d2_non_business_reversal, 2)
    c3_net_eligible_common_credit = max(0.0, round(c2 - total_reversal, 2))
    total_eligible_itc = round(t4 + c3_net_eligible_common_credit, 2)
    
    return {
        "statutory_rule": "Rule 42 (CGST Rules 2017)",
        "inputs": {
            "total_input_tax_T": t,
            "exclusive_non_business_T1": t1,
            "exclusive_exempt_T2": t2,
            "blocked_sec17_5_T3": t3,
            "exclusive_taxable_T4": t4,
            "exempt_turnover_E": e,
            "total_turnover_F": f,
            "exempt_turnover_ratio": round(exempt_ratio, 4)
        },
        "computed_credits": {
            "credited_to_ledger_C1": c1,
            "common_credit_C2": c2,
            "exempt_reversal_D1": d1_exempt_reversal,
            "non_business_reversal_D2": d2_non_business_reversal,
            "total_reversal_required_in_3B_4B": total_reversal,
            "net_eligible_common_credit_C3": c3_net_eligible_common_credit,
            "total_net_eligible_itc": total_eligible_itc
        },
        "gstr3b_mapping": {
            "table_4_A_all_other": c1,
            "table_4_B_1_reversal": total_reversal,
            "table_4_C_net_itc": total_eligible_itc
        }
    }


def compute_rule43_reversal(
    common_capital_goods_tc: float,
    exempt_turnover_e: float,
    total_turnover_f: float,
    useful_life_months: int = 60
) -> Dict[str, Any]:
    """
    Computes Rule 43 monthly reversal on Common Capital Goods.
    - Useful life = 60 months
    - Monthly credit Tm = Tc / 60
    - Monthly reversal Te = (E / F) * Tr
    """
    tc = float(common_capital_goods_tc)
    e = float(exempt_turnover_e)
    f = float(total_turnover_f)
    
    if f <= 0:
        raise ValueError("Total turnover (F) must be greater than zero.")
        
    monthly_credit_tm = round(tc / useful_life_months, 2)
    exempt_ratio = min(1.0, max(0.0, e / f))
    monthly_reversal_te = round(exempt_ratio * monthly_credit_tm, 2)
    net_monthly_credit = round(monthly_credit_tm - monthly_reversal_te, 2)
    
    return {
        "statutory_rule": "Rule 43 (CGST Rules 2017)",
        "inputs": {
            "common_capital_goods_credit_Tc": tc,
            "useful_life_months": useful_life_months,
            "exempt_turnover_E": e,
            "total_turnover_F": f,
            "exempt_ratio": round(exempt_ratio, 4)
        },
        "computed": {
            "monthly_credit_Tm": monthly_credit_tm,
            "monthly_reversal_Te_in_3B_4B": monthly_reversal_te,
            "net_monthly_capital_goods_credit": net_monthly_credit
        }
    }

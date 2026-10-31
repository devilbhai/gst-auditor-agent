"""
GSTR-9 & GSTR-9C Annual Return & CA Reconciliation Statement Engine.
Automates annual reconciliation required for businesses (> ₹2 Cr for GSTR-9, > ₹5 Cr for GSTR-9C).
Reconciles:
- Audited Financial Statements (P&L Turnover) vs GST Returns (GSTR-1 & 3B)
- Tax Payable vs Tax Paid rate-wise
- Books ITC vs GSTR-3B Claimed ITC vs GSTR-2A/2B Auto-drafted ITC
- Computes Unreconciled Differences & DRC-03 Additional Tax Liability
"""

from typing import Dict, Any, List, Optional


def compute_gstr9_reconciliation(
    audited_pnl_turnover: float,
    gstr1_annual_turnover: float,
    gstr3b_annual_turnover: float,
    books_tax_payable: Dict[str, float],
    gstr3b_tax_paid: Dict[str, float],
    books_itc: Dict[str, float],
    gstr3b_claimed_itc: Dict[str, float],
    gstr2b_annual_itc: Dict[str, float],
    exempt_non_gst_turnover: float = 0.0,
    advances_unadjusted: float = 0.0
) -> Dict[str, Any]:
    """
    Performs GSTR-9 / GSTR-9C Annual Audit Reconciliation.
    Identifies variance, statutory interest/penalties, and suggests DRC-03 tax payments.
    """
    # -------------------------------------------------------------
    # 1. Turnover Reconciliation (GSTR-9C Table 5)
    # -------------------------------------------------------------
    adjusted_audited_turnover = audited_pnl_turnover + advances_unadjusted - exempt_non_gst_turnover
    turnover_diff_gstr1 = round(audited_pnl_turnover - gstr1_annual_turnover, 2)
    turnover_diff_gstr3b = round(audited_pnl_turnover - gstr3b_annual_turnover, 2)
    gstr1_vs_gstr3b_diff = round(gstr1_annual_turnover - gstr3b_annual_turnover, 2)

    # -------------------------------------------------------------
    # 2. Tax Liability Reconciliation (GSTR-9C Table 9 & 11)
    # -------------------------------------------------------------
    unreconciled_tax = {}
    total_short_paid_tax = 0.0
    for tax_head in ["igst", "cgst", "sgst"]:
        b_tax = books_tax_payable.get(tax_head, 0.0)
        p_tax = gstr3b_tax_paid.get(tax_head, 0.0)
        diff = round(b_tax - p_tax, 2)
        unreconciled_tax[tax_head] = {
            "books_payable": b_tax,
            "gstr3b_paid": p_tax,
            "variance": diff,
            "status": "SHORT_PAID" if diff > 1.0 else ("EXCESS_PAID" if diff < -1.0 else "RECONCILED")
        }
        if diff > 1.0:
            total_short_paid_tax += diff

    # -------------------------------------------------------------
    # 3. ITC Reconciliation (GSTR-9 Table 8 & GSTR-9C Table 12)
    # -------------------------------------------------------------
    itc_reconciliation = {}
    total_excess_claimed_itc = 0.0
    for tax_head in ["igst", "cgst", "sgst"]:
        b_itc = books_itc.get(tax_head, 0.0)
        c_itc = gstr3b_claimed_itc.get(tax_head, 0.0)
        g2b_itc = gstr2b_annual_itc.get(tax_head, 0.0)
        
        diff_books_vs_3b = round(c_itc - b_itc, 2)
        diff_3b_vs_2b = round(c_itc - g2b_itc, 2)
        
        itc_reconciliation[tax_head] = {
            "books_itc": b_itc,
            "gstr3b_claimed": c_itc,
            "gstr2b_available": g2b_itc,
            "excess_claimed_vs_books": diff_books_vs_3b,
            "excess_claimed_vs_2b": diff_3b_vs_2b,
            "risk_flag": diff_3b_vs_2b > 5.0
        }
        if diff_3b_vs_2b > 5.0:
            total_excess_claimed_itc += diff_3b_vs_2b

    # Overall Audit Status
    has_unreconciled_liability = (total_short_paid_tax > 10.0 or total_excess_claimed_itc > 10.0)

    recommendations = []
    if abs(gstr1_vs_gstr3b_diff) > 100.0:
        recommendations.append(
            f"GSTR-1 turnover (₹{gstr1_annual_turnover:,.2f}) does not match GSTR-3B turnover (₹{gstr3b_annual_turnover:,.2f}). "
            f"Difference of ₹{abs(gstr1_vs_gstr3b_diff):,.2f} will trigger Rule 88C DRC-01B notice."
        )
    if total_short_paid_tax > 10.0:
        recommendations.append(
            f"Short paid tax of ₹{total_short_paid_tax:,.2f} detected. "
            f"Must be discharged voluntarily via Form DRC-03 with Section 50 interest to avoid penalty."
        )
    if total_excess_claimed_itc > 10.0:
        recommendations.append(
            f"ITC claimed in GSTR-3B exceeds GSTR-2B by ₹{total_excess_claimed_itc:,.2f}. "
            f"Inadmissible under Section 16(2)(aa). Reverse in Table 4(B) or pay through DRC-03."
        )

    return {
        "turnover_reconciliation": {
            "audited_pnl_turnover": audited_pnl_turnover,
            "gstr1_annual_turnover": gstr1_annual_turnover,
            "gstr3b_annual_turnover": gstr3b_annual_turnover,
            "unreconciled_pnl_vs_gstr1": turnover_diff_gstr1,
            "unreconciled_pnl_vs_gstr3b": turnover_diff_gstr3b,
            "gstr1_vs_gstr3b_diff": gstr1_vs_gstr3b_diff,
            "status": "MATCHED" if abs(turnover_diff_gstr3b) <= 5.0 else "UNRECONCILED"
        },
        "tax_liability_reconciliation": {
            "heads": unreconciled_tax,
            "total_short_paid_tax": round(total_short_paid_tax, 2)
        },
        "itc_reconciliation": {
            "heads": itc_reconciliation,
            "total_excess_claimed_itc": round(total_excess_claimed_itc, 2)
        },
        "audit_summary": {
            "clean_audit": not has_unreconciled_liability,
            "total_statutory_exposure": round(total_short_paid_tax + total_excess_claimed_itc, 2),
            "recommendations": recommendations
        }
    }

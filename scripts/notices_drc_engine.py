"""
GST Notices & DRC Engine.
Implements automated analysis, compliance checks, and reply drafts for:
- DRC-01B / Rule 88C: Intimation of difference in liability (GSTR-1 vs GSTR-3B)
- DRC-01C / Rule 88D: Intimation of difference in ITC (GSTR-2B vs GSTR-3B)
- Section 50 Statutory Interest Calculator (18% for delayed cash tax, 24% for utilized wrongful ITC)
- Form DRC-03 Voluntary Payment & Reply Drafting Engine
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date


def calculate_section_50_interest(
    tax_amount: float,
    due_date: str,
    payment_date: str,
    is_wrongly_utilized_itc: bool = False
) -> Dict[str, Any]:
    """
    Computes statutory interest under Section 50 of CGST Act.
    - Section 50(1): 18% p.a. on delayed net cash tax payment.
    - Section 50(3) read with Rule 88B: 24% p.a. on wrongly availed AND utilized ITC.
    """
    d_due = datetime.strptime(due_date, "%Y-%m-%d").date()
    d_pay = datetime.strptime(payment_date, "%Y-%m-%d").date()
    
    delay_days = max(0, (d_pay - d_due).days)
    rate = 24.0 if is_wrongly_utilized_itc else 18.0
    
    interest_amount = 0.0
    if delay_days > 0 and tax_amount > 0:
        interest_amount = round(tax_amount * (rate / 100.0) * (delay_days / 365.0), 2)
        
    return {
        "tax_amount": tax_amount,
        "due_date": due_date,
        "payment_date": payment_date,
        "delay_days": delay_days,
        "interest_rate_percent": rate,
        "interest_amount": interest_amount,
        "statutory_section": "Section 50(3) [24% p.a.]" if is_wrongly_utilized_itc else "Section 50(1) [18% p.a.]"
    }


def analyze_drc01b_rule_88c(
    gstr1_tax_liability: float,
    gstr3b_tax_liability: float,
    threshold_percent: float = 20.0,
    threshold_amount: float = 2500000.0
) -> Dict[str, Any]:
    """
    Evaluates risk of receiving DRC-01B notice under Rule 88C (GSTR-1 liability > GSTR-3B).
    Generates structured reply / reconciliation.
    """
    diff = round(gstr1_tax_liability - gstr3b_tax_liability, 2)
    percent_diff = round((diff / gstr3b_tax_liability * 100.0), 2) if gstr3b_tax_liability > 0 else 100.0
    
    triggers_notice = (diff > threshold_amount) or (percent_diff >= threshold_percent and diff > 5000.0)
    
    draft_explanation = None
    if triggers_notice:
        draft_explanation = (
            f"The differential liability of ₹{diff:,.2f} ({percent_diff}%) between GSTR-1 and GSTR-3B "
            f"exceeds the statutory scrutiny threshold. If a DRC-01B notice is issued, options include:\n"
            f"1. Discharge differential liability with applicable interest via Form DRC-03.\n"
            f"2. File Part B reply specifying one of the permissible grounds (e.g., typographical error in GSTR-1, "
            f"inadvertent duplicate reporting, or credit notes adjusted in GSTR-3B)."
        )
        
    return {
        "gstr1_liability": gstr1_tax_liability,
        "gstr3b_liability": gstr3b_tax_liability,
        "difference": diff,
        "percent_difference": percent_diff,
        "triggers_drc01b": triggers_notice,
        "risk_level": "HIGH (NOTICE RISK)" if triggers_notice else "NORMAL",
        "draft_response_guidance": draft_explanation
    }


def analyze_drc01c_rule_88d(
    gstr2b_itc: float,
    gstr3b_claimed_itc: float,
    threshold_percent: float = 20.0,
    threshold_amount: float = 2500000.0
) -> Dict[str, Any]:
    """
    Evaluates risk of receiving DRC-01C notice under Rule 88D (GSTR-3B claimed ITC > GSTR-2B).
    """
    diff = round(gstr3b_claimed_itc - gstr2b_itc, 2)
    percent_diff = round((diff / gstr2b_itc * 100.0), 2) if gstr2b_itc > 0 else 100.0
    
    triggers_notice = (diff > threshold_amount) or (percent_diff >= threshold_percent and diff > 5000.0)
    
    draft_explanation = None
    if triggers_notice:
        draft_explanation = (
            f"ITC claimed in GSTR-3B exceeds GSTR-2B by ₹{diff:,.2f} ({percent_diff}%). "
            f"As per Rule 88D, this triggers DRC-01C intimation. Permissible justifications include:\n"
            f"1. Inward supply received in prior tax period but accounted now (proviso to Sec 16(2)).\n"
            f"2. ITC of import of goods/services from SEZ not auto-populated in GSTR-2B.\n"
            f"3. Reverse charge ITC paid in cash in current tax period."
        )

    return {
        "gstr2b_itc": gstr2b_itc,
        "gstr3b_claimed_itc": gstr3b_claimed_itc,
        "excess_claimed": diff,
        "percent_difference": percent_diff,
        "triggers_drc01c": triggers_notice,
        "risk_level": "CRITICAL (INADMISSIBLE ITC RISK)" if triggers_notice else "NORMAL",
        "draft_response_guidance": draft_explanation
    }

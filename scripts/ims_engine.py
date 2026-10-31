"""
2026 Modern GST Statutory Engine:
- GSTN Invoice Management System (IMS) Workflow (Accept / Reject / Pending)
- Section 16(4) ITC Availment Cut-off Engine (30th November Statutory Deadline)
- Mandatory Input Service Distributor (ISD) Allocation Engine (Amended Section 20)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date


def check_section_16_4_time_limit(invoice_date_str: str, return_filing_date_str: str) -> Dict[str, Any]:
    """
    Checks Section 16(4) statutory time limit for claiming Input Tax Credit.
    Rule: ITC on an invoice of Financial Year (April - March) can only be claimed up to
    30th November of the following financial year, or date of filing Annual Return GSTR-9, whichever is earlier.
    """
    inv_date = datetime.strptime(invoice_date_str, "%Y-%m-%d").date()
    filing_date = datetime.strptime(return_filing_date_str, "%Y-%m-%d").date()
    
    # Determine Financial Year of invoice
    if inv_date.month >= 4:
        fy_start_year = inv_date.year
    else:
        fy_start_year = inv_date.year - 1
        
    fy_end_year = fy_start_year + 1
    # Statutory deadline is 30th November of subsequent financial year
    cutoff_date = date(fy_end_year, 11, 30)
    
    is_time_barred = filing_date > cutoff_date
    days_lapsed = (filing_date - cutoff_date).days if is_time_barred else 0

    return {
        "invoice_date": invoice_date_str,
        "return_filing_date": return_filing_date_str,
        "financial_year": f"FY {fy_start_year}-{str(fy_end_year)[-2:]}",
        "statutory_cutoff_date": cutoff_date.strftime("%Y-%m-%d"),
        "is_time_barred": is_time_barred,
        "status": "TIME_BARRED_INADMISSIBLE" if is_time_barred else "VALID_WITHIN_TIME_LIMIT",
        "days_exceeded": days_lapsed,
        "statutory_note": (
            f"Under Section 16(4), ITC for {fy_start_year}-{str(fy_end_year)[-2:]} expired on 30-Nov-{fy_end_year}. "
            f"Filing on {return_filing_date_str} is barred by {days_lapsed} days."
            if is_time_barred else "Eligible for ITC claim within statutory deadline."
        )
    }


def process_ims_actions(
    ims_actions: List[Dict[str, Any]],
    current_period: str
) -> Dict[str, Any]:
    """
    Simulates the GSTN Invoice Management System (IMS).
    Recipients take 1 of 3 statutory actions on inward supplies before 2B generation:
    1. ACCEPT: Flows directly into GSTR-2B as eligible ITC.
    2. REJECT: Dropped from GSTR-2B; no ITC flow; supplier notified for amendment in GSTR-1A.
    3. PENDING: Retained in IMS buffer for future tax period (e.g. goods in transit under Sec 16(2)(b)).
    """
    accepted = []
    rejected = []
    pending = []
    
    accepted_itc = {"igst": 0.0, "cgst": 0.0, "sgst": 0.0}
    pending_itc = {"igst": 0.0, "cgst": 0.0, "sgst": 0.0}
    rejected_itc = {"igst": 0.0, "cgst": 0.0, "sgst": 0.0}

    for action in ims_actions:
        inv_no = action.get("invoice_number", "")
        action_type = str(action.get("action", "ACCEPT")).upper().strip()
        cgst = float(action.get("cgst", 0.0))
        sgst = float(action.get("sgst", 0.0))
        igst = float(action.get("igst", 0.0))
        
        entry = {
            "invoice_number": inv_no,
            "supplier_gstin": action.get("supplier_gstin"),
            "invoice_total": float(action.get("invoice_total", 0.0)),
            "cgst": cgst,
            "sgst": sgst,
            "igst": igst,
            "reason": action.get("reason", "")
        }

        if action_type == "ACCEPT":
            accepted.append(entry)
            accepted_itc["igst"] += igst
            accepted_itc["cgst"] += cgst
            accepted_itc["sgst"] += sgst
        elif action_type == "REJECT":
            rejected.append(entry)
            rejected_itc["igst"] += igst
            rejected_itc["cgst"] += cgst
            rejected_itc["sgst"] += sgst
        elif action_type == "PENDING":
            pending.append(entry)
            pending_itc["igst"] += igst
            pending_itc["cgst"] += cgst
            pending_itc["sgst"] += sgst

    return {
        "ims_period": current_period,
        "summary": {
            "total_invoices_reviewed": len(ims_actions),
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "pending_count": len(pending),
            "eligible_itc_routed_to_gstr2b": accepted_itc,
            "itc_held_in_ims_buffer": pending_itc,
            "disallowed_rejected_itc": rejected_itc
        },
        "accepted_invoices": accepted,
        "rejected_invoices": rejected,
        "pending_invoices": pending
    }


def compute_isd_distribution(
    head_office_gstin: str,
    common_service_itc: Dict[str, float],
    recipient_branches: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Computes Input Service Distributor (ISD) credit distribution under amended Section 20.
    Distributes common input service ITC amongst recipient units based on their turnover ratio.
    """
    total_branch_turnover = sum(float(b.get("turnover", 0.0)) for b in recipient_branches)
    if total_branch_turnover <= 0:
        raise ValueError("Total branch turnover must be greater than zero for ISD distribution.")
        
    ho_state = head_office_gstin[:2]
    allocations = []
    
    for b in recipient_branches:
        b_gstin = b.get("branch_gstin", "").strip().upper()
        b_state = b_gstin[:2]
        b_turnover = float(b.get("turnover", 0.0))
        ratio = b_turnover / total_branch_turnover
        
        is_same_state = (ho_state == b_state)
        # If recipient is in different state, CGST+SGST converts to IGST
        allocated_igst = round(common_service_itc.get("igst", 0.0) * ratio, 2)
        
        if is_same_state:
            allocated_cgst = round(common_service_itc.get("cgst", 0.0) * ratio, 2)
            allocated_sgst = round(common_service_itc.get("sgst", 0.0) * ratio, 2)
        else:
            # Cross-state conversion to IGST under Section 20(2)
            allocated_cgst = 0.0
            allocated_sgst = 0.0
            allocated_igst += round((common_service_itc.get("cgst", 0.0) + common_service_itc.get("sgst", 0.0)) * ratio, 2)
            
        allocations.append({
            "branch_gstin": b_gstin,
            "turnover": b_turnover,
            "turnover_share_percent": round(ratio * 100, 2),
            "distributed_itc": {
                "igst": allocated_igst,
                "cgst": allocated_cgst,
                "sgst": allocated_sgst,
                "total": round(allocated_igst + allocated_cgst + allocated_sgst, 2)
            }
        })

    return {
        "form": "GSTR-6 (ISD)",
        "isd_head_office_gstin": head_office_gstin,
        "total_common_itc": common_service_itc,
        "total_recipient_branches": len(recipient_branches),
        "branch_allocations": allocations
    }

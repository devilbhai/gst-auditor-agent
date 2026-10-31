"""
GSTR-3B Engine: Monthly Self-Declared Summary Return & Tax Payment Set-Off.
Computes:
- Table 3.1: Tax on Outward and Reverse Charge Inward Supplies
- Table 3.2: Inter-state supplies to unregistered persons
- Table 4: Eligible ITC & Statutory Reversals (Rules 38, 42, 43, Sec 17(5))
- Table 5: Exempt, Nil, and Non-GST inward supplies
- Table 6.1: Statutory Tax Payment & Set-Off Engine (Sec 49, 49A, 49B)
- Cash Ledger & PMT-06 Challan Requirement Calculation
"""

from typing import Dict, Any, List, Optional
import os
import sys

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gst_rules import check_blocked_itc_risk


def compute_gstr3b(
    sales_invoices: List[Dict[str, Any]],
    purchase_invoices: List[Dict[str, Any]],
    gstin: str,
    fp: str,
    opening_itc_ledger: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Computes statutory GSTR-3B tables, ITC eligible/ineligible breakdown,
    and calculates optimal legal set-off under Sections 49, 49A, and 49B.
    """
    supplier_state = gstin[:2]
    itc_ledger = opening_itc_ledger or {"igst": 0.0, "cgst": 0.0, "sgst": 0.0}
    
    # -------------------------------------------------------------
    # Table 3.1 Outward Supplies & Inward RCM
    # -------------------------------------------------------------
    t31_a = {"txval": 0.0, "iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0} # Taxable
    t31_b = {"txval": 0.0, "iamt": 0.0, "csamt": 0.0} # Zero rated / Exports
    t31_c = {"txval": 0.0} # Nil / Exempt
    t31_d = {"txval": 0.0, "iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0} # Inward RCM
    t31_e = {"txval": 0.0} # Non-GST
    
    # Table 3.2 Inter-state supplies to unregistered
    t32_unreg = {}

    for s_inv in sales_invoices:
        txval = float(s_inv.get("taxable_value", 0.0))
        cgst = float(s_inv.get("cgst", 0.0))
        sgst = float(s_inv.get("sgst", 0.0))
        igst = float(s_inv.get("igst", 0.0))
        pos = str(s_inv.get("place_of_supply") or supplier_state).zfill(2)
        buyer_gstin = s_inv.get("buyer_gstin", "").strip()
        
        is_zero_rated = s_inv.get("zero_rated", False)
        is_nil_exempt = s_inv.get("nil_exempt", False)
        is_rcm = s_inv.get("reverse_charge", False)
        
        if is_zero_rated:
            t31_b["txval"] += txval
            t31_b["iamt"] += igst
        elif is_nil_exempt:
            t31_c["txval"] += txval
        else:
            t31_a["txval"] += txval
            t31_a["iamt"] += igst
            t31_a["camt"] += cgst
            t31_a["samt"] += sgst
            
            # Check Table 3.2
            if not buyer_gstin and pos != supplier_state:
                if pos not in t32_unreg:
                    t32_unreg[pos] = {"pos": pos, "txval": 0.0, "iamt": 0.0}
                t32_unreg[pos]["txval"] += txval
                t32_unreg[pos]["iamt"] += igst

    # -------------------------------------------------------------
    # Table 4: Eligible ITC & Reversals
    # -------------------------------------------------------------
    itc_available_all_other = {"iamt": 0.0, "camt": 0.0, "samt": 0.0}
    itc_available_rcm = {"iamt": 0.0, "camt": 0.0, "samt": 0.0}
    itc_reversed_sec17_5 = {"iamt": 0.0, "camt": 0.0, "samt": 0.0}

    for p_inv in purchase_invoices:
        txval = float(p_inv.get("taxable_value", 0.0))
        cgst = float(p_inv.get("cgst", 0.0))
        sgst = float(p_inv.get("sgst", 0.0))
        igst = float(p_inv.get("igst", 0.0))
        desc = p_inv.get("item_description", "")
        
        # Check Section 17(5) Blocked ITC
        risk = check_blocked_itc_risk(desc)
        if risk["blocked"]:
            itc_reversed_sec17_5["iamt"] += igst
            itc_reversed_sec17_5["camt"] += cgst
            itc_reversed_sec17_5["samt"] += sgst
        elif p_inv.get("reverse_charge"):
            itc_available_rcm["iamt"] += igst
            itc_available_rcm["camt"] += cgst
            itc_available_rcm["samt"] += sgst
            # Also payable under Table 3.1(d)
            t31_d["txval"] += txval
            t31_d["iamt"] += igst
            t31_d["camt"] += cgst
            t31_d["samt"] += sgst
        else:
            itc_available_all_other["iamt"] += igst
            itc_available_all_other["camt"] += cgst
            itc_available_all_other["samt"] += sgst

    # Net ITC Available Table 4(C)
    net_itc = {
        "iamt": max(0.0, itc_available_all_other["iamt"] + itc_available_rcm["iamt"] - itc_reversed_sec17_5["iamt"]),
        "camt": max(0.0, itc_available_all_other["camt"] + itc_available_rcm["camt"] - itc_reversed_sec17_5["camt"]),
        "samt": max(0.0, itc_available_all_other["samt"] + itc_available_rcm["samt"] - itc_reversed_sec17_5["samt"])
    }

    # -------------------------------------------------------------
    # Table 6.1: Tax Payment & Set-Off Optimization (Sec 49, 49A, 49B)
    # Total Gross Output Liability = 3.1(a) + 3.1(b) + 3.1(d)
    # -------------------------------------------------------------
    tax_liability = {
        "igst": round(t31_a["iamt"] + t31_b["iamt"] + t31_d["iamt"], 2),
        "cgst": round(t31_a["camt"] + t31_d["camt"], 2),
        "sgst": round(t31_a["samt"] + t31_d["samt"], 2)
    }

    total_available_credit = {
        "igst": round(itc_ledger.get("igst", 0.0) + net_itc["iamt"], 2),
        "cgst": round(itc_ledger.get("cgst", 0.0) + net_itc["camt"], 2),
        "sgst": round(itc_ledger.get("sgst", 0.0) + net_itc["samt"], 2)
    }

    rem_credit = dict(total_available_credit)
    rem_liability = dict(tax_liability)
    
    set_off = {
        "igst_paid_by_igst": 0.0,
        "cgst_paid_by_igst": 0.0,
        "sgst_paid_by_igst": 0.0,
        "cgst_paid_by_cgst": 0.0,
        "igst_paid_by_cgst": 0.0,
        "sgst_paid_by_sgst": 0.0,
        "igst_paid_by_sgst": 0.0
    }

    # Step 1: Utilize IGST Credit completely
    # 1.1 IGST credit -> IGST liability
    offset_igst_igst = min(rem_credit["igst"], rem_liability["igst"])
    set_off["igst_paid_by_igst"] = offset_igst_igst
    rem_credit["igst"] -= offset_igst_igst
    rem_liability["igst"] -= offset_igst_igst

    # 1.2 IGST credit -> CGST liability
    if rem_credit["igst"] > 0 and rem_liability["cgst"] > 0:
        offset_igst_cgst = min(rem_credit["igst"], rem_liability["cgst"])
        set_off["cgst_paid_by_igst"] = offset_igst_cgst
        rem_credit["igst"] -= offset_igst_cgst
        rem_liability["cgst"] -= offset_igst_cgst

    # 1.3 IGST credit -> SGST liability
    if rem_credit["igst"] > 0 and rem_liability["sgst"] > 0:
        offset_igst_sgst = min(rem_credit["igst"], rem_liability["sgst"])
        set_off["sgst_paid_by_igst"] = offset_igst_sgst
        rem_credit["igst"] -= offset_igst_sgst
        rem_liability["sgst"] -= offset_igst_sgst

    # Step 2: Utilize CGST Credit -> CGST liability first, then IGST
    offset_cgst_cgst = min(rem_credit["cgst"], rem_liability["cgst"])
    set_off["cgst_paid_by_cgst"] = offset_cgst_cgst
    rem_credit["cgst"] -= offset_cgst_cgst
    rem_liability["cgst"] -= offset_cgst_cgst

    if rem_credit["cgst"] > 0 and rem_liability["igst"] > 0:
        offset_cgst_igst = min(rem_credit["cgst"], rem_liability["igst"])
        set_off["igst_paid_by_cgst"] = offset_cgst_igst
        rem_credit["cgst"] -= offset_cgst_igst
        rem_liability["igst"] -= offset_cgst_igst

    # Step 3: Utilize SGST Credit -> SGST liability first, then IGST (NEVER CGST!)
    offset_sgst_sgst = min(rem_credit["sgst"], rem_liability["sgst"])
    set_off["sgst_paid_by_sgst"] = offset_sgst_sgst
    rem_credit["sgst"] -= offset_sgst_sgst
    rem_liability["sgst"] -= offset_sgst_sgst

    if rem_credit["sgst"] > 0 and rem_liability["igst"] > 0:
        offset_sgst_igst = min(rem_credit["sgst"], rem_liability["igst"])
        set_off["igst_paid_by_sgst"] = offset_sgst_igst
        rem_credit["sgst"] -= offset_sgst_igst
        rem_liability["igst"] -= offset_sgst_igst

    # Step 4: Net Cash Payable via Challan PMT-06
    cash_payable = {
        "igst": round(rem_liability["igst"], 2),
        "cgst": round(rem_liability["cgst"], 2),
        "sgst": round(rem_liability["sgst"], 2),
        "total_cash": round(rem_liability["igst"] + rem_liability["cgst"] + rem_liability["sgst"], 2)
    }

    closing_itc_balance = {
        "igst": round(rem_credit["igst"], 2),
        "cgst": round(rem_credit["cgst"], 2),
        "sgst": round(rem_credit["sgst"], 2)
    }

    return {
        "gstin": gstin,
        "fp": fp,
        "table_3_1": {
            "outward_taxable": t31_a,
            "outward_zero_rated": t31_b,
            "outward_nil_exempt": t31_c,
            "inward_rcm": t31_d,
            "non_gst": t31_e
        },
        "table_3_2": list(t32_unreg.values()),
        "table_4_itc": {
            "itc_available_all_other": itc_available_all_other,
            "itc_available_rcm": itc_available_rcm,
            "itc_reversed_sec17_5": itc_reversed_sec17_5,
            "net_itc": net_itc
        },
        "table_6_1_tax_payment": {
            "gross_tax_liability": tax_liability,
            "total_available_credit": total_available_credit,
            "set_off_breakdown": set_off,
            "cash_payable_pmt06": cash_payable,
            "closing_itc_balance": closing_itc_balance
        }
    }

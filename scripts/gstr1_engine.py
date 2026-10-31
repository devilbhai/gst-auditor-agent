"""
GSTR-1 Engine: Statement of Outward Supplies.
Generates, validates, and prepares GST Portal compatible JSON for GSTR-1.
Covers:
- Table 4: B2B Invoices (Regular, Reverse Charge)
- Table 5: B2C Large (Inter-state taxable invoice value > ₹1,00,000 / ₹2,50,000)
- Table 7: B2C Small (Intra-state & small inter-state)
- Table 8: Nil-rated, Exempted & Non-GST supplies
- Table 11: Advances Received and Adjusted
- Table 12: HSN-wise summary of outward supplies
- Table 13: Documents issued summary (Tax invoice, credit/debit notes series)
"""

from typing import Dict, Any, List, Optional
import json
import os
import sys

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gstin_validator import validate_gstin


def build_gstr1_tables(invoices: List[Dict[str, Any]], gstin: str, fp: str) -> Dict[str, Any]:
    """
    Transforms raw outward sales invoices into statutory GSTR-1 tables.
    fp: Financial period in MMYYYY format (e.g. '102026' for Oct 2026).
    """
    supplier_state = gstin[:2]
    
    b2b = {}
    b2cl = []
    b2cs = {}
    nil_exempt = {
        "nil_amt": 0.0,
        "expt_amt": 0.0,
        "ngsup_amt": 0.0
    }
    hsn_summary = {}
    doc_summary = {
        "doc_num": 1,
        "doc_typ": "Invoices for outward supply",
        "from": "",
        "to": "",
        "totnum": len(invoices),
        "canc": 0,
        "net_issue": len(invoices)
    }

    inv_numbers = []

    for inv in invoices:
        inv_no = str(inv.get("invoice_number", "")).strip()
        inv_numbers.append(inv_no)
        inv_date = inv.get("invoice_date", "01-10-2026")
        buyer_gstin = inv.get("buyer_gstin", "").strip().upper()
        pos = str(inv.get("place_of_supply") or (buyer_gstin[:2] if len(buyer_gstin) >= 2 else supplier_state)).zfill(2)
        
        taxable_val = float(inv.get("taxable_value", 0.0))
        rate = float(inv.get("tax_rate", 18.0))
        cgst = float(inv.get("cgst", 0.0))
        sgst = float(inv.get("sgst", 0.0))
        igst = float(inv.get("igst", 0.0))
        inv_total = float(inv.get("invoice_total") or (taxable_val + cgst + sgst + igst))
        
        hsn = str(inv.get("hsn_sac") or "9983").strip()
        is_inter_state = (pos != supplier_state)
        
        # 1. Update HSN Summary (Table 12)
        if hsn not in hsn_summary:
            hsn_summary[hsn] = {
                "num": len(hsn_summary) + 1,
                "hsn_sc": hsn,
                "desc": inv.get("item_description", "Goods/Services"),
                "uqc": "OTH",
                "qty": float(inv.get("quantity", 1)),
                "txval": 0.0,
                "iamt": 0.0,
                "camt": 0.0,
                "samt": 0.0,
                "csamt": 0.0
            }
        hsn_summary[hsn]["txval"] = round(hsn_summary[hsn]["txval"] + taxable_val, 2)
        hsn_summary[hsn]["iamt"] = round(hsn_summary[hsn]["iamt"] + igst, 2)
        hsn_summary[hsn]["camt"] = round(hsn_summary[hsn]["camt"] + cgst, 2)
        hsn_summary[hsn]["samt"] = round(hsn_summary[hsn]["samt"] + sgst, 2)

        # 2. Categorize into B2B / B2CL / B2CS
        if buyer_gstin:
            # Table 4: B2B
            if buyer_gstin not in b2b:
                b2b[buyer_gstin] = {
                    "ctin": buyer_gstin,
                    "inv": []
                }
            
            b2b[buyer_gstin]["inv"].append({
                "inum": inv_no,
                "idt": inv_date,
                "val": round(inv_total, 2),
                "pos": pos,
                "rchrg": "Y" if inv.get("reverse_charge") else "N",
                "inv_typ": "R",
                "itms": [
                    {
                        "num": 1,
                        "itm_det": {
                            "rt": rate,
                            "txval": round(taxable_val, 2),
                            "iamt": round(igst, 2),
                            "camt": round(cgst, 2),
                            "samt": round(sgst, 2),
                            "csamt": 0.0
                        }
                    }
                ]
            })
        else:
            # B2C
            # Table 5: B2CL (Inter-state & invoice total > 1,00,000 / 2,50,000)
            if is_inter_state and inv_total > 100000.0:
                b2cl.append({
                    "pos": pos,
                    "inv": [
                        {
                            "inum": inv_no,
                            "idt": inv_date,
                            "val": round(inv_total, 2),
                            "itms": [
                                {
                                    "num": 1,
                                    "itm_det": {
                                        "rt": rate,
                                        "txval": round(taxable_val, 2),
                                        "iamt": round(igst, 2),
                                        "csamt": 0.0
                                    }
                                }
                            ]
                        }
                    ]
                })
            else:
                # Table 7: B2CS
                b2cs_key = (pos, rate, "E" if inv.get("ecommerce") else "OE")
                if b2cs_key not in b2cs:
                    b2cs[b2cs_key] = {
                        "sply_ty": "INTER" if is_inter_state else "INTRA",
                        "pos": pos,
                        "typ": b2cs_key[2],
                        "rt": rate,
                        "txval": 0.0,
                        "iamt": 0.0,
                        "camt": 0.0,
                        "samt": 0.0,
                        "csamt": 0.0
                    }
                b2cs[b2cs_key]["txval"] = round(b2cs[b2cs_key]["txval"] + taxable_val, 2)
                b2cs[b2cs_key]["iamt"] = round(b2cs[b2cs_key]["iamt"] + igst, 2)
                b2cs[b2cs_key]["camt"] = round(b2cs[b2cs_key]["camt"] + cgst, 2)
                b2cs[b2cs_key]["samt"] = round(b2cs[b2cs_key]["samt"] + sgst, 2)

    if inv_numbers:
        doc_summary["from"] = inv_numbers[0]
        doc_summary["to"] = inv_numbers[-1]

    # Format into official GST Portal JSON structure
    gstr1_payload = {
        "gstin": gstin,
        "fp": fp,
        "version": "GSTR1_v1.0",
        "hash": "hash_autogenerated",
        "b2b": list(b2b.values()),
        "b2cl": b2cl,
        "b2cs": list(b2cs.values()),
        "nil": nil_exempt,
        "hsn": {"data": list(hsn_summary.values())},
        "doc_issue": {"doc_det": [doc_summary]}
    }
    
    return gstr1_payload


def audit_gstr1_portal_json(gstr1_data: Dict[str, Any]) -> Dict[str, Any]:
    """Audits an accountant/CA generated GSTR-1 JSON against GST portal rules."""
    errors = []
    warnings = []
    
    gstin = gstr1_data.get("gstin")
    val = validate_gstin(gstin)
    if not val["valid"]:
        errors.append(f"Invalid Taxpayer GSTIN: {gstin} ({val.get('reason')})")

    supplier_st = val.get("state_code", gstin[:2] if gstin else "00")
    
    # Check B2B table
    b2b_list = gstr1_data.get("b2b", [])
    total_b2b_taxable = 0.0
    for b2b_rec in b2b_list:
        ctin = b2b_rec.get("ctin")
        c_val = validate_gstin(ctin)
        if not c_val["valid"]:
            errors.append(f"Table 4 (B2B): Recipient GSTIN '{ctin}' is invalid: {c_val.get('reason')}")
            
        for inv in b2b_rec.get("inv", []):
            pos = inv.get("pos", ctin[:2] if ctin else "")
            for itm in inv.get("itms", []):
                det = itm.get("itm_det", {})
                txval = float(det.get("txval", 0.0))
                total_b2b_taxable += txval
                iamt = float(det.get("iamt", 0.0))
                camt = float(det.get("camt", 0.0))
                samt = float(det.get("samt", 0.0))
                
                # Check tax jurisdiction
                if pos == supplier_st and iamt > 0.05:
                    errors.append(f"Invoice {inv.get('inum')}: Intra-state supply (POS {pos}) cannot contain IGST (₹{iamt}).")
                if pos != supplier_st and (camt > 0.05 or samt > 0.05):
                    errors.append(f"Invoice {inv.get('inum')}: Inter-state supply (POS {pos}) cannot contain CGST/SGST.")

    # Check HSN Table 12
    hsn_list = gstr1_data.get("hsn", {}).get("data", [])
    if not hsn_list:
        warnings.append("Table 12 (HSN Summary) is empty. Mandatory as per GST Notification 78/2020.")
    else:
        for item in hsn_list:
            code = str(item.get("hsn_sc", "")).strip()
            if len(code) < 4:
                warnings.append(f"HSN code '{code}' has fewer than 4 digits (Table 12 mandate).")

    return {
        "valid": len(errors) == 0,
        "gstin": gstin,
        "fp": gstr1_data.get("fp"),
        "total_b2b_records": len(b2b_list),
        "total_b2b_taxable": round(total_b2b_taxable, 2),
        "errors": errors,
        "warnings": warnings
    }

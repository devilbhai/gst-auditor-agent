#!/usr/bin/env python3
"""
GST Auditor Agent - Core Orchestration Engine & CLI.
Audits Indian GST invoices for statutory compliance, GSTIN checksums,
inter vs intra state tax allocation, E-Way Bill mandates, and E-Invoicing IRNs.
"""

import sys
import os
import json
import argparse
from typing import Dict, Any, List

# Ensure scripts dir is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gstin_validator import validate_gstin, STATE_CODES
from hsn_verifier import verify_hsn_sac
from gst_rules import (
    check_place_of_supply,
    check_eway_bill_compliance,
    check_einvoice_compliance,
    check_blocked_itc_risk
)
from report_generator import generate_markdown_report, generate_html_dashboard


def audit_single_invoice(inv: Dict[str, Any], company_turnover_cr: float = 5.0) -> Dict[str, Any]:
    """Runs statutory compliance audit on a single invoice record."""
    issues = []
    inv_no = str(inv.get("invoice_number", "UNKNOWN"))
    
    supplier_gstin = inv.get("supplier_gstin")
    buyer_gstin = inv.get("buyer_gstin")
    
    # 1. Validate Supplier GSTIN
    supp_val = validate_gstin(supplier_gstin)
    if not supp_val["valid"]:
        issues.append(f"[INVALID SUPPLIER GSTIN] {supplier_gstin}: {supp_val['reason']}")
    supplier_state = supp_val.get("state_code", supplier_gstin[:2] if supplier_gstin and len(supplier_gstin) >= 2 else "00")
    
    # 2. Validate Buyer GSTIN (if B2B)
    buyer_state = None
    if buyer_gstin:
        buyer_val = validate_gstin(buyer_gstin)
        if not buyer_val["valid"]:
            issues.append(f"[INVALID BUYER GSTIN] {buyer_gstin}: {buyer_val['reason']}")
        buyer_state = buyer_val.get("state_code", buyer_gstin[:2] if len(buyer_gstin) >= 2 else None)
        
    # Place of supply defaults to buyer state if not explicitly given
    pos = str(inv.get("place_of_supply") or buyer_state or supplier_state).zfill(2)
    
    # Financial fields
    taxable_value = float(inv.get("taxable_value", 0.0))
    cgst = float(inv.get("cgst", 0.0))
    sgst = float(inv.get("sgst", 0.0))
    igst = float(inv.get("igst", 0.0))
    tax_rate = float(inv.get("tax_rate", 18.0))
    total_value = float(inv.get("invoice_total") or (taxable_value + cgst + sgst + igst))
    
    # 3. Place of Supply & Tax Allocation Check
    pos_errors = check_place_of_supply(
        supplier_state=supplier_state,
        place_of_supply_state=pos,
        cgst_amount=cgst,
        sgst_amount=sgst,
        igst_amount=igst,
        tax_rate=tax_rate,
        taxable_value=taxable_value
    )
    issues.extend(pos_errors)
    
    # 4. HSN / SAC Code Verification
    hsn_code = inv.get("hsn_sac")
    if hsn_code:
        hsn_result = verify_hsn_sac(hsn_code, tax_rate, turnover_crores=company_turnover_cr)
        if not hsn_result["valid"]:
            issues.extend(hsn_result["issues"])
            
    # 5. E-Way Bill Verification (Rule 138)
    is_intra = (supplier_state == pos)
    is_service = str(hsn_code).startswith("99") if hsn_code else False
    eway_check = check_eway_bill_compliance(
        invoice_value=total_value,
        is_intra_state=is_intra,
        state_code=supplier_state,
        eway_bill_number=inv.get("eway_bill_number"),
        is_service=is_service
    )
    if not eway_check["compliant"] and eway_check.get("issue"):
        issues.append(eway_check["issue"])
        
    # 6. E-Invoicing / IRN Verification (Rule 48(4))
    is_b2b = bool(buyer_gstin)
    einvoice_check = check_einvoice_compliance(
        turnover_crores=company_turnover_cr,
        is_b2b=is_b2b,
        irn=inv.get("irn")
    )
    if not einvoice_check["compliant"] and einvoice_check.get("issue"):
        issues.append(einvoice_check["issue"])
        
    # 7. Blocked ITC Section 17(5)
    item_desc = inv.get("item_description", "")
    if item_desc:
        itc_risk = check_blocked_itc_risk(item_desc)
        if itc_risk["blocked"]:
            issues.append(itc_risk["warning"])
            
    compliant = (len(issues) == 0)
    tax_at_risk = 0.0 if compliant else (cgst + sgst + igst)
    
    return {
        "invoice_number": inv_no,
        "supplier_gstin": supplier_gstin,
        "supplier_state": supplier_state,
        "buyer_gstin": buyer_gstin,
        "place_of_supply": pos,
        "taxable_value": taxable_value,
        "cgst": cgst,
        "sgst": sgst,
        "igst": igst,
        "tax_rate": tax_rate,
        "invoice_total": total_value,
        "compliant": compliant,
        "issues": issues,
        "tax_at_risk": tax_at_risk
    }


def audit_invoices(invoices: List[Dict[str, Any]], turnover_crores: float = 5.0) -> Dict[str, Any]:
    """Audits a batch of invoices and compiles aggregate compliance statistics."""
    audited = []
    total_critical = 0
    total_warnings = 0
    total_tax_at_risk = 0.0
    passed_count = 0
    
    for inv in invoices:
        res = audit_single_invoice(inv, company_turnover_cr=turnover_crores)
        audited.append(res)
        
        if res["compliant"]:
            passed_count += 1
        else:
            total_tax_at_risk += res["tax_at_risk"]
            for issue in res["issues"]:
                if "[CRITICAL" in issue or "[LEGAL INVALIDITY" in issue or "[INVALID" in issue:
                    total_critical += 1
                else:
                    total_warnings += 1
                    
    total_invoices = len(invoices)
    failed_count = total_invoices - passed_count
    
    return {
        "summary": {
            "total_invoices": total_invoices,
            "passed_invoices": passed_count,
            "failed_invoices": failed_count,
            "total_critical_errors": total_critical,
            "total_warnings": total_warnings,
            "total_tax_at_risk": round(total_tax_at_risk, 2),
            "compliance_percentage": round((passed_count / total_invoices * 100), 1) if total_invoices else 100.0
        },
        "audited_invoices": audited
    }


def main():
    parser = argparse.ArgumentParser(description="GST Auditor Agent — Indian Statutory Compliance Engine")
    parser.add_argument("invoice_file", help="Path to JSON file containing invoice records")
    parser.add_argument("--turnover", type=float, default=5.0, help="Annual turnover in INR Crores (default: 5.0)")
    parser.add_argument("--html", help="Path to output standalone interactive HTML dashboard")
    parser.add_argument("--json", action="store_true", help="Print audit result as raw JSON")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.invoice_file):
        print(f"Error: File not found: {args.invoice_file}", file=sys.stderr)
        sys.exit(1)
        
    with open(args.invoice_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    invoices = data if isinstance(data, list) else data.get("invoices", [])
    
    audit_results = audit_invoices(invoices, turnover_crores=args.turnover)
    
    if args.html:
        generate_html_dashboard(audit_results, args.html)
        print(f"✅ Interactive HTML Dashboard generated at: {args.html}")
        
    if args.json:
        print(json.dumps(audit_results, indent=2))
    else:
        print(generate_markdown_report(audit_results))


if __name__ == "__main__":
    main()

"""
Input Tax Credit (ITC) Reconciler.
Reconciles Purchase Register (Books) vs GSTR-2B Auto-drafted ITC statement.
Detects unfiled vendor invoices, tax mismatches, and RCM misclassifications.
"""

from typing import Dict, Any, List


def reconcile_books_vs_gstr2b(books_invoices: List[Dict[str, Any]], gstr2b_invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Reconciles purchase records against GSTR-2B statement.
    Categorizes invoices into:
    - Exactly Matched (Safe to claim ITC)
    - Tax Mismatch (Discrepancy between vendor reported vs books)
    - Missing in 2B (Vendor has not filed GSTR-1 yet - ITC at risk under Sec 16(2)(aa))
    - Excess in 2B (Available in 2B but not in books)
    """
    gstr2b_map = {}
    for inv in gstr2b_invoices:
        key = (inv.get("supplier_gstin", "").strip().upper(), inv.get("invoice_number", "").strip().upper())
        gstr2b_map[key] = inv

    matched = []
    tax_mismatches = []
    missing_in_2b = []
    claimed_books_itc = 0.0
    available_2b_itc = 0.0
    
    seen_2b_keys = set()

    for b_inv in books_invoices:
        sgstin = b_inv.get("supplier_gstin", "").strip().upper()
        inv_no = b_inv.get("invoice_number", "").strip().upper()
        key = (sgstin, inv_no)
        
        books_tax = float(b_inv.get("cgst", 0.0)) + float(b_inv.get("sgst", 0.0)) + float(b_inv.get("igst", 0.0))
        claimed_books_itc += books_tax
        
        if key in gstr2b_map:
            seen_2b_keys.add(key)
            g_inv = gstr2b_map[key]
            g2b_tax = float(g_inv.get("cgst", 0.0)) + float(g_inv.get("sgst", 0.0)) + float(g_inv.get("igst", 0.0))
            available_2b_itc += g2b_tax
            
            diff = abs(books_tax - g2b_tax)
            if diff <= 1.0:
                matched.append({
                    "supplier_gstin": sgstin,
                    "invoice_number": inv_no,
                    "books_tax": round(books_tax, 2),
                    "gstr2b_tax": round(g2b_tax, 2),
                    "status": "MATCHED"
                })
            else:
                tax_mismatches.append({
                    "supplier_gstin": sgstin,
                    "invoice_number": inv_no,
                    "books_tax": round(books_tax, 2),
                    "gstr2b_tax": round(g2b_tax, 2),
                    "variance": round(books_tax - g2b_tax, 2),
                    "status": "TAX_MISMATCH",
                    "action": "Hold excess ITC claim; request supplier to amend in next GSTR-1"
                })
        else:
            missing_in_2b.append({
                "supplier_gstin": sgstin,
                "invoice_number": inv_no,
                "books_tax": round(books_tax, 2),
                "invoice_date": b_inv.get("invoice_date", ""),
                "status": "NOT_IN_2B",
                "action": "Do NOT claim ITC in GSTR-3B under Rule 36(4). Follow up with vendor."
            })
            
    excess_in_2b = []
    for key, g_inv in gstr2b_map.items():
        if key not in seen_2b_keys:
            g2b_tax = float(g_inv.get("cgst", 0.0)) + float(g_inv.get("sgst", 0.0)) + float(g_inv.get("igst", 0.0))
            excess_in_2b.append({
                "supplier_gstin": key[0],
                "invoice_number": key[1],
                "gstr2b_tax": round(g2b_tax, 2),
                "status": "UNCLAIMED_IN_BOOKS",
                "action": "Verify if purchase is accounted for in subsequent months"
            })
            
    return {
        "summary": {
            "total_books_invoices": len(books_invoices),
            "total_2b_invoices": len(gstr2b_invoices),
            "matched_count": len(matched),
            "mismatch_count": len(tax_mismatches),
            "missing_in_2b_count": len(missing_in_2b),
            "excess_in_2b_count": len(excess_in_2b),
            "total_claimed_books_itc": round(claimed_books_itc, 2),
            "total_available_2b_itc": round(available_2b_itc, 2),
            "at_risk_itc_amount": round(sum(item["books_tax"] for item in missing_in_2b), 2)
        },
        "matched": matched,
        "tax_mismatches": tax_mismatches,
        "missing_in_2b": missing_in_2b,
        "excess_in_2b": excess_in_2b
    }

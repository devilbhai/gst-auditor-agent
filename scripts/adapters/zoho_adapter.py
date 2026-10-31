"""
Zoho Books Adapter.
Parses Zoho Books Invoice / Bill CSV and JSON exports.
"""

import csv
import io
import json
from typing import List, Dict, Any


def parse_zoho_csv(csv_text: str) -> List[Dict[str, Any]]:
    """Parses Zoho Books standard invoice CSV export."""
    invoices = []
    reader = csv.DictReader(io.StringIO(csv_text))
    
    for row in reader:
        inv_no = row.get("Invoice Number") or row.get("Bill Number") or row.get("Invoice#")
        if not inv_no:
            continue
            
        gstin = row.get("GST Identification Number (GSTIN)") or row.get("GSTIN") or row.get("Customer GSTIN") or ""
        pos = row.get("Place of Supply") or (gstin[:2] if len(gstin) >= 2 else "")
        # Clean pos if name like "[27] Maharashtra"
        if "[" in pos and "]" in pos:
            pos = pos.split("[")[1].split("]")[0]
            
        try:
            total = float(row.get("Total") or row.get("Invoice Total") or 0.0)
            cgst = float(row.get("CGST") or 0.0)
            sgst = float(row.get("SGST") or 0.0)
            igst = float(row.get("IGST") or 0.0)
            taxable = float(row.get("SubTotal") or row.get("Taxable Amount") or (total - (cgst + sgst + igst)))
        except ValueError:
            continue
            
        hsn = row.get("HSN/SAC") or row.get("HSN Code") or "9983"
        rate = float(row.get("Item Tax %") or 18.0)

        invoices.append({
            "invoice_number": str(inv_no).strip(),
            "invoice_date": row.get("Invoice Date", ""),
            "buyer_gstin": str(gstin).strip().upper(),
            "place_of_supply": str(pos).strip().zfill(2),
            "taxable_value": round(taxable, 2),
            "cgst": round(cgst, 2),
            "sgst": round(sgst, 2),
            "igst": round(igst, 2),
            "tax_rate": rate,
            "invoice_total": round(total, 2),
            "hsn_sac": str(hsn).strip(),
            "source_software": "Zoho Books"
        })

    return invoices

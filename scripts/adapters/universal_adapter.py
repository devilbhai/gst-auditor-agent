"""
Universal Indian Accounting Software Adapter.
Supports Busy Accounting, Vyapar, Marg ERP 9+, Swipe, and any custom Excel/CSV invoice exports
via Intelligent Column Auto-Detection.
"""

import csv
import io
import json
from typing import List, Dict, Any


COLUMN_ALIASES = {
    "invoice_number": ["invoice_no", "invoice no", "inv no", "invoice number", "vch no", "vch no.", "voucher no", "bill no", "bill number", "doc no"],
    "date": ["date", "invoice date", "vch date", "bill date", "doc date", "inv date"],
    "gstin": ["gstin", "party gstin", "buyer gstin", "customer gstin", "supplier gstin", "gstin/uin", "gst number"],
    "place_of_supply": ["place of supply", "pos", "state code", "state", "place of delivery"],
    "taxable_value": ["taxable value", "taxable amount", "basic amount", "net amount", "taxable amt", "subtotal", "ass value", "taxable"],
    "cgst": ["cgst", "cgst amount", "central tax", "cgst amt", "central gst"],
    "sgst": ["sgst", "sgst amount", "state tax", "sgst amt", "state gst", "utgst"],
    "igst": ["igst", "igst amount", "integrated tax", "igst amt", "integrated gst"],
    "total": ["total", "invoice total", "grand total", "bill amount", "gross total", "net total", "invoice value"],
    "hsn": ["hsn", "hsn code", "hsn/sac", "sac", "sac code", "commodity code"]
}


def find_matching_key(row_dict: Dict[str, Any], canonical_name: str) -> str:
    aliases = COLUMN_ALIASES.get(canonical_name, [])
    # Case insensitive exact match or stripped match
    for k in row_dict.keys():
        cleaned_k = k.strip().lower().replace("_", " ")
        if cleaned_k == canonical_name.replace("_", " ") or cleaned_k in aliases:
            return k
    return ""


def parse_universal_csv(csv_text: str, default_software: str = "Universal / Busy / Vyapar / Marg") -> List[Dict[str, Any]]:
    """Intelligently detects column schemas and converts rows into standardized invoice records."""
    invoices = []
    reader = csv.DictReader(io.StringIO(csv_text))
    
    for row in reader:
        inv_k = find_matching_key(row, "invoice_number")
        if not inv_k or not row.get(inv_k):
            continue
            
        inv_no = str(row[inv_k]).strip()
        
        date_k = find_matching_key(row, "date")
        inv_date = str(row.get(date_k, "")).strip()
        
        gstin_k = find_matching_key(row, "gstin")
        gstin = str(row.get(gstin_k, "")).strip().upper()
        
        pos_k = find_matching_key(row, "place_of_supply")
        pos = str(row.get(pos_k, "")).strip() or (gstin[:2] if len(gstin) >= 2 else "")
        if len(pos) > 2 and pos[:2].isdigit():
            pos = pos[:2]
            
        hsn_k = find_matching_key(row, "hsn")
        hsn = str(row.get(hsn_k, "9983")).strip()
        
        def safe_float(key_name: str) -> float:
            k = find_matching_key(row, key_name)
            if not k:
                return 0.0
            val_str = str(row.get(k, "0")).replace(",", "").replace("₹", "").strip()
            try:
                return float(val_str)
            except ValueError:
                return 0.0
                
        taxable = safe_float("taxable_value")
        cgst = safe_float("cgst")
        sgst = safe_float("sgst")
        igst = safe_float("igst")
        total = safe_float("total")
        
        if total == 0.0:
            total = taxable + cgst + sgst + igst
        if taxable == 0.0 and total > 0.0:
            taxable = max(0.0, total - (cgst + sgst + igst))

        invoices.append({
            "invoice_number": inv_no,
            "invoice_date": inv_date,
            "buyer_gstin": gstin,
            "place_of_supply": pos.zfill(2) if pos else "",
            "taxable_value": round(taxable, 2),
            "cgst": round(cgst, 2),
            "sgst": round(sgst, 2),
            "igst": round(igst, 2),
            "tax_rate": 18.0 if taxable > 0 and (cgst + sgst + igst) > 0 else 0.0,
            "invoice_total": round(total, 2),
            "hsn_sac": hsn,
            "source_software": default_software
        })

    return invoices

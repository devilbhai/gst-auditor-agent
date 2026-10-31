"""
Tally Prime & Tally.ERP 9 Adapter.
Parses Tally XML exports (Daybook, Sales Register) and Tally CSV exports
into standardized invoice data structures for GST auditing and portal filing.
"""

import xml.etree.ElementTree as ET
import csv
import io
from typing import List, Dict, Any


def parse_tally_xml(xml_content: str) -> List[Dict[str, Any]]:
    """Parses standard Tally XML export containing VOUCHER elements."""
    invoices = []
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        # Wrap if fragment
        root = ET.fromstring(f"<ROOT>{xml_content}</ROOT>")

    # Find all vouchers
    for vch in root.iter("VOUCHER"):
        vch_type = vch.findtext("VOUCHERTYPENAME", "").strip()
        inv_no = vch.findtext("VOUCHERNUMBER", "") or vch.findtext("REFERENCE", "")
        inv_date = vch.findtext("DATE", "")
        party_gstin = vch.findtext("PARTYGSTIN", "").strip().upper()
        pos = vch.findtext("PLACEOFSUPPLY", "") or (party_gstin[:2] if len(party_gstin) >= 2 else "")
        
        # Scan ledger entries for amounts
        taxable_amt = 0.0
        cgst = 0.0
        sgst = 0.0
        igst = 0.0
        hsn = ""

        for ledger in vch.iter("ALLLEDGERENTRIES.LIST"):
            lname = ledger.findtext("LEDGERNAME", "").lower()
            amt_str = ledger.findtext("AMOUNT", "0")
            try:
                amt = abs(float(amt_str))
            except ValueError:
                amt = 0.0

            if "cgst" in lname:
                cgst += amt
            elif "sgst" in lname:
                sgst += amt
            elif "igst" in lname:
                igst += amt
            elif "sales" in lname or "income" in lname or "revenue" in lname:
                taxable_amt += amt

        # Scan inventory entries for HSN if present
        for inv_entry in vch.iter("ALLINVENTORYENTRIES.LIST"):
            hsn = inv_entry.findtext("HSNCODE", "") or inv_entry.findtext("COMMODITYCODE", "")
            if taxable_amt == 0:
                try:
                    taxable_amt += abs(float(inv_entry.findtext("AMOUNT", "0")))
                except ValueError:
                    pass

        if inv_no:
            invoices.append({
                "invoice_number": inv_no,
                "invoice_date": inv_date,
                "buyer_gstin": party_gstin,
                "place_of_supply": pos,
                "taxable_value": round(taxable_amt, 2),
                "cgst": round(cgst, 2),
                "sgst": round(sgst, 2),
                "igst": round(igst, 2),
                "tax_rate": 18.0 if taxable_amt > 0 and (cgst + sgst + igst) > 0 else 0.0,
                "invoice_total": round(taxable_amt + cgst + sgst + igst, 2),
                "hsn_sac": hsn or "9983",
                "source_software": "Tally Prime XML"
            })

    return invoices


def parse_tally_csv(csv_text: str) -> List[Dict[str, Any]]:
    """Parses Tally exported Sales/Purchase register CSV."""
    invoices = []
    reader = csv.DictReader(io.StringIO(csv_text))
    
    for row in reader:
        # Standard Tally Column variants
        inv_no = row.get("Vch No.") or row.get("Voucher Number") or row.get("Invoice No") or row.get("Vch No")
        if not inv_no:
            continue
            
        inv_date = row.get("Date") or row.get("Vch Date") or ""
        gstin = row.get("GSTIN/UIN") or row.get("Party GSTIN") or row.get("GSTIN") or ""
        
        try:
            gross = float(row.get("Gross Total") or row.get("Total Amount") or 0.0)
            cgst = float(row.get("CGST") or row.get("Central Tax") or 0.0)
            sgst = float(row.get("SGST") or row.get("State Tax") or 0.0)
            igst = float(row.get("IGST") or row.get("Integrated Tax") or 0.0)
            taxable = float(row.get("Taxable Value") or row.get("Taxable Amount") or (gross - (cgst + sgst + igst)))
        except ValueError:
            continue

        invoices.append({
            "invoice_number": str(inv_no).strip(),
            "invoice_date": str(inv_date).strip(),
            "buyer_gstin": str(gstin).strip().upper(),
            "place_of_supply": gstin[:2] if len(gstin) >= 2 else "",
            "taxable_value": round(taxable, 2),
            "cgst": round(cgst, 2),
            "sgst": round(sgst, 2),
            "igst": round(igst, 2),
            "invoice_total": round(gross or (taxable + cgst + sgst + igst), 2),
            "source_software": "Tally Prime CSV"
        })

    return invoices

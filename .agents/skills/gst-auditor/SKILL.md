---
name: gst-auditor
description: >-
  The Definitive Indian GST, CA Audit & Universal ERP Suite. Imports invoices from Tally Prime (XML/CSV),
  Zoho Books, Busy, Vyapar, Marg ERP, and spreadsheets. Generates and audits GSTR-1, computes GSTR-3B
  tax set-off and cash challans (PMT-06), automates GSTR-9 / 9C annual turnover & ITC reconciliation,
  computes Rule 42 & 43 pro-rata ITC reversals, calculates Form RFD-01 refunds (Inverted Duty & Export LUT),
  evaluates Rule 88C (DRC-01B) & Rule 88D (DRC-01C) notice risks, calculates Section 50 interest,
  generates Form CMP-08 composition challans, computes GSTR-7 TDS and GSTR-8 TCS, enforces Rule 138 E-Way Bills
  and Rule 48(4) E-Invoicing, and verifies 15-character GSTIN Mod-36 checksums.
---

# 🇮🇳 Complete GST & Universal ERP Compliance Suite

This skill equips Antigravity with the comprehensive statutory toolkit used by Indian Chartered Accountants, Tax Consultants, and Accountants across all major Indian ERP systems.

## Universal ERP Importer Commands

```bash
# Import from Tally Prime XML:
python3 scripts/forms_hub.py import daybook.xml --format tally-xml --output sales.json

# Import from Zoho Books CSV:
python3 scripts/forms_hub.py import zoho.csv --format zoho-csv --output sales.json

# Import from Busy / Vyapar / Marg / Excel:
python3 scripts/forms_hub.py import register.csv --format universal-csv --output sales.json
```

## Statutory Returns & Computations

```bash
# GSTR-1 Portal JSON
python3 scripts/forms_hub.py gstr1 sales.json --gstin 27AAPFU0939F1ZV --output gstr1_upload.json

# GSTR-3B Tax Set-Off & PMT-06 Cash Challan
python3 scripts/forms_hub.py gstr3b --sales sales.json --purchases purchases.json --gstin 27AAPFU0939F1ZV

# Rule 42 Pro-rata ITC Reversal on Common Inputs
python3 scripts/forms_hub.py rule42 --total-itc 100000 --exempt-exclusive 10000 --blocked 5000 --taxable-exclusive 50000 --exempt-turnover 200000 --total-turnover 1000000

# Rule 43 Capital Goods Monthly Reversal
python3 scripts/forms_hub.py rule43 --capital-itc 60000 --exempt-turnover 250000 --total-turnover 1000000

# Form RFD-01 Inverted Duty Refund
python3 scripts/forms_hub.py refund --type inverted --inverted-turnover 1000000 --adjusted-turnover 1000000 --net-itc-inputs 180000 --net-itc-services 20000 --tax-payable 50000

# Form CMP-08 Composition Scheme
python3 scripts/forms_hub.py cmp08 --turnover 1000000 --scheme trader

# DRC-01B / DRC-01C / Section 50 Interest
python3 scripts/forms_hub.py notices --check interest --tax-due 100000 --due-date 2026-10-20 --pay-date 2026-11-20
```

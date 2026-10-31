---
name: gst-auditor
description: >-
  The Definitive Indian GST, CA Audit & Universal ERP Suite for Claude Code. Imports invoices from
  Tally Prime (XML/CSV), Zoho Books, Busy, Vyapar, Marg ERP, and spreadsheets. Generates and audits GSTR-1,
  computes GSTR-3B tax set-off and cash challans (PMT-06), automates GSTR-9 / 9C annual turnover & ITC reconciliation,
  computes Rule 42 & 43 pro-rata ITC reversals, calculates Form RFD-01 refunds (Inverted Duty & Export LUT),
  evaluates Rule 88C (DRC-01B) & Rule 88D (DRC-01C) notice risks, calculates Section 50 interest,
  generates Form CMP-08 composition challans, computes GSTR-7 TDS and GSTR-8 TCS, enforces Rule 138 E-Way Bills
  and Rule 48(4) E-Invoicing, and verifies 15-character GSTIN Mod-36 checksums.
---

# 🇮🇳 Complete GST & Universal ERP Compliance Suite (Claude Code)

Enables Claude Code to import from all major Indian accounting software (Tally, Zoho, Busy, Vyapar, Marg) and execute the complete spectrum of GST compliance, returns, reversals, refunds, and notice defenses.

## Quick Runbook

```bash
# Import from Tally Prime XML:
python3 scripts/forms_hub.py import daybook.xml --format tally-xml --output sales.json

# Import from Zoho Books CSV:
python3 scripts/forms_hub.py import zoho.csv --format zoho-csv --output sales.json

# Import from Busy / Vyapar / Marg / CSV:
python3 scripts/forms_hub.py import register.csv --format universal-csv --output sales.json

# Full GSTR-1, GSTR-3B, Rule 42/43, RFD-01 & Notice Audits:
python3 scripts/forms_hub.py --help
```

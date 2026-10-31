---
name: gst-auditor
description: >-
  Complete Indian GST & CA Compliance Suite for Claude Code. Generates and audits GSTR-1,
  computes GSTR-3B tax set-off and cash challans (PMT-06), automates GSTR-9 / 9C annual turnover & ITC
  reconciliation, evaluates Rule 88C (DRC-01B) & Rule 88D (DRC-01C) notice risks, calculates Section 50 interest,
  enforces Rule 138 E-Way Bills & Rule 48(4) E-Invoicing, and verifies 15-char GSTIN Mod-36 checksums.
---

# 🇮🇳 Complete GST & CA Compliance Suite (Claude Code)

Enables Claude Code to handle the entire lifecycle of Indian GST compliance, returns, reconciliations, and notice defenses for accountants and Chartered Accountants.

## Commands

```bash
# GSTR-1 Portal JSON Generation
python3 scripts/forms_hub.py gstr1 sales.json --gstin 27AAPFU0939F1ZV --output gstr1_upload.json

# GSTR-1 Validation
python3 scripts/forms_hub.py gstr1 gstr1_upload.json --gstin 27AAPFU0939F1ZV --validate

# GSTR-3B Computation & Statutory Tax Set-Off
python3 scripts/forms_hub.py gstr3b --sales sales.json --purchases purchases.json --gstin 27AAPFU0939F1ZV

# GSTR-9 / 9C Annual Reconciliation
python3 scripts/forms_hub.py gstr9 --config test_data/sample_gstr9_config.json

# DRC-01B / DRC-01C / Section 50 Interest
python3 scripts/forms_hub.py notices --check interest --tax-due 100000 --due-date 2026-10-20 --pay-date 2026-11-20
```

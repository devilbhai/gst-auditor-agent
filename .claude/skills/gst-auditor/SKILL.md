---
name: gst-auditor
description: >-
  Audits Indian GST invoices, purchase registers, and e-way bills for statutory compliance.
  Use when the user asks to verify GSTINs, audit invoices, check CGST/SGST vs IGST tax split,
  validate HSN/SAC codes, check E-Way Bill mandates (Rule 138), verify E-Invoicing IRN (Rule 48(4)),
  detect blocked ITC under Section 17(5), or reconcile Purchase Books with GSTR-2B.
---

# 🇮🇳 GST Statutory Compliance & Audit Skill (Claude Code)

This skill enables Claude Code to audit Indian GST invoices, detect statutory non-compliance, verify 15-character GSTIN checksums via Mod-36 Luhn variant, validate tax jurisdictions, and verify E-Way Bill and E-Invoicing requirements.

## Usage

Audit an invoice JSON file directly via terminal:
```bash
python3 scripts/gst_auditor.py path/to/invoices.json --html audit_report.html
```

Run test suite:
```bash
python3 -m unittest discover -s tests
```

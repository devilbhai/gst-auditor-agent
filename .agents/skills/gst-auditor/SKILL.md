---
name: gst-auditor
description: >-
  Complete Indian GST & CA Compliance Suite. Generates and audits GSTR-1, computes GSTR-3B
  tax set-off and cash challans (PMT-06), automates GSTR-9 / 9C annual turnover & ITC reconciliation,
  evaluates Rule 88C (DRC-01B) & Rule 88D (DRC-01C) notice risks, calculates Section 50 interest,
  enforces Rule 138 E-Way Bills & Rule 48(4) E-Invoicing, and verifies 15-char GSTIN Mod-36 checksums.
---

# 🇮🇳 Complete GST & CA Compliance Suite

This skill equips Antigravity with the complete set of tools, procedures, and statutory formulas used by Indian Chartered Accountants, Tax Practitioners, and Accountants.

---

## 📋 Comprehensive GST Forms Covered

| Form / Mechanism | Statutory Rule / Section | Purpose |
| :--- | :--- | :--- |
| **GSTR-1** | Section 37 / Rule 59 | Statement of Outward Supplies (B2B, B2CL, B2CS, HSN Table 12, Doc Table 13). Generates GST Portal JSON. |
| **GSTR-2B vs Books** | Section 16(2)(aa) / Rule 36(4) | Reconciles Purchase register against auto-drafted ITC to catch unfiled vendor invoices. |
| **GSTR-3B** | Section 39 / Rule 61 | Summary return, eligible/blocked ITC (Sec 17(5)), and optimal tax set-off under Sec 49, 49A & 49B. |
| **GSTR-9 & 9C** | Section 44 / Rule 80 | Annual Return & CA Reconciliation Statement (Audited P&L vs GSTR-1 vs GSTR-3B vs GSTR-2B). |
| **DRC-01B** | Rule 88C | Intimation of difference in tax liability between GSTR-1 and GSTR-3B (> 20% or > ₹25 Lakhs). |
| **DRC-01C** | Rule 88D | Intimation of difference in ITC availed in GSTR-3B vs available in GSTR-2B. |
| **DRC-03 & Sec 50** | Section 50(1) & 50(3) | Voluntary tax payment & daily interest calculation (18% p.a. for cash delay, 24% p.a. for wrong utilized ITC). |
| **E-Way Bill** | Rule 138 | Consignment movement > ₹50,000 threshold verification. |
| **E-Invoice (IRN)** | Rule 48(4) | Mandatory 64-character hash IRN for businesses with turnover > ₹5 Crore. |

---

## 🛠 Command-Line Usage for the Agent

### 1. Generate Official GSTR-1 Portal JSON:
```bash
python3 scripts/forms_hub.py gstr1 path/to/sales.json --gstin 27AAPFU0939F1ZV --output gstr1_upload.json
```

### 2. Validate GSTR-1 JSON before Portal Upload:
```bash
python3 scripts/forms_hub.py gstr1 path/to/gstr1_upload.json --gstin 27AAPFU0939F1ZV --validate
```

### 3. Compute Monthly GSTR-3B, Tax Set-Off & PMT-06 Cash Challan:
```bash
python3 scripts/forms_hub.py gstr3b --sales sales.json --purchases purchases.json --gstin 27AAPFU0939F1ZV
```

### 4. Run Annual GSTR-9 / 9C Audit & Books Reconciliation:
```bash
python3 scripts/forms_hub.py gstr9 --config test_data/sample_gstr9_config.json
```

### 5. Check DRC-01B / DRC-01C Notice Risk:
```bash
# Check Rule 88C liability difference (GSTR-1 vs 3B):
python3 scripts/forms_hub.py notices --check drc01b --gstr1-tax 500000 --gstr3b-tax 350000

# Check Rule 88D ITC difference (GSTR-2B vs 3B):
python3 scripts/forms_hub.py notices --check drc01c --gstr2b-itc 200000 --gstr3b-itc 280000
```

### 6. Calculate Section 50 Statutory Interest:
```bash
python3 scripts/forms_hub.py notices --check interest --tax-due 100000 --due-date 2026-10-20 --pay-date 2026-11-20
```

### 7. Full Invoice Audit & Interactive Visual HTML Dashboard:
```bash
python3 scripts/gst_auditor.py test_data/sample_invoices.json --html audit_dashboard.html
```

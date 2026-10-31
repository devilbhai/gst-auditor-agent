<div align="center">

# 🇮🇳 GST Auditor Agent

### **The Complete Indian GST, CA Audit & Statutory Forms Suite**
*Autonomous Tax Compliance Engine for Indian Businesses, Accountants & CAs*
*Compatible with Claude Code, Google Antigravity, Cursor, and Python CI/CD*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-21%20Passed%20(100%25)-brightgreen.svg)]()
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero%20(Stdlib)-success.svg)]()
[![Platform](https://img.shields.io/badge/Agent-Antigravity%20%7C%20Claude%20Code-purple.svg)]()

<p align="center">
  <a href="#-the-complete-gst-forms-suite">Forms Suite</a> •
  <a href="#-quickstart-in-30-seconds">Quickstart</a> •
  <a href="#-ca--accountant-runbook">CA Runbook</a> •
  <a href="#-antigravity--claude-code-integration">AI Skill Setup</a> •
  <a href="#-interactive-html-dashboard">Dashboard Preview</a>
</p>

</div>

---

## ⚡ The Complete Indian GST Problem

Every Indian business, accountant, and Chartered Accountant deals with a fragmented maze of returns and notices:
- **GSTR-1 errors** (wrong POS, inter-state charged as intra-state, missing HSN Table 12).
- **GSTR-3B tax payment blunders** (violating Section 49, 49A, 49B set-off rules or wrongly paying cash when ITC is available).
- **ITC mismatches** (Books vs GSTR-2B; claiming ineligible ITC under Section 17(5)).
- **Rule 88C (DRC-01B) & Rule 88D (DRC-01C) departmental notices** when GSTR-1 liability > GSTR-3B or 3B claimed ITC > 2B.
- **GSTR-9 & 9C annual reconciliations** between audited P&L turnover and GST returns.
- **Section 50 statutory interest penalties** (18% p.a. for late cash tax, 24% p.a. for utilized wrongful ITC).

**GST Auditor Agent** solves this end-to-end with **pure Python standard library (zero external dependencies)**.

---

## 📋 The Complete GST Forms Suite

| Form / Mechanism | Statutory Reference | What GST Auditor Agent Does |
| :--- | :--- | :--- |
| **GSTR-1** | Sec 37 / Rule 59 | Generates official GST Portal JSON for Table 4 (B2B), 5 (B2CL), 7 (B2CS), 12 (HSN Summary), 13 (Docs). Audits pre-upload JSON files. |
| **GSTR-2B Reconciler** | Sec 16(2)(aa) / Rule 36(4) | Reconciles purchase registers against GSTR-2B. Identifies unfiled vendor invoices and tax variances. |
| **GSTR-3B** | Sec 39 / Rule 61 | Computes Table 3.1 outward liabilities, Table 4 eligible & reversed ITC (Sec 17(5)), and executes legal set-off under Sec 49, 49A & 49B. Calculates exact PMT-06 cash challan. |
| **GSTR-9 & 9C** | Sec 44 / Rule 80 | Annual reconciliation engine for businesses (> ₹2 Cr / ₹5 Cr). Reconciles Audited P&L Turnover vs GSTR-1 vs GSTR-3B and computes DRC-03 additional tax liability. |
| **DRC-01B** | Rule 88C | Analyzes liability differences between GSTR-1 and GSTR-3B. Flags notice risk if difference > 20% or > ₹25 Lakhs, and drafts statutory justifications. |
| **DRC-01C** | Rule 88D | Analyzes ITC differences between GSTR-2B and GSTR-3B. Flags inadmissible ITC risk and generates explanation grounds. |
| **Section 50 Interest** | Sec 50(1) & 50(3) | Computes exact day-count statutory interest (18% p.a. on delayed net cash tax; 24% p.a. on utilized ineligible ITC). |
| **E-Way Bill (EWB-01)** | Rule 138 | Enforces ₹50,000 threshold (and ₹1 Lakh exemptions in MH, DL, GJ, WB, BR) for movement of goods. |
| **E-Invoice (IRN)** | Rule 48(4) | Enforces 64-character hash IRN and QR validation for businesses with turnover > ₹5 Crore. |

---

## 🚀 Quickstart in 30 Seconds

```bash
# 1. Clone the repository
git clone https://github.com/devilbhai/gst-auditor-agent.git
cd gst-auditor-agent

# 2. Run the 21 automated unit tests (pure stdlib, 100% pass)
python3 -m unittest discover -s tests -v
```

---

## 💼 CA & Accountant Runbook

### 1. Generate Official GSTR-1 Portal JSON
Transform raw sales invoices into GST portal compatible JSON:
```bash
python3 scripts/forms_hub.py gstr1 test_data/sample_invoices.json --gstin 27AAPFU0939F1ZV --output gstr1_portal.json
```

### 2. Pre-Upload Audit of GSTR-1 JSON
Catch tax jurisdiction errors, invalid recipient GSTINs, and HSN defects before uploading:
```bash
python3 scripts/forms_hub.py gstr1 gstr1_portal.json --gstin 27AAPFU0939F1ZV --validate
```

### 3. Compute Monthly GSTR-3B & Cash Challan (PMT-06)
Runs statutory tax set-off (exhausting IGST first, preventing illegal CGST/SGST cross-set-off):
```bash
python3 scripts/forms_hub.py gstr3b \
  --sales test_data/sample_invoices.json \
  --purchases test_data/sample_invoices.json \
  --gstin 27AAPFU0939F1ZV
```

### 4. Annual GSTR-9 / 9C Books Reconciliation
Reconciles audited financial statements against filed GST returns:
```bash
python3 scripts/forms_hub.py gstr9 --config test_data/sample_gstr9_config.json
```

### 5. Check Departmental Notice Risks (Rule 88C & Rule 88D)
```bash
# Check DRC-01B risk (GSTR-1 vs 3B liability mismatch):
python3 scripts/forms_hub.py notices --check drc01b --gstr1-tax 500000 --gstr3b-tax 350000

# Check DRC-01C risk (GSTR-3B claimed ITC vs 2B available):
python3 scripts/forms_hub.py notices --check drc01c --gstr2b-itc 200000 --gstr3b-itc 280000
```

### 6. Calculate Section 50 Statutory Interest
```bash
python3 scripts/forms_hub.py notices --check interest \
  --tax-due 100000 \
  --due-date 2026-10-20 \
  --pay-date 2026-11-20
```

### 7. Run Comprehensive Invoice Audit & Interactive Visual Dashboard
```bash
python3 scripts/gst_auditor.py test_data/sample_invoices.json --html audit_dashboard.html
```

---

## 🤖 Antigravity & Claude Code Integration

### Using with Google Antigravity
The skill is pre-configured in `.agents/skills/gst-auditor/SKILL.md`. Simply copy the folder into your project:

```bash
mkdir -p .agents/skills
cp -r /path/to/gst-auditor-agent/.agents/skills/gst-auditor .agents/skills/
```
In chat, simply instruct:
> *"Audit our sales in sales.json, check DRC-01B notice risk against our 3B, and generate our GSTR-1 portal JSON."*

### Using with Claude Code
Claude Code automatically discovers skills in `.claude/skills/`:
```bash
cp -r .claude/skills/gst-auditor ~/.claude/skills/
```

---

## 🗂 Project Structure

```text
gst-auditor-agent/
├── .agents/skills/gst-auditor/   # Antigravity skill definitions & guides
│   ├── SKILL.md
│   └── references/gst_rules.md  # Detailed statutory guidelines
├── .claude/skills/gst-auditor/   # Claude Code skill definition
│   └── SKILL.md
├── scripts/
│   ├── forms_hub.py             # Master CLI for CAs & accountants
│   ├── gstr1_engine.py          # GSTR-1 generator & portal JSON validator
│   ├── gstr3b_engine.py         # GSTR-3B computation & Sec 49 set-off engine
│   ├── gstr9_engine.py          # GSTR-9 / 9C annual reconciliation engine
│   ├── notices_drc_engine.py    # DRC-01B, DRC-01C & Sec 50 interest engine
│   ├── gst_auditor.py           # Core invoice auditor and CLI
│   ├── gstin_validator.py       # Mod-36 Luhn GSTIN checksum validator
│   ├── gst_rules.py             # Statutory rules (Rule 138, Rule 48, Sec 17(5))
│   ├── hsn_verifier.py          # HSN / SAC codes and rate checker
│   ├── itc_reconciler.py        # Purchase Register vs GSTR-2B reconciler
│   └── report_generator.py      # Terminal Markdown & Interactive HTML generator
├── test_data/
│   ├── sample_invoices.json     # Diverse real-world Indian invoice test cases
│   ├── sample_gstr9_config.json # Annual audit reconciliation sample config
│   └── sample_audit_dashboard.html
├── tests/
│   ├── test_gst_auditor.py      # Core auditor test suite (14 tests)
│   └── test_gst_forms.py        # Forms & CA suite test suite (7 tests)
├── pyproject.toml
├── LICENSE                      # MIT License
└── README.md
```

---

## 🧪 Testing

```bash
python3 -m unittest discover -s tests -v
```

All **21 tests** pass in `< 0.01s` with pure standard library.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

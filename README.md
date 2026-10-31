<div align="center">

# 🇮🇳 GST Auditor Agent

### **Autonomous Indian GST, E-Way Bill & E-Invoice Audit Agent**
*Compatible with Claude Code, Google Antigravity, Cursor, and Python CI/CD*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-14%20Passed%20(100%25)-brightgreen.svg)]()
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero%20(Stdlib)-success.svg)]()
[![Platform](https://img.shields.io/badge/Agent-Antigravity%20%7C%20Claude%20Code-purple.svg)]()

<p align="center">
  <a href="#-quickstart-in-30-seconds">Quickstart</a> •
  <a href="#-core-auditing-superpowers">Superpowers</a> •
  <a href="#-antigravity--claude-code-integration">AI Skill Setup</a> •
  <a href="#-interactive-html-dashboard">Dashboard Preview</a> •
  <a href="#-statutory-rules-covered">Statutory Rules</a>
</p>

</div>

---

## ⚡ Why GST Auditor Agent?

Every Indian startup, SaaS, and SME dreads GST reconciliation. A single tax jurisdiction mistake (such as charging **IGST on intra-state supplies** or missing an **E-Way Bill** for consignments > ₹50,000) results in show-cause notices, 18% penalty interest, and disallowed Input Tax Credit (ITC).

**GST Auditor Agent** is an autonomous compliance engine and AI skill that inspects invoices, detects fraudulent or faulty GSTINs via **Mod-36 Luhn checksums**, verifies Place of Supply, enforces **Rule 138 (E-Way Bill)** and **Rule 48(4) (E-Invoicing IRN)**, flags **Section 17(5) Blocked ITC**, and reconciles Books with **GSTR-2B**.

---

## 🚀 Quickstart in 30 Seconds

> **Zero external dependencies required.** Runs on pure Python 3 standard library.

```bash
# 1. Clone the repository
git clone https://github.com/your-username/gst-auditor-agent.git
cd gst-auditor-agent

# 2. Run the audit against sample invoices
python3 scripts/gst_auditor.py test_data/sample_invoices.json --html test_data/sample_audit_dashboard.html

# 3. Run full test suite (100% pass)
python3 -m unittest discover -s tests
```

### 📺 Terminal Output Preview

```text
# 🇮🇳 GST Compliance & Statutory Audit Report
Audit Status: 🔴 ACTION REQUIRED | Invoices Audited: 5 | Compliance Score: 40.0%

### 📊 Executive Summary
- Passed Invoices: 2 / 5
- Flagged Invoices: 3 / 5
- Critical Statutory Errors: 3
- Compliance Warnings: 3
- Total Tax Exposure / At-Risk ITC: ₹61,200.00

---
### 🔍 Detailed Invoice Findings

#### Invoice #INV-2026-001 — ✅ PASS
- Supplier: 27AAPFU0939F1ZV (Maharashtra)
- Buyer / POS: 27AAACW1234D1ZS (State: 27)
- Invoice Total: ₹118,000.00
- No discrepancies found. All checks verified.

#### Invoice #INV-2026-002 — ❌ FAIL
- Detected Discrepancies:
  ⚠️ [CRITICAL - TAX JURISDICTION ERROR] Inter-state transaction (State 27 != 29) cannot charge CGST or SGST. Must charge IGST only.
  ⚠️ [COMPLIANCE RISK - RULE 138] Consignment value ₹295,000.00 exceeds threshold ₹50,000.00. Missing E-Way Bill Number.
  ⚠️ [LEGAL INVALIDITY - RULE 48(4)] Aggregate turnover > ₹5 Cr mandate. B2B invoices without 64-char IRN are null & void.
```

---

## 🧠 Core Auditing Superpowers

| Feature | Description | Statutory Reference |
| :--- | :--- | :--- |
| **GSTIN Mod-36 Checksum** | Algorithmically recalculates the 15th checksum character to catch fake/mistyped GST numbers. | GSTIN Specifications |
| **Tax Jurisdiction Engine** | Auto-checks State Code vs Place of Supply. Prevents illegal IGST on local sales or CGST/SGST on inter-state sales. | Sec 7 & 8 IGST Act |
| **Rule 138 E-Way Bill** | Flags goods shipments > ₹50k (or ₹1 Lakh in exempt states like DL, MH, WB, GJ) lacking valid e-Way bill. | CGST Rule 138 |
| **Rule 48(4) E-Invoicing** | Validates 64-character hash IRN for businesses with turnover > ₹5 Cr. | CGST Rule 48(4) |
| **Sec 17(5) Blocked ITC** | Detects ineligible ITC claims (gym memberships, food & beverage, passenger motor cars). | CGST Sec 17(5) |
| **GSTR-2B Reconciler** | Reconciles purchase books against GSTR-2B to catch unfiled vendor invoices before filing GSTR-3B. | CGST Sec 16(2)(aa) |

---

## 🤖 Antigravity & Claude Code Integration

### Using with Google Antigravity
The skill is pre-configured in `.agents/skills/gst-auditor/SKILL.md`. Simply copy the folder into your project:

```bash
# Add to any existing repo
mkdir -p .agents/skills
cp -r /path/to/gst-auditor-agent/.agents/skills/gst-auditor .agents/skills/
```
In chat, simply instruct:
> *"Audit our October purchase invoices in data/purchases.json and generate a compliance dashboard."*

### Using with Claude Code
Claude Code automatically discovers skills in `.claude/skills/`:
```bash
cp -r .claude/skills/gst-auditor ~/.claude/skills/
```

---

## 📊 Interactive HTML Dashboard

Generate executive-ready, interactive visual audit reports with a single flag:

```bash
python3 scripts/gst_auditor.py test_data/sample_invoices.json --html audit_dashboard.html
```

Features included in the dashboard:
- **Compliance Health Gauge** (Score %, Passed vs Flagged)
- **Financial Exposure Metric** (Total At-Risk Tax Amount in ₹)
- **Live Filter Buttons** (*All*, *Flagged Only*, *Passed*)
- **Print / PDF Export Ready** with Tailwind CSS styling

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
│   ├── gst_auditor.py           # Core orchestrator and CLI
│   ├── gstin_validator.py       # Mod-36 Luhn GSTIN validator
│   ├── gst_rules.py             # Statutory rules (Rule 138, Rule 48, Sec 17(5))
│   ├── hsn_verifier.py          # HSN / SAC codes and rate checker
│   ├── itc_reconciler.py        # Purchase Register vs GSTR-2B reconciliation
│   └── report_generator.py      # Terminal Markdown & Interactive HTML generator
├── test_data/
│   ├── sample_invoices.json     # Diverse real-world Indian invoice test cases
│   └── sample_audit_dashboard.html
├── tests/
│   └── test_gst_auditor.py      # Unit tests (14 test cases, 100% pass)
├── pyproject.toml
├── LICENSE                      # MIT License
└── README.md
```

---

## 🧪 Testing

```bash
python3 -m unittest discover -s tests -v
```

All 14 tests run in `< 0.01s` with 0 external dependencies.

---

## 🤝 Contributing

Contributions are welcome! If you want to add new HSN codes, state-specific e-way bill exemptions, or Tally/Zoho/Swipe JSON adapters:
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/tally-adapter`)
3. Commit your Changes (`git commit -m 'Add Tally Prime XML/JSON parser'`)
4. Push to the Branch (`git push origin feature/tally-adapter`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

---
name: gst-auditor
description: >-
  Audits Indian GST invoices, purchase registers, and e-way bills for statutory compliance.
  Use when the user asks to verify GSTINs, audit invoices, check CGST/SGST vs IGST tax split,
  validate HSN/SAC codes, check E-Way Bill mandates (Rule 138), verify E-Invoicing IRN (Rule 48(4)),
  detect blocked ITC under Section 17(5), or reconcile Purchase Books with GSTR-2B.
---

# 🇮🇳 GST Statutory Compliance & Audit Skill

This skill turns Antigravity into an autonomous Indian GST auditor. It verifies invoices against GST statutory rules, catches tax jurisdiction blunders (e.g. intra-state charged as IGST), validates 15-character GSTIN checksums via Mod-36 Luhn variant, audits E-Way Bill and E-Invoicing mandates, and identifies blocked ITC.

## Quick CLI Execution

To run an audit on a batch of invoices (JSON):

```bash
python3 scripts/gst_auditor.py path/to/invoices.json --html path/to/audit_dashboard.html
```

To specify annual turnover (defaults to 5.0 Cr for Rule 48(4) IRN check):
```bash
python3 scripts/gst_auditor.py path/to/invoices.json --turnover 10.0
```

To output structured JSON:
```bash
python3 scripts/gst_auditor.py path/to/invoices.json --json
```

---

## Statutory Rules Enforced

1. **GSTIN Checksum & State Code Verification**:
   - Algorithmic 15-character validation (State Code + PAN + Entity + 'Z' + Mod-36 checksum).
2. **Place of Supply (POS) & Tax Split**:
   - `Supplier State == Place of Supply`: Intra-State $\rightarrow$ CGST + SGST (50% equal split). IGST must be 0.
   - `Supplier State != Place of Supply`: Inter-State $\rightarrow$ IGST only. CGST and SGST must be 0.
3. **E-Way Bill Mandate (Rule 138)**:
   - Consignments of goods exceeding ₹50,000 (or ₹1,00,000 for intra-state in exempted states like Maharashtra, Delhi, Gujarat, Bihar, West Bengal) must have a valid 12-digit E-Way Bill Number.
   - Services (SAC starting with 99) are exempt.
4. **E-Invoicing / IRN Mandate (Rule 48(4))**:
   - Mandatory for businesses with aggregate turnover > ₹5 Crore.
   - B2B invoices without a 64-character Invoice Reference Number (IRN) generated via the IRP are legally void; buyer cannot claim Input Tax Credit (ITC).
5. **HSN / SAC Code & Tax Slab**:
   - Validates code length (minimum 4 digits for turnover $\le$ ₹5 Cr; minimum 6 digits for turnover > ₹5 Cr).
   - Validates tax rate against statutory slabs: 0%, 0.1%, 0.25%, 1.5%, 3%, 5%, 12%, 18%, 28%.
6. **Blocked ITC Section 17(5)**:
   - Flags ineligibility for motor vehicles, food & beverages, outdoor catering, club memberships, personal consumption, and lost/stolen goods.
7. **Purchase Register vs GSTR-2B Reconciliation**:
   - Detects unfiled vendor invoices (ITC at risk under Section 16(2)(aa)).
   - Flags tax amount discrepancies between books and GSTR-2B.

---

## Step-by-Step Audit Procedure for the Agent

When the user provides an invoice or ask to audit books:

1. **Locate or Extract Data**:
   Parse invoice details: `supplier_gstin`, `buyer_gstin`, `place_of_supply`, `taxable_value`, `cgst`, `sgst`, `igst`, `hsn_sac`, `invoice_total`, `irn`, `eway_bill_number`.
2. **Run Core Auditor**:
   Invoke `scripts/gst_auditor.py` or import `audit_single_invoice` from `scripts.gst_auditor`.
3. **Present Output**:
   - Executive Summary (Total Invoices, Passed, Critical Errors, Tax At Risk).
   - Detailed Findings per invoice.
   - If requested, generate the interactive HTML Dashboard using `--html <filename>.html`.

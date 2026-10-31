"""
Audit Report Generator.
Produces high-impact Terminal Markdown and standalone Interactive HTML Dashboards.
"""

from typing import Dict, Any, List
import json


def generate_markdown_report(audit_result: Dict[str, Any]) -> str:
    """Generates a clean, comprehensive Markdown audit report."""
    summary = audit_result.get("summary", {})
    invoices = audit_result.get("audited_invoices", [])
    
    total = summary.get("total_invoices", 0)
    passed = summary.get("passed_invoices", 0)
    failed = summary.get("failed_invoices", 0)
    critical_issues = summary.get("total_critical_errors", 0)
    warnings = summary.get("total_warnings", 0)
    at_risk_amount = summary.get("total_tax_at_risk", 0.0)
    
    status_icon = "🟢 COMPLIANT" if failed == 0 else "🔴 ACTION REQUIRED"
    
    lines = [
        f"# 🇮🇳 GST Compliance & Statutory Audit Report",
        f"**Audit Status:** {status_icon} | **Invoices Audited:** {total} | **Compliance Score:** {round((passed/total)*100, 1) if total else 100}%",
        f"",
        f"### 📊 Executive Summary",
        f"- **Passed Invoices:** {passed} / {total}",
        f"- **Flagged Invoices:** {failed} / {total}",
        f"- **Critical Statutory Errors:** {critical_issues}",
        f"- **Compliance Warnings:** {warnings}",
        f"- **Total Tax Exposure / At-Risk ITC:** ₹{at_risk_amount:,.2f}",
        f"",
        f"---",
        f"### 🔍 Detailed Invoice Findings",
        f""
    ]
    
    for inv in invoices:
        inv_no = inv.get("invoice_number", "Unknown")
        status = "✅ PASS" if inv.get("compliant") else "❌ FAIL"
        lines.append(f"#### Invoice #{inv_no} — {status}")
        lines.append(f"- **Supplier:** `{inv.get('supplier_gstin')}` ({inv.get('supplier_state', 'Unknown')})")
        lines.append(f"- **Buyer / POS:** `{inv.get('buyer_gstin')}` (State: {inv.get('place_of_supply', 'Unknown')})")
        lines.append(f"- **Invoice Total:** ₹{inv.get('invoice_total', 0):,.2f}")
        
        issues = inv.get("issues", [])
        if issues:
            lines.append(f"- **Detected Discrepancies:**")
            for issue in issues:
                lines.append(f"  - ⚠️ {issue}")
        else:
            lines.append(f"- **No discrepancies found.** All checks verified.")
        lines.append("")
        
    return "\n".join(lines)


def generate_html_dashboard(audit_result: Dict[str, Any], output_path: str) -> None:
    """Creates a modern, standalone interactive HTML dashboard with charts and filters."""
    summary = audit_result.get("summary", {})
    invoices = audit_result.get("audited_invoices", [])
    
    total = summary.get("total_invoices", 0)
    passed = summary.get("passed_invoices", 0)
    failed = summary.get("failed_invoices", 0)
    critical_errors = summary.get("total_critical_errors", 0)
    warnings = summary.get("total_warnings", 0)
    tax_at_risk = summary.get("total_tax_at_risk", 0.0)
    compliance_score = round((passed / total * 100), 1) if total else 100

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GST Auditor Agent — Compliance Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}
    </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen p-4 md:p-8">
    <div class="max-w-7xl mx-auto space-y-8">
        
        <!-- Header -->
        <header class="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
            <div>
                <div class="flex items-center gap-3">
                    <span class="text-3xl">🇮🇳</span>
                    <h1 class="text-2xl md:text-3xl font-extrabold tracking-tight bg-gradient-to-r from-orange-400 via-amber-200 to-emerald-400 bg-clip-text text-transparent">
                        GST Auditor Agent
                    </h1>
                    <span class="px-2.5 py-1 text-xs font-semibold rounded-full bg-orange-500/10 text-orange-400 border border-orange-500/20">
                        Statutory Engine v1.0
                    </span>
                </div>
                <p class="text-slate-400 text-sm mt-1">Autonomous Indian GST, E-Way Bill & E-Invoice Audit Report</p>
            </div>
            <div class="flex items-center gap-3">
                <button onclick="window.print()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg border border-slate-700 transition">
                    Export PDF
                </button>
            </div>
        </header>

        <!-- KPI Cards Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            <!-- Score Card -->
            <div class="bg-slate-800/60 border border-slate-800 rounded-2xl p-5 shadow-xl relative overflow-hidden">
                <div class="flex justify-between items-start">
                    <span class="text-slate-400 text-xs font-semibold uppercase tracking-wider">Compliance Health</span>
                    <span class="px-2 py-0.5 text-xs font-bold rounded {'bg-emerald-500/20 text-emerald-400' if compliance_score >= 80 else 'bg-rose-500/20 text-rose-400'}">
                        {'HEALTHY' if compliance_score >= 80 else 'AT RISK'}
                    </span>
                </div>
                <div class="mt-3 text-3xl font-black text-white">{compliance_score}%</div>
                <div class="w-full bg-slate-700/50 h-2 rounded-full mt-3 overflow-hidden">
                    <div class="{'bg-emerald-500' if compliance_score >= 80 else 'bg-rose-500'} h-full rounded-full" style="width: {compliance_score}%"></div>
                </div>
            </div>

            <!-- Total Invoices -->
            <div class="bg-slate-800/60 border border-slate-800 rounded-2xl p-5 shadow-xl">
                <span class="text-slate-400 text-xs font-semibold uppercase tracking-wider">Audited Invoices</span>
                <div class="mt-3 text-3xl font-black text-white">{total}</div>
                <div class="text-xs text-slate-400 mt-2 flex gap-3">
                    <span class="text-emerald-400 font-semibold">{passed} Valid</span>
                    <span>•</span>
                    <span class="text-rose-400 font-semibold">{failed} Flagged</span>
                </div>
            </div>

            <!-- Critical Errors -->
            <div class="bg-slate-800/60 border border-slate-800 rounded-2xl p-5 shadow-xl">
                <span class="text-slate-400 text-xs font-semibold uppercase tracking-wider">Critical Tax Violations</span>
                <div class="mt-3 text-3xl font-black text-rose-400">{critical_errors}</div>
                <div class="text-xs text-amber-400 mt-2 font-medium">+{warnings} Statutory Warnings</div>
            </div>

            <!-- Tax at Risk -->
            <div class="bg-slate-800/60 border border-slate-800 rounded-2xl p-5 shadow-xl">
                <span class="text-slate-400 text-xs font-semibold uppercase tracking-wider">Tax Exposure / Risk</span>
                <div class="mt-3 text-3xl font-black text-amber-300">₹{tax_at_risk:,.2f}</div>
                <div class="text-xs text-slate-400 mt-2">Disputed or Ineligible ITC</div>
            </div>
        </div>

        <!-- Invoices Audit Table -->
        <div class="bg-slate-800/40 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
            <div class="p-5 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <h2 class="text-lg font-bold text-slate-100 flex items-center gap-2">
                    <span>Audit Breakdown</span>
                    <span class="text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-300 font-normal">{len(invoices)} entries</span>
                </h2>
                <div class="flex gap-2">
                    <button onclick="filterTable('all')" class="filter-btn px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600 text-white" data-filter="all">All</button>
                    <button onclick="filterTable('failed')" class="filter-btn px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700" data-filter="failed">Flagged Only</button>
                    <button onclick="filterTable('passed')" class="filter-btn px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700" data-filter="passed">Passed</button>
                </div>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm" id="invoiceTable">
                    <thead class="bg-slate-800/80 text-slate-400 text-xs uppercase font-semibold">
                        <tr>
                            <th class="py-3.5 px-4">Invoice #</th>
                            <th class="py-3.5 px-4">Supplier & POS</th>
                            <th class="py-3.5 px-4">Total Value</th>
                            <th class="py-3.5 px-4">Taxes (C/S/I)</th>
                            <th class="py-3.5 px-4">Status</th>
                            <th class="py-3.5 px-4">Audited Issues</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800/60 font-mono text-xs">
"""

    for inv in invoices:
        is_pass = inv.get("compliant", False)
        status_class = "passed" if is_pass else "failed"
        badge_html = """<span class="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">PASS</span>""" if is_pass else """<span class="px-2.5 py-1 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">AUDIT FAIL</span>"""
        
        issues_list = inv.get("issues", [])
        if issues_list:
            issues_rendered = "<ul class='space-y-1 text-rose-300 font-sans'>"
            for iss in issues_list:
                issues_rendered += f"<li class='flex items-start gap-1.5'><span>⚠️</span><span>{iss}</span></li>"
            issues_rendered += "</ul>"
        else:
            issues_rendered = "<span class='text-slate-500 font-sans'>No issues detected</span>"

        taxes = f"C: ₹{inv.get('cgst', 0):.0f} | S: ₹{inv.get('sgst', 0):.0f} | I: ₹{inv.get('igst', 0):.0f}"

        html_content += f"""
                        <tr class="hover:bg-slate-800/30 transition invoice-row {status_class}">
                            <td class="py-4 px-4 font-bold text-slate-200">{inv.get('invoice_number')}</td>
                            <td class="py-4 px-4">
                                <div class="text-slate-300">{inv.get('supplier_gstin')}</div>
                                <div class="text-slate-500 text-[11px] font-sans">POS: State {inv.get('place_of_supply')}</div>
                            </td>
                            <td class="py-4 px-4 font-sans text-slate-200 font-semibold">₹{inv.get('invoice_total', 0):,.2f}</td>
                            <td class="py-4 px-4 text-slate-400">{taxes}</td>
                            <td class="py-4 px-4">{badge_html}</td>
                            <td class="py-4 px-4 max-w-md">{issues_rendered}</td>
                        </tr>
"""

    html_content += """
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Footer -->
        <footer class="pt-6 border-t border-slate-800 text-center text-xs text-slate-500">
            Automated by <span class="font-semibold text-slate-400">GST Auditor Agent</span> • Built for Antigravity & Claude Code
        </footer>
    </div>

    <script>
        function filterTable(filter) {
            document.querySelectorAll('.filter-btn').forEach(btn => {
                if (btn.getAttribute('data-filter') === filter) {
                    btn.classList.add('bg-indigo-600', 'text-white');
                    btn.classList.remove('bg-slate-800', 'text-slate-300');
                } else {
                    btn.classList.remove('bg-indigo-600', 'text-white');
                    btn.classList.add('bg-slate-800', 'text-slate-300');
                }
            });

            const rows = document.querySelectorAll('.invoice-row');
            rows.forEach(row => {
                if (filter === 'all') {
                    row.style.display = '';
                } else if (row.classList.contains(filter)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

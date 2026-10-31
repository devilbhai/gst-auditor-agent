#!/usr/bin/env python3
"""
GST Forms Hub — Complete Indian Tax Accounting & CA Audit Suite.
Unified command-line interface for Indian Accountants, Tax Consultants, and CAs.
Supports:
- GSTR-1 Portal JSON Generation & Pre-Upload Audit
- GSTR-3B Computation, ITC Optimization & Cash Set-off Engine
- GSTR-9 / 9C Annual Books Reconciliation
- DRC-01B / DRC-01C Notice Risk Analyzer & Section 50 Interest Calculator
- Rule 42 & Rule 43 Pro-Rata ITC Reversal Engine
- Form RFD-01 GST Refund Engine (Inverted Duty & Export LUT)
- Form CMP-08 Composition Scheme Engine
- GSTR-7 (TDS) & GSTR-8 (TCS) Return Engine
- Universal Accounting Importers (Tally Prime, Zoho Books, Busy, Vyapar, Marg ERP, CSV)
"""

import os
import sys
import json
import argparse
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gstr1_engine import build_gstr1_tables, audit_gstr1_portal_json
from gstr3b_engine import compute_gstr3b
from gstr9_engine import compute_gstr9_reconciliation
from notices_drc_engine import (
    calculate_section_50_interest,
    analyze_drc01b_rule_88c,
    analyze_drc01c_rule_88d
)
from rule42_43_engine import compute_rule42_reversal, compute_rule43_reversal
from refund_engine import compute_inverted_duty_refund, compute_export_lut_refund
from composition_engine import compute_cmp08_quarterly
from tds_tcs_engine import compute_gstr7_tds, compute_gstr8_tcs
from ims_engine import check_section_16_4_time_limit, process_ims_actions, compute_isd_distribution

from adapters.tally_adapter import parse_tally_xml, parse_tally_csv
from adapters.zoho_adapter import parse_zoho_csv
from adapters.universal_adapter import parse_universal_csv


def main():
    parser = argparse.ArgumentParser(
        description="GST Forms Hub — Complete Indian Tax Accounting & CA Audit Suite"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available GST statutory modules")

    # 1. GSTR-1
    p_gstr1 = subparsers.add_parser("gstr1", help="Generate or audit GSTR-1 return")
    p_gstr1.add_argument("sales_file", help="JSON file containing outward sales invoices")
    p_gstr1.add_argument("--gstin", required=True, help="Taxpayer 15-char GSTIN")
    p_gstr1.add_argument("--period", default="102026", help="Financial Period MMYYYY (default: 102026)")
    p_gstr1.add_argument("--output", help="Path to write GST Portal uploadable JSON file")
    p_gstr1.add_argument("--validate", action="store_true", help="Validate existing GSTR-1 JSON")

    # 2. GSTR-3B
    p_gstr3b = subparsers.add_parser("gstr3b", help="Compute GSTR-3B tax payment, ITC and cash challan")
    p_gstr3b.add_argument("--sales", required=True, help="JSON file of sales invoices")
    p_gstr3b.add_argument("--purchases", required=True, help="JSON file of purchase invoices")
    p_gstr3b.add_argument("--gstin", required=True, help="Taxpayer 15-char GSTIN")
    p_gstr3b.add_argument("--period", default="102026", help="Period MMYYYY")

    # 3. GSTR-9 / 9C
    p_gstr9 = subparsers.add_parser("gstr9", help="GSTR-9 / 9C Annual Reconciliation (Books vs Portal)")
    p_gstr9.add_argument("--config", required=True, help="JSON file with annual turnover, tax paid & ITC data")

    # 4. DRC & Notices
    p_drc = subparsers.add_parser("notices", help="Analyze DRC-01B / DRC-01C notice risk & Section 50 interest")
    p_drc.add_argument("--check", choices=["drc01b", "drc01c", "interest"], required=True)
    p_drc.add_argument("--gstr1-tax", type=float, default=0.0)
    p_drc.add_argument("--gstr3b-tax", type=float, default=0.0)
    p_drc.add_argument("--gstr2b-itc", type=float, default=0.0)
    p_drc.add_argument("--gstr3b-itc", type=float, default=0.0)
    p_drc.add_argument("--tax-due", type=float, default=0.0)
    p_drc.add_argument("--due-date", help="YYYY-MM-DD")
    p_drc.add_argument("--pay-date", help="YYYY-MM-DD")
    p_drc.add_argument("--wrong-itc", action="store_true", help="Calculate 24%% interest on utilized wrong ITC")

    # 5. Rule 42 & 43
    p_r42 = subparsers.add_parser("rule42", help="Compute Rule 42 pro-rata ITC reversal on common inputs")
    p_r42.add_argument("--total-itc", type=float, required=True, help="Total input tax (T)")
    p_r42.add_argument("--non-business", type=float, default=0.0, help="T1 (Non-business exclusive)")
    p_r42.add_argument("--exempt-exclusive", type=float, default=0.0, help="T2 (Exempt exclusive)")
    p_r42.add_argument("--blocked", type=float, default=0.0, help="T3 (Sec 17(5) blocked)")
    p_r42.add_argument("--taxable-exclusive", type=float, default=0.0, help="T4 (Taxable exclusive)")
    p_r42.add_argument("--exempt-turnover", type=float, required=True, help="E (Exempt turnover)")
    p_r42.add_argument("--total-turnover", type=float, required=True, help="F (Total turnover)")

    p_r43 = subparsers.add_parser("rule43", help="Compute Rule 43 monthly reversal on Capital Goods")
    p_r43.add_argument("--capital-itc", type=float, required=True, help="Tc (Common capital goods credit)")
    p_r43.add_argument("--exempt-turnover", type=float, required=True, help="E (Exempt turnover)")
    p_r43.add_argument("--total-turnover", type=float, required=True, help="F (Total turnover)")

    # 6. GST Refund (RFD-01)
    p_ref = subparsers.add_parser("refund", help="Calculate GST Refunds (Inverted Duty or Export LUT)")
    p_ref.add_argument("--type", choices=["inverted", "export"], required=True)
    p_ref.add_argument("--inverted-turnover", type=float, default=0.0)
    p_ref.add_argument("--export-turnover", type=float, default=0.0)
    p_ref.add_argument("--adjusted-turnover", type=float, required=True)
    p_ref.add_argument("--net-itc-inputs", type=float, default=0.0)
    p_ref.add_argument("--net-itc-services", type=float, default=0.0)
    p_ref.add_argument("--tax-payable", type=float, default=0.0)

    # 7. Composition Scheme (CMP-08)
    p_cmp = subparsers.add_parser("cmp08", help="Compute Form CMP-08 quarterly payment challan")
    p_cmp.add_argument("--turnover", type=float, required=True)
    p_cmp.add_argument("--scheme", choices=["trader", "manufacturer", "restaurant", "service_provider"], default="trader")
    p_cmp.add_argument("--rcm-val", type=float, default=0.0)

    # 8. TDS / TCS
    p_tds = subparsers.add_parser("tds", help="Compute GSTR-7 TDS under Section 51")
    p_tds.add_argument("contracts_file", help="JSON file with contract records")
    p_tds.add_argument("--deductor-gstin", required=True)
    p_tds.add_argument("--period", default="102026")

    p_tcs = subparsers.add_parser("tcs", help="Compute GSTR-8 TCS under Section 52 for E-Commerce Operators")
    p_tcs.add_argument("supplies_file", help="JSON file with supplies data")
    p_tcs.add_argument("--eco-gstin", required=True)
    p_tcs.add_argument("--period", default="102026")

    # 9. Universal Importers
    p_imp = subparsers.add_parser("import", help="Import invoices from Tally, Zoho, Busy, Vyapar, Marg, or CSV")
    p_imp.add_argument("file", help="Path to input export file (XML or CSV)")
    p_imp.add_argument("--format", choices=["tally-xml", "tally-csv", "zoho-csv", "universal-csv", "busy", "vyapar", "marg"], default="universal-csv")
    p_imp.add_argument("--output", help="Optional path to save normalized JSON file")

    # 10. 2026 Modern Mandates: IMS & Section 16(4) & ISD
    p_ims = subparsers.add_parser("ims", help="Simulate GSTN Invoice Management System (IMS) Accept/Reject/Pending actions")
    p_ims.add_argument("actions_file", help="JSON file with invoice actions")
    p_ims.add_argument("--period", default="102026")

    p_s16 = subparsers.add_parser("sec16-4", help="Audit Section 16(4) 30-Nov statutory time limit on ITC")
    p_s16.add_argument("--invoice-date", required=True, help="YYYY-MM-DD")
    p_s16.add_argument("--filing-date", required=True, help="YYYY-MM-DD")

    p_isd = subparsers.add_parser("isd", help="Mandatory Input Service Distributor (GSTR-6) allocation under Sec 20")
    p_isd.add_argument("config_file", help="JSON file with HO GSTIN, common ITC and branch turnover data")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # GSTR-1
    if args.command == "gstr1":
        with open(args.sales_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if args.validate:
            res = audit_gstr1_portal_json(data)
            print(json.dumps(res, indent=2))
        else:
            invoices = data if isinstance(data, list) else data.get("invoices", [])
            gstr1_payload = build_gstr1_tables(invoices, gstin=args.gstin, fp=args.period)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as out_f:
                    json.dump(gstr1_payload, out_f, indent=2)
                print(f"✅ GSTR-1 Portal JSON written to: {args.output}")
            else:
                print(json.dumps(gstr1_payload, indent=2))

    # GSTR-3B
    elif args.command == "gstr3b":
        with open(args.sales, "r", encoding="utf-8") as sf:
            s_data = json.load(sf)
        with open(args.purchases, "r", encoding="utf-8") as pf:
            p_data = json.load(pf)
        s_invs = s_data if isinstance(s_data, list) else s_data.get("invoices", [])
        p_invs = p_data if isinstance(p_data, list) else p_data.get("invoices", [])
        g3b = compute_gstr3b(s_invs, p_invs, gstin=args.gstin, fp=args.period)
        print(json.dumps(g3b, indent=2))

    # GSTR-9
    elif args.command == "gstr9":
        with open(args.config, "r", encoding="utf-8") as cf:
            cfg = json.load(cf)
        g9 = compute_gstr9_reconciliation(
            audited_pnl_turnover=float(cfg.get("audited_pnl_turnover", 0.0)),
            gstr1_annual_turnover=float(cfg.get("gstr1_annual_turnover", 0.0)),
            gstr3b_annual_turnover=float(cfg.get("gstr3b_annual_turnover", 0.0)),
            books_tax_payable=cfg.get("books_tax_payable", {}),
            gstr3b_tax_paid=cfg.get("gstr3b_tax_paid", {}),
            books_itc=cfg.get("books_itc", {}),
            gstr3b_claimed_itc=cfg.get("gstr3b_claimed_itc", {}),
            gstr2b_annual_itc=cfg.get("gstr2b_annual_itc", {})
        )
        print(json.dumps(g9, indent=2))

    # Notices & DRC
    elif args.command == "notices":
        if args.check == "drc01b":
            res = analyze_drc01b_rule_88c(args.gstr1_tax, args.gstr3b_tax)
            print(json.dumps(res, indent=2))
        elif args.check == "drc01c":
            res = analyze_drc01c_rule_88d(args.gstr2b_itc, args.gstr3b_itc)
            print(json.dumps(res, indent=2))
        elif args.check == "interest":
            if not args.due_date or not args.pay_date:
                print("Error: --due-date and --pay-date (YYYY-MM-DD) are required for interest calculation.")
                sys.exit(1)
            res = calculate_section_50_interest(
                tax_amount=args.tax_due,
                due_date=args.due_date,
                payment_date=args.pay_date,
                is_wrongly_utilized_itc=args.wrong_itc
            )
            print(json.dumps(res, indent=2))

    # Rule 42
    elif args.command == "rule42":
        res = compute_rule42_reversal(
            total_input_tax=args.total_itc,
            t1_non_business=args.non_business,
            t2_exempt_exclusive=args.exempt_exclusive,
            t3_blocked_sec17_5=args.blocked,
            t4_taxable_exclusive=args.taxable_exclusive,
            exempt_turnover_e=args.exempt_turnover,
            total_turnover_f=args.total_turnover
        )
        print(json.dumps(res, indent=2))

    # Rule 43
    elif args.command == "rule43":
        res = compute_rule43_reversal(
            common_capital_goods_tc=args.capital_itc,
            exempt_turnover_e=args.exempt_turnover,
            total_turnover_f=args.total_turnover
        )
        print(json.dumps(res, indent=2))

    # Refund
    elif args.command == "refund":
        if args.type == "inverted":
            res = compute_inverted_duty_refund(
                turnover_inverted_supplies=args.inverted_turnover,
                adjusted_total_turnover=args.adjusted_turnover,
                net_itc_inputs=args.net_itc_inputs,
                net_itc_services=args.net_itc_services,
                tax_payable_on_inverted_supplies=args.tax_payable
            )
        else:
            res = compute_export_lut_refund(
                turnover_zero_rated_export=args.export_turnover,
                adjusted_total_turnover=args.adjusted_turnover,
                net_itc=args.net_itc_inputs
            )
        print(json.dumps(res, indent=2))

    # CMP-08
    elif args.command == "cmp08":
        res = compute_cmp08_quarterly(
            turnover=args.turnover,
            scheme_type=args.scheme,
            inward_rcm_value=args.rcm_val
        )
        print(json.dumps(res, indent=2))

    # TDS
    elif args.command == "tds":
        with open(args.contracts_file, "r", encoding="utf-8") as f:
            c_data = json.load(f)
        records = c_data if isinstance(c_data, list) else c_data.get("records", [])
        res = compute_gstr7_tds(records, deductor_gstin=args.deductor_gstin, fp=args.period)
        print(json.dumps(res, indent=2))

    # TCS
    elif args.command == "tcs":
        with open(args.supplies_file, "r", encoding="utf-8") as f:
            s_data = json.load(f)
        supplies = s_data if isinstance(s_data, list) else s_data.get("supplies", [])
        res = compute_gstr8_tcs(supplies, eco_gstin=args.eco_gstin, fp=args.period)
        print(json.dumps(res, indent=2))

    # Importers
    elif args.command == "import":
        with open(args.file, "r", encoding="utf-8", errors="ignore") as in_f:
            content = in_f.read()
            
        fmt = args.format
        if fmt == "tally-xml":
            parsed = parse_tally_xml(content)
        elif fmt == "tally-csv":
            parsed = parse_tally_csv(content)
        elif fmt == "zoho-csv":
            parsed = parse_zoho_csv(content)
        else:
            software_label = "Busy Accounting" if fmt == "busy" else ("Vyapar" if fmt == "vyapar" else ("Marg ERP" if fmt == "marg" else "Universal CSV"))
            parsed = parse_universal_csv(content, default_software=software_label)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as out_f:
                json.dump(parsed, out_f, indent=2)
            print(f"✅ Successfully parsed {len(parsed)} invoices from {fmt.upper()} to: {args.output}")
        else:
            print(json.dumps(parsed, indent=2))


    # IMS
    elif args.command == "ims":
        with open(args.actions_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        actions = data if isinstance(data, list) else data.get("actions", [])
        res = process_ims_actions(actions, current_period=args.period)
        print(json.dumps(res, indent=2))

    # Section 16(4)
    elif args.command == "sec16-4":
        res = check_section_16_4_time_limit(args.invoice_date, args.filing_date)
        print(json.dumps(res, indent=2))

    # ISD
    elif args.command == "isd":
        with open(args.config_file, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        res = compute_isd_distribution(
            head_office_gstin=cfg["head_office_gstin"],
            common_service_itc=cfg["common_service_itc"],
            recipient_branches=cfg["branches"]
        )
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
GST Forms & CA Compliance Hub.
Unified command-line interface for Indian Accountants, Tax Consultants, and CAs.
Supports:
- GSTR-1 Portal JSON Generation & Pre-Upload Audit
- GSTR-3B Computation, ITC Optimization & Cash Set-off Engine
- GSTR-9 / 9C Annual Books Reconciliation
- DRC-01B / DRC-01C Notice Risk Analyzer & Section 50 Interest Calculator
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


def main():
    parser = argparse.ArgumentParser(
        description="GST Forms Hub — Complete Indian Tax Accounting & CA Audit Suite"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available GST statutory modules")

    # 1. GSTR-1 Subparser
    p_gstr1 = subparsers.add_parser("gstr1", help="Generate or audit GSTR-1 return")
    p_gstr1.add_argument("sales_file", help="JSON file containing outward sales invoices")
    p_gstr1.add_argument("--gstin", required=True, help="Taxpayer 15-char GSTIN")
    p_gstr1.add_argument("--period", default="102026", help="Financial Period MMYYYY (default: 102026)")
    p_gstr1.add_argument("--output", help="Path to write GST Portal uploadable JSON file")
    p_gstr1.add_argument("--validate", action="store_true", help="Validate existing GSTR-1 JSON")

    # 2. GSTR-3B Subparser
    p_gstr3b = subparsers.add_parser("gstr3b", help="Compute GSTR-3B tax payment, ITC and cash challan")
    p_gstr3b.add_argument("--sales", required=True, help="JSON file of sales invoices")
    p_gstr3b.add_argument("--purchases", required=True, help="JSON file of purchase invoices")
    p_gstr3b.add_argument("--gstin", required=True, help="Taxpayer 15-char GSTIN")
    p_gstr3b.add_argument("--period", default="102026", help="Period MMYYYY")

    # 3. GSTR-9 / 9C Subparser
    p_gstr9 = subparsers.add_parser("gstr9", help="GSTR-9 / 9C Annual Reconciliation (Books vs Portal)")
    p_gstr9.add_argument("--config", required=True, help="JSON file with annual turnover, tax paid & ITC data")

    # 4. DRC & Notices Subparser
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


if __name__ == "__main__":
    main()

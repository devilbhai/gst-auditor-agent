"""
Unit Tests for Comprehensive GST Forms & CA Suite.
Runs with standard library unittest.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from gstr1_engine import build_gstr1_tables, audit_gstr1_portal_json
from gstr3b_engine import compute_gstr3b
from gstr9_engine import compute_gstr9_reconciliation
from notices_drc_engine import (
    calculate_section_50_interest,
    analyze_drc01b_rule_88c,
    analyze_drc01c_rule_88d
)


class TestGSTR1Engine(unittest.TestCase):
    def setUp(self):
        self.gstin = "27AAPFU0939F1ZV"
        self.sample_sales = [
            {
                "invoice_number": "INV-001",
                "invoice_date": "15-10-2026",
                "buyer_gstin": "27AAACW1234D1ZS",
                "place_of_supply": "27",
                "taxable_value": 50000.0,
                "tax_rate": 18.0,
                "cgst": 4500.0,
                "sgst": 4500.0,
                "igst": 0.0,
                "hsn_sac": "998313"
            },
            {
                "invoice_number": "INV-002",
                "invoice_date": "16-10-2026",
                "buyer_gstin": "",
                "place_of_supply": "29", # Inter-state B2CL (> 1 Lakh)
                "taxable_value": 150000.0,
                "tax_rate": 18.0,
                "cgst": 0.0,
                "sgst": 0.0,
                "igst": 27000.0,
                "hsn_sac": "8471"
            }
        ]

    def test_build_gstr1(self):
        g1 = build_gstr1_tables(self.sample_sales, gstin=self.gstin, fp="102026")
        self.assertEqual(g1["gstin"], self.gstin)
        self.assertEqual(len(g1["b2b"]), 1)
        self.assertEqual(len(g1["b2cl"]), 1)
        self.assertEqual(len(g1["hsn"]["data"]), 2)

    def test_audit_gstr1_portal_json(self):
        g1 = build_gstr1_tables(self.sample_sales, gstin=self.gstin, fp="102026")
        res = audit_gstr1_portal_json(g1)
        self.assertTrue(res["valid"])
        self.assertEqual(len(res["errors"]), 0)


class TestGSTR3BEngine(unittest.TestCase):
    def test_compute_gstr3b_and_setoff(self):
        sales = [
            {"taxable_value": 100000.0, "cgst": 9000.0, "sgst": 9000.0, "igst": 0.0, "place_of_supply": "27"}
        ]
        purchases = [
            {"taxable_value": 40000.0, "cgst": 3600.0, "sgst": 3600.0, "igst": 0.0, "item_description": "Office IT Cables"}
        ]
        res = compute_gstr3b(sales, purchases, gstin="27AAPFU0939F1ZV", fp="102026")
        
        # Gross liability = CGST 9000, SGST 9000
        # ITC available = CGST 3600, SGST 3600
        # Cash payable = CGST 5400, SGST 5400 -> Total cash 10800
        cash = res["table_6_1_tax_payment"]["cash_payable_pmt06"]
        self.assertEqual(cash["cgst"], 5400.0)
        self.assertEqual(cash["sgst"], 5400.0)
        self.assertEqual(cash["total_cash"], 10800.0)


class TestGSTR9Engine(unittest.TestCase):
    def test_annual_reconciliation(self):
        res = compute_gstr9_reconciliation(
            audited_pnl_turnover=10000000.0,
            gstr1_annual_turnover=9500000.0,
            gstr3b_annual_turnover=9500000.0,
            books_tax_payable={"igst": 0, "cgst": 900000, "sgst": 900000},
            gstr3b_tax_paid={"igst": 0, "cgst": 855000, "sgst": 855000},
            books_itc={"igst": 0, "cgst": 200000, "sgst": 200000},
            gstr3b_claimed_itc={"igst": 0, "cgst": 250000, "sgst": 250000},
            gstr2b_annual_itc={"igst": 0, "cgst": 200000, "sgst": 200000}
        )
        self.assertFalse(res["audit_summary"]["clean_audit"])
        self.assertGreater(res["audit_summary"]["total_statutory_exposure"], 0)


class TestNoticesAndInterest(unittest.TestCase):
    def test_drc01b_rule_88c(self):
        # Difference > 20%
        res = analyze_drc01b_rule_88c(gstr1_tax_liability=150000.0, gstr3b_tax_liability=100000.0)
        self.assertTrue(res["triggers_drc01b"])
        self.assertEqual(res["percent_difference"], 50.0)

    def test_drc01c_rule_88d(self):
        # 3B claimed ITC > 2B by 30%
        res = analyze_drc01c_rule_88d(gstr2b_itc=100000.0, gstr3b_claimed_itc=135000.0)
        self.assertTrue(res["triggers_drc01c"])

    def test_section_50_interest(self):
        res = calculate_section_50_interest(
            tax_amount=100000.0,
            due_date="2026-10-20",
            payment_date="2026-11-19" # 30 days delay
        )
        self.assertEqual(res["delay_days"], 30)
        self.assertEqual(res["interest_rate_percent"], 18.0)
        self.assertAlmostEqual(res["interest_amount"], round(100000 * 0.18 * 30 / 365, 2), places=1)


if __name__ == "__main__":
    unittest.main()

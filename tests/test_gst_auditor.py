"""
Unit Tests for GST Auditor Agent.
Runs with standard Python `python3 -m unittest`. Zero dependencies required.
"""

import unittest
import os
import sys

# Add scripts to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from gstin_validator import validate_gstin, calculate_checksum_char
from hsn_verifier import verify_hsn_sac
from gst_rules import (
    check_place_of_supply,
    check_eway_bill_compliance,
    check_einvoice_compliance,
    check_blocked_itc_risk
)
from itc_reconciler import reconcile_books_vs_gstr2b
from gst_auditor import audit_single_invoice, audit_invoices


class TestGSTINValidator(unittest.TestCase):
    def test_valid_gstin(self):
        res = validate_gstin("27AAPFU0939F1ZV")
        self.assertTrue(res["valid"])
        self.assertEqual(res["state_code"], "27")
        self.assertEqual(res["state_name"], "Maharashtra")
        self.assertEqual(res["pan"], "AAPFU0939F")

    def test_invalid_checksum(self):
        res = validate_gstin("27AAPFU0939F1ZO")
        self.assertFalse(res["valid"])
        self.assertIn("Checksum mismatch", res["reason"])

    def test_invalid_state_code(self):
        res = validate_gstin("95AAPFU0939F1ZV")
        self.assertFalse(res["valid"])
        self.assertIn("not a recognized GST state code", res["reason"])

    def test_invalid_length(self):
        res = validate_gstin("27AAPFU0939F1Z")
        self.assertFalse(res["valid"])
        self.assertIn("Expected 15 characters", res["reason"])


class TestHSNVerifier(unittest.TestCase):
    def test_valid_hsn_and_rate(self):
        res = verify_hsn_sac("998313", 18.0, turnover_crores=5.0)
        self.assertTrue(res["valid"])

    def test_invalid_gst_slab(self):
        res = verify_hsn_sac("8471", 13.5)
        self.assertFalse(res["valid"])
        self.assertTrue(any("not a recognized GST slab" in iss for iss in res["issues"]))

    def test_short_hsn_for_large_turnover(self):
        res = verify_hsn_sac("84", 18.0, turnover_crores=10.0)
        self.assertFalse(res["valid"])
        self.assertTrue(any("at least 6 digits" in iss for iss in res["issues"]))


class TestGSTRules(unittest.TestCase):
    def test_intra_state_correct(self):
        errs = check_place_of_supply(
            supplier_state="27",
            place_of_supply_state="27",
            cgst_amount=900.0,
            sgst_amount=900.0,
            igst_amount=0.0,
            tax_rate=18.0,
            taxable_value=10000.0
        )
        self.assertEqual(len(errs), 0)

    def test_intra_state_igst_violation(self):
        errs = check_place_of_supply(
            supplier_state="27",
            place_of_supply_state="27",
            cgst_amount=0.0,
            sgst_amount=0.0,
            igst_amount=1800.0,
            tax_rate=18.0,
            taxable_value=10000.0
        )
        self.assertTrue(any("cannot charge IGST" in e for e in errs))

    def test_inter_state_cgst_sgst_violation(self):
        errs = check_place_of_supply(
            supplier_state="27",
            place_of_supply_state="29",
            cgst_amount=900.0,
            sgst_amount=900.0,
            igst_amount=0.0,
            tax_rate=18.0,
            taxable_value=10000.0
        )
        self.assertTrue(any("cannot charge CGST" in e for e in errs))

    def test_eway_bill_goods_over_50k(self):
        res = check_eway_bill_compliance(
            invoice_value=75000.0,
            is_intra_state=False,
            state_code="27",
            eway_bill_number=None
        )
        self.assertFalse(res["compliant"])
        self.assertTrue(res["required"])

    def test_einvoice_rule_48_4(self):
        res = check_einvoice_compliance(
            turnover_crores=10.0,
            is_b2b=True,
            irn="3b4f6e1a8b9c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e"
        )
        self.assertTrue(res["compliant"])

    def test_blocked_itc_sec17_5(self):
        res = check_blocked_itc_risk("Annual Executive Gym Membership")
        self.assertTrue(res["blocked"])
        self.assertEqual(res["keyword_matched"], "gym membership")


class TestITCReconciler(unittest.TestCase):
    def test_books_vs_2b_matching(self):
        books = [
            {"supplier_gstin": "27AAPFU0939F1ZV", "invoice_number": "INV-101", "cgst": 90, "sgst": 90, "igst": 0},
            {"supplier_gstin": "27AAPFU0939F1ZV", "invoice_number": "INV-102", "cgst": 50, "sgst": 50, "igst": 0}
        ]
        gstr2b = [
            {"supplier_gstin": "27AAPFU0939F1ZV", "invoice_number": "INV-101", "cgst": 90, "sgst": 90, "igst": 0}
        ]
        res = reconcile_books_vs_gstr2b(books, gstr2b)
        self.assertEqual(res["summary"]["matched_count"], 1)
        self.assertEqual(res["summary"]["missing_in_2b_count"], 1)
        self.assertEqual(res["summary"]["at_risk_itc_amount"], 100.0)


if __name__ == "__main__":
    unittest.main()

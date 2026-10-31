"""
Unit Tests for 2026 Modern Mandates:
- GSTN Invoice Management System (IMS)
- Section 16(4) 30-Nov Statutory Cut-off
- Section 20 Mandatory ISD Distribution
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from ims_engine import check_section_16_4_time_limit, process_ims_actions, compute_isd_distribution


class Test2026Mandates(unittest.TestCase):
    def test_section_16_4_valid_within_deadline(self):
        # Invoice date: 15-Oct-2025 (FY 2025-26). Deadline: 30-Nov-2026.
        # Filing date: 20-Oct-2026 -> Valid!
        res = check_section_16_4_time_limit("2025-10-15", "2026-10-20")
        self.assertFalse(res["is_time_barred"])
        self.assertEqual(res["status"], "VALID_WITHIN_TIME_LIMIT")

    def test_section_16_4_time_barred(self):
        # Invoice date: 15-Oct-2024 (FY 2024-25). Deadline: 30-Nov-2025.
        # Filing date: 15-Dec-2025 -> Time barred!
        res = check_section_16_4_time_limit("2024-10-15", "2025-12-15")
        self.assertTrue(res["is_time_barred"])
        self.assertEqual(res["status"], "TIME_BARRED_INADMISSIBLE")
        self.assertEqual(res["days_exceeded"], 15)

    def test_ims_workflow(self):
        actions = [
            {"invoice_number": "INV-01", "supplier_gstin": "27AAPFU0939F1ZV", "action": "ACCEPT", "igst": 1000},
            {"invoice_number": "INV-02", "supplier_gstin": "27AAPFU0939F1ZV", "action": "PENDING", "igst": 500},
            {"invoice_number": "INV-03", "supplier_gstin": "27AAPFU0939F1ZV", "action": "REJECT", "igst": 300}
        ]
        res = process_ims_actions(actions, current_period="102026")
        s = res["summary"]
        self.assertEqual(s["accepted_count"], 1)
        self.assertEqual(s["pending_count"], 1)
        self.assertEqual(s["rejected_count"], 1)
        self.assertEqual(s["eligible_itc_routed_to_gstr2b"]["igst"], 1000.0)
        self.assertEqual(s["itc_held_in_ims_buffer"]["igst"], 500.0)

    def test_isd_distribution(self):
        ho = "27AAPFU0939F1ZV" # Maharashtra HO
        branches = [
            {"branch_gstin": "27AAACW1234D1ZS", "turnover": 4000000.0}, # MH branch (40%)
            {"branch_gstin": "29AABCU9603R1ZJ", "turnover": 6000000.0}  # Karnataka branch (60%)
        ]
        common_itc = {"cgst": 50000.0, "sgst": 50000.0, "igst": 0.0}
        res = compute_isd_distribution(ho, common_itc, branches)
        
        allocs = res["branch_allocations"]
        # MH branch gets 40% of CGST (20k) and SGST (20k)
        self.assertEqual(allocs[0]["distributed_itc"]["cgst"], 20000.0)
        self.assertEqual(allocs[0]["distributed_itc"]["sgst"], 20000.0)
        
        # KA branch gets 60% of (CGST+SGST = 100k) converted to IGST = 60,000
        self.assertEqual(allocs[1]["distributed_itc"]["igst"], 60000.0)
        self.assertEqual(allocs[1]["distributed_itc"]["cgst"], 0.0)


if __name__ == "__main__":
    unittest.main()

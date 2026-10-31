"""
Unit Tests for Advanced GST Modules & Accounting Software Adapters.
Covers:
- Rule 42 & Rule 43 Pro-rata Reversals
- Form RFD-01 Refund Engine (Inverted Duty & Export LUT)
- Form CMP-08 Composition Scheme
- GSTR-7 TDS & GSTR-8 TCS
- Tally Prime, Zoho Books, and Universal CSV Adapters
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from rule42_43_engine import compute_rule42_reversal, compute_rule43_reversal
from refund_engine import compute_inverted_duty_refund, compute_export_lut_refund
from composition_engine import compute_cmp08_quarterly
from tds_tcs_engine import compute_gstr7_tds, compute_gstr8_tcs
from adapters.tally_adapter import parse_tally_xml, parse_tally_csv
from adapters.zoho_adapter import parse_zoho_csv
from adapters.universal_adapter import parse_universal_csv


class TestRule42And43(unittest.TestCase):
    def test_rule42_reversal(self):
        # T=100000, T1=5000, T2=10000, T3=5000, T4=50000. C1=80000, C2=30000. E=200000, F=1000000 (20%)
        res = compute_rule42_reversal(
            total_input_tax=100000.0,
            t1_non_business=5000.0,
            t2_exempt_exclusive=10000.0,
            t3_blocked_sec17_5=5000.0,
            t4_taxable_exclusive=50000.0,
            exempt_turnover_e=200000.0,
            total_turnover_f=1000000.0,
            has_non_business_common_use=True
        )
        c = res["computed_credits"]
        self.assertEqual(c["credited_to_ledger_C1"], 80000.0)
        self.assertEqual(c["common_credit_C2"], 30000.0)
        # D1 = 20% of 30000 = 6000
        self.assertEqual(c["exempt_reversal_D1"], 6000.0)
        # D2 = 5% of 30000 = 1500
        self.assertEqual(c["non_business_reversal_D2"], 1500.0)
        self.assertEqual(c["total_reversal_required_in_3B_4B"], 7500.0)

    def test_rule43_capital_goods(self):
        res = compute_rule43_reversal(
            common_capital_goods_tc=60000.0,
            exempt_turnover_e=250000.0,
            total_turnover_f=1000000.0 # 25% exempt
        )
        # Tm = 60000 / 60 = 1000
        # Te = 25% of 1000 = 250
        self.assertEqual(res["computed"]["monthly_credit_Tm"], 1000.0)
        self.assertEqual(res["computed"]["monthly_reversal_Te_in_3B_4B"], 250.0)


class TestRefundEngine(unittest.TestCase):
    def test_inverted_duty_refund(self):
        res = compute_inverted_duty_refund(
            turnover_inverted_supplies=1000000.0,
            adjusted_total_turnover=1000000.0,
            net_itc_inputs=180000.0,
            net_itc_services=20000.0,
            tax_payable_on_inverted_supplies=50000.0
        )
        # Inputs weight = 180000/200000 = 90%
        # Tax deduction = 50000 * 0.9 = 45000
        # Max refund = 180000 - 45000 = 135000
        self.assertEqual(res["breakdown"]["maximum_eligible_refund"], 135000.0)

    def test_export_lut_refund(self):
        res = compute_export_lut_refund(
            turnover_zero_rated_export=500000.0,
            adjusted_total_turnover=1000000.0,
            net_itc=100000.0
        )
        # Ratio = 50% -> refund = 50,000
        self.assertEqual(res["maximum_eligible_refund"], 50000.0)


class TestCompositionEngine(unittest.TestCase):
    def test_cmp08_trader(self):
        res = compute_cmp08_quarterly(turnover=1000000.0, scheme_type="trader")
        self.assertEqual(res["table_1_outward_tax"]["rate_percent"], 1.0)
        self.assertEqual(res["table_4_net_tax_payable_cash"]["total_cash_challan"], 10000.0)

    def test_cmp08_restaurant(self):
        res = compute_cmp08_quarterly(turnover=500000.0, scheme_type="restaurant")
        self.assertEqual(res["table_1_outward_tax"]["rate_percent"], 5.0)
        self.assertEqual(res["table_4_net_tax_payable_cash"]["total_cash_challan"], 25000.0)


class TestTDSTCS(unittest.TestCase):
    def test_gstr7_tds(self):
        contracts = [
            {"supplier_gstin": "27AAPFU0939F1ZV", "contract_value": 300000.0, "taxable_amount": 100000.0, "place_of_supply": "27"},
            {"supplier_gstin": "27AAPFU0939F1ZV", "contract_value": 200000.0, "taxable_amount": 50000.0} # below 2.5L threshold
        ]
        res = compute_gstr7_tds(contracts, deductor_gstin="27AAACW1234D1ZS", fp="102026")
        self.assertEqual(res["total_suppliers_deducted"], 1)
        self.assertEqual(res["total_tds_liability"]["total_tds_deposit_pmt06"], 2000.0)

    def test_gstr8_tcs(self):
        supplies = [
            {"supplier_gstin": "27AAPFU0939F1ZV", "gross_supplies": 120000.0, "returned_supplies": 20000.0, "place_of_supply": "27"}
        ]
        # Net taxable = 100,000 -> 1% TCS = 1,000 (500 CGST + 500 SGST)
        res = compute_gstr8_tcs(supplies, eco_gstin="27AAACW1234D1ZS", fp="102026")
        self.assertEqual(res["total_tcs_liability"]["total_tcs_deposit"], 1000.0)


class TestAdapters(unittest.TestCase):
    def test_tally_xml_parser(self):
        xml_sample = """
        <ENVELOPE>
            <BODY>
                <DATA>
                    <TALLYMESSAGE>
                        <VOUCHER VOUCHERTYPENAME="Sales">
                            <VOUCHERNUMBER>INV-TALLY-01</VOUCHERNUMBER>
                            <DATE>20261015</DATE>
                            <PARTYGSTIN>27AAPFU0939F1ZV</PARTYGSTIN>
                            <PLACEOFSUPPLY>27</PLACEOFSUPPLY>
                            <ALLLEDGERENTRIES.LIST>
                                <LEDGERNAME>Sales Account</LEDGERNAME>
                                <AMOUNT>-50000.00</AMOUNT>
                            </ALLLEDGERENTRIES.LIST>
                            <ALLLEDGERENTRIES.LIST>
                                <LEDGERNAME>Output CGST</LEDGERNAME>
                                <AMOUNT>-4500.00</AMOUNT>
                            </ALLLEDGERENTRIES.LIST>
                            <ALLLEDGERENTRIES.LIST>
                                <LEDGERNAME>Output SGST</LEDGERNAME>
                                <AMOUNT>-4500.00</AMOUNT>
                            </ALLLEDGERENTRIES.LIST>
                        </VOUCHER>
                    </TALLYMESSAGE>
                </DATA>
            </BODY>
        </ENVELOPE>
        """
        invs = parse_tally_xml(xml_sample)
        self.assertEqual(len(invs), 1)
        self.assertEqual(invs[0]["invoice_number"], "INV-TALLY-01")
        self.assertEqual(invs[0]["taxable_value"], 50000.0)
        self.assertEqual(invs[0]["cgst"], 4500.0)

    def test_universal_csv_parser(self):
        csv_sample = """Invoice No,Date,Party GSTIN,Place of Supply,Taxable Amount,CGST,SGST,IGST,Total
INV-BUSY-101,15-10-2026,27AAPFU0939F1ZV,27,10000,900,900,0,11800
"""
        invs = parse_universal_csv(csv_sample, default_software="Busy Accounting")
        self.assertEqual(len(invs), 1)
        self.assertEqual(invs[0]["invoice_number"], "INV-BUSY-101")
        self.assertEqual(invs[0]["taxable_value"], 10000.0)
        self.assertEqual(invs[0]["invoice_total"], 11800.0)


if __name__ == "__main__":
    unittest.main()

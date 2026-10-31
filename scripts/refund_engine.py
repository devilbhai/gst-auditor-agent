"""
GST Refund Engine (Form RFD-01 & RFD-11 Export LUT).
Calculates statutory refunds under Section 54 of CGST Act read with Rule 89:
- Rule 89(5): Inverted Duty Structure Refund
- Rule 89(4): Zero-Rated Supply / Export under LUT without payment of IGST
- Rule 89(1): Excess Balance in Electronic Cash Ledger
"""

from typing import Dict, Any, Optional


def compute_inverted_duty_refund(
    turnover_inverted_supplies: float,
    adjusted_total_turnover: float,
    net_itc_inputs: float,
    net_itc_services: float,
    tax_payable_on_inverted_supplies: float
) -> Dict[str, Any]:
    """
    Computes maximum refund under Rule 89(5) for Inverted Duty Structure
    (as amended by Notification No. 14/2022-Central Tax).
    Formula:
    Refund = {(Turnover Inverted * Net ITC Inputs) / Adjusted Total Turnover}
             - {Tax Payable Inverted * (Net ITC Inputs / (Net ITC Inputs + Net ITC Services))}
    """
    inv_to = float(turnover_inverted_supplies)
    adj_to = float(adjusted_total_turnover)
    itc_inputs = float(net_itc_inputs)
    itc_services = float(net_itc_services)
    tax_payable = float(tax_payable_on_inverted_supplies)
    
    if adj_to <= 0:
        raise ValueError("Adjusted total turnover must be greater than zero.")
        
    itc_ratio = inv_to / adj_to
    itc_share_numerator = round(itc_ratio * itc_inputs, 2)
    
    total_itc = itc_inputs + itc_services
    input_weight = (itc_inputs / total_itc) if total_itc > 0 else 1.0
    tax_deduction = round(tax_payable * input_weight, 2)
    
    max_refund = max(0.0, round(itc_share_numerator - tax_deduction, 2))
    
    return {
        "statutory_section": "Section 54(3)(ii) read with Rule 89(5)",
        "refund_type": "Inverted Duty Structure",
        "inputs": {
            "turnover_inverted_supplies": inv_to,
            "adjusted_total_turnover": adj_to,
            "net_itc_on_inputs": itc_inputs,
            "net_itc_on_services": itc_services,
            "tax_payable_on_inverted": tax_payable
        },
        "breakdown": {
            "proportional_input_itc": itc_share_numerator,
            "adjusted_tax_payable_deduction": tax_deduction,
            "maximum_eligible_refund": max_refund
        },
        "action": "File Form GST RFD-01 under category 'Refund on account of ITC accumulated due to Inverted Tax Structure'."
    }


def compute_export_lut_refund(
    turnover_zero_rated_export: float,
    adjusted_total_turnover: float,
    net_itc: float
) -> Dict[str, Any]:
    """
    Computes refund of accumulated ITC for Zero-Rated Exports without payment of tax under LUT
    as per Rule 89(4) of CGST Rules 2017.
    Formula: Refund = (Turnover Zero-Rated * Net ITC) / Adjusted Total Turnover
    """
    exp_to = float(turnover_zero_rated_export)
    adj_to = float(adjusted_total_turnover)
    itc = float(net_itc)
    
    if adj_to <= 0:
        raise ValueError("Adjusted total turnover must be greater than zero.")
        
    export_ratio = min(1.0, exp_to / adj_to)
    eligible_refund = round(export_ratio * itc, 2)
    
    return {
        "statutory_section": "Section 54(3)(i) read with Rule 89(4)",
        "refund_type": "Zero-Rated Supplies (Exports) under LUT/Bond",
        "inputs": {
            "turnover_zero_rated_export": exp_to,
            "adjusted_total_turnover": adj_to,
            "net_itc_eligible": itc,
            "export_turnover_ratio": round(export_ratio, 4)
        },
        "maximum_eligible_refund": eligible_refund,
        "prerequisites": [
            "Valid Letter of Undertaking (LUT - Form RFD-11) for the current financial year",
            "Shipping Bill / Export Declaration with EGM verification",
            "Foreign Inward Remittance Certificate (FIRC) / BRC for services"
        ],
        "action": "File Form GST RFD-01 under category 'Refund of unutilized ITC on account of exports without payment of tax'."
    }

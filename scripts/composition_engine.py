"""
Composition Scheme Engine (CMP-08 & GSTR-4).
Computes quarterly tax liabilities under Section 10 and Section 10(2A) of CGST Act.
"""

from typing import Dict, Any, List


COMPOSITION_RATES = {
    "trader": {"rate": 1.0, "cgst": 0.5, "sgst": 0.5, "description": "Traders (1% of taxable turnover)"},
    "manufacturer": {"rate": 1.0, "cgst": 0.5, "sgst": 0.5, "description": "Manufacturers (1% of total turnover)"},
    "restaurant": {"rate": 5.0, "cgst": 2.5, "sgst": 2.5, "description": "Restaurant services (5% of total turnover)"},
    "service_provider": {"rate": 6.0, "cgst": 3.0, "sgst": 3.0, "description": "Service Providers Sec 10(2A) (6% of turnover)"}
}


def compute_cmp08_quarterly(
    turnover: float,
    scheme_type: str,
    inward_rcm_value: float = 0.0,
    rcm_tax_rate: float = 18.0,
    interest: float = 0.0
) -> Dict[str, Any]:
    """
    Computes Form CMP-08 quarterly payment challan.
    Taxpayers in composition scheme cannot collect tax from customers or claim ITC.
    """
    st = scheme_type.lower().strip()
    if st not in COMPOSITION_RATES:
        raise ValueError(f"Invalid scheme_type '{scheme_type}'. Must be one of: {list(COMPOSITION_RATES.keys())}")
        
    rate_info = COMPOSITION_RATES[st]
    to_val = float(turnover)
    
    # Tax on outward supplies
    tax_cgst = round(to_val * (rate_info["cgst"] / 100.0), 2)
    tax_sgst = round(to_val * (rate_info["sgst"] / 100.0), 2)
    
    # Inward supplies liable to reverse charge (RCM)
    rcm_val = float(inward_rcm_value)
    rcm_cgst = round(rcm_val * ((rcm_tax_rate / 2.0) / 100.0), 2)
    rcm_sgst = round(rcm_val * ((rcm_tax_rate / 2.0) / 100.0), 2)
    
    # Total payable in CASH (no ITC permissible under Sec 10(4))
    total_cgst = round(tax_cgst + rcm_cgst + (interest / 2.0), 2)
    total_sgst = round(tax_sgst + rcm_sgst + (interest / 2.0), 2)
    total_payable = round(total_cgst + total_sgst, 2)
    
    return {
        "form": "CMP-08",
        "scheme": rate_info["description"],
        "turnover": to_val,
        "table_1_outward_tax": {
            "rate_percent": rate_info["rate"],
            "cgst": tax_cgst,
            "sgst": tax_sgst
        },
        "table_2_inward_rcm_tax": {
            "inward_rcm_value": rcm_val,
            "cgst": rcm_cgst,
            "sgst": rcm_sgst
        },
        "table_3_interest": interest,
        "table_4_net_tax_payable_cash": {
            "cgst": total_cgst,
            "sgst": total_sgst,
            "total_cash_challan": total_payable
        },
        "compliance_notes": [
            "Input Tax Credit (ITC) CANNOT be claimed by composition dealers.",
            "Tax CANNOT be collected from buyers (must write 'Composition taxable person, not eligible to collect tax on supplies' on bill of supply).",
            "Inter-state outward supplies are strictly prohibited under Section 10(2)(c)."
        ]
    }

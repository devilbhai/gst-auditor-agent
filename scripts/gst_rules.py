"""
Indian GST Statutory Business Rules Engine.
Implements Rule 138 (E-Way Bill), Rule 48(4) (E-Invoicing IRN),
Section 7/8 IGST Act (Place of Supply), and Section 17(5) Blocked ITC.
"""

from typing import Dict, Any, List

# States with higher intra-state E-Way Bill threshold (₹1,00,000 instead of ₹50,000)
HIGH_THRESHOLD_INTRA_EWAY_STATES = {"07", "27", "10", "19", "24"} # Delhi, Maharashtra, Bihar, WB, Gujarat

# Blocked ITC categories under Section 17(5) CGST Act
BLOCKED_ITC_KEYWORDS = [
    "motor car", "passenger vehicle", "car rental", "food and beverages",
    "catering", "club membership", "gym membership", "beauty treatment",
    "cosmetic surgery", "life insurance", "health insurance for employees",
    "personal consumption", "gift", "free sample", "lost or stolen"
]


def check_place_of_supply(
    supplier_state: str,
    place_of_supply_state: str,
    cgst_amount: float,
    sgst_amount: float,
    igst_amount: float,
    tax_rate: float,
    taxable_value: float
) -> List[str]:
    """
    Validates tax split based on Supplier State vs Place of Supply.
    - Same State -> INTRA-STATE: CGST and SGST must be equal (50% each), IGST = 0.
    - Different State -> INTER-STATE: IGST only, CGST = 0, SGST = 0.
    """
    violations = []
    supplier_st = str(supplier_state).zfill(2)
    pos_st = str(place_of_supply_state).zfill(2)
    
    is_intra_state = (supplier_st == pos_st)
    expected_total_tax = round(taxable_value * (tax_rate / 100.0), 2)
    
    if is_intra_state:
        # Must be CGST + SGST
        if igst_amount > 0.05:
            violations.append(
                f"[CRITICAL - TAX JURISDICTION ERROR] Intra-state transaction (Supplier State {supplier_st} == POS {pos_st}) "
                f"cannot charge IGST (₹{igst_amount:.2f}). Must charge equal CGST and SGST."
            )
        # Check equal split between CGST and SGST
        if abs(cgst_amount - sgst_amount) > 1.0:
            violations.append(
                f"[MATH MISMATCH] Intra-state tax must be split equally between CGST and SGST. "
                f"Found CGST=₹{cgst_amount:.2f}, SGST=₹{sgst_amount:.2f} (diff > ₹1.00)."
            )
        # Verify rate split
        expected_half = round(expected_total_tax / 2.0, 2)
        if abs(cgst_amount - expected_half) > 1.0:
            violations.append(
                f"[CALCULATION MISMATCH] Expected CGST ₹{expected_half:.2f} ({tax_rate/2}%), found ₹{cgst_amount:.2f}."
            )
    else:
        # Must be IGST
        if cgst_amount > 0.05 or sgst_amount > 0.05:
            violations.append(
                f"[CRITICAL - TAX JURISDICTION ERROR] Inter-state transaction (Supplier State {supplier_st} != POS {pos_st}) "
                f"cannot charge CGST (₹{cgst_amount:.2f}) or SGST (₹{sgst_amount:.2f}). Must charge IGST only."
            )
        if abs(igst_amount - expected_total_tax) > 1.0:
            violations.append(
                f"[CALCULATION MISMATCH] Expected IGST ₹{expected_total_tax:.2f} ({tax_rate}%), found ₹{igst_amount:.2f}."
            )
            
    return violations


def check_eway_bill_compliance(
    invoice_value: float,
    is_intra_state: bool,
    state_code: str,
    eway_bill_number: str = None,
    is_service: bool = False
) -> Dict[str, Any]:
    """
    Checks Rule 138 E-Way Bill requirement.
    Services are exempt from E-Way bill.
    Goods consignments > ₹50,000 (or state exemption) mandate E-Way Bill.
    """
    if is_service:
        return {"required": False, "compliant": True, "note": "Services are exempt from E-Way Bill."}
        
    threshold = 100000.0 if (is_intra_state and state_code in HIGH_THRESHOLD_INTRA_EWAY_STATES) else 50000.0
    
    if invoice_value > threshold:
        has_eway = bool(eway_bill_number and len(str(eway_bill_number).strip()) >= 12)
        return {
            "required": True,
            "threshold": threshold,
            "invoice_value": invoice_value,
            "eway_bill_number": eway_bill_number,
            "compliant": has_eway,
            "issue": None if has_eway else (
                f"[COMPLIANCE RISK - RULE 138] Consignment value ₹{invoice_value:,.2f} exceeds threshold ₹{threshold:,.2f}. "
                f"E-Way Bill is mandatory prior to goods dispatch. Missing or invalid E-Way Bill Number."
            )
        }
        
    return {
        "required": False,
        "threshold": threshold,
        "invoice_value": invoice_value,
        "compliant": True,
        "note": f"Consignment value ₹{invoice_value:,.2f} is within ₹{threshold:,.2f} limit."
    }


def check_einvoice_compliance(
    turnover_crores: float,
    is_b2b: bool,
    irn: str = None,
    signed_qr: bool = False
) -> Dict[str, Any]:
    """
    Checks Rule 48(4) E-Invoicing mandate (Threshold > ₹5 Crore).
    Any B2B invoice issued without IRN and QR code by eligible taxpayer is invalid in the eyes of law.
    """
    if not is_b2b:
        return {"required": False, "compliant": True, "note": "B2C invoices exempt from IRN mandate."}
        
    if turnover_crores >= 5.0:
        has_irn = bool(irn and len(str(irn).strip()) == 64)
        return {
            "required": True,
            "compliant": has_irn,
            "irn": irn,
            "issue": None if has_irn else (
                f"[LEGAL INVALIDITY - RULE 48(4)] Aggregate turnover is ₹{turnover_crores} Cr (> ₹5 Cr mandate). "
                f"B2B invoices without a 64-character Invoice Reference Number (IRN) generated via IRP "
                f"are deemed null and void; buyer cannot claim Input Tax Credit."
            )
        }
        
    return {
        "required": False,
        "compliant": True,
        "note": f"Turnover ₹{turnover_crores} Cr is below the ₹5 Cr mandatory E-Invoicing threshold."
    }


def check_blocked_itc_risk(item_description: str) -> Dict[str, Any]:
    """Checks whether an expense item might be blocked from ITC claims under Section 17(5)."""
    desc_lower = str(item_description).lower()
    for keyword in BLOCKED_ITC_KEYWORDS:
        if keyword in desc_lower:
            return {
                "blocked": True,
                "keyword_matched": keyword,
                "warning": (
                    f"[ITC INELIGIBILITY - SEC 17(5)] Item '{item_description}' matches blocked category '{keyword}'. "
                    f"Input Tax Credit cannot be claimed unless specific business exemption applies."
                )
            }
    return {"blocked": False}

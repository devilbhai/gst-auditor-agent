"""
TDS (GSTR-7) & TCS (GSTR-8) Engine.
Computes deductions and collections under Section 51 and Section 52 of CGST Act.
"""

from typing import Dict, Any, List


def compute_gstr7_tds(
    contract_records: List[Dict[str, Any]],
    deductor_gstin: str,
    fp: str
) -> Dict[str, Any]:
    """
    Computes Form GSTR-7 for Tax Deducted at Source (TDS) under Section 51.
    Mandatory when total value of supply under a contract exceeds ₹2,50,000.
    Rate: 2% (1% CGST + 1% SGST or 2% IGST).
    """
    deductor_state = deductor_gstin[:2]
    tds_entries = []
    total_taxable = 0.0
    total_tds = {"igst": 0.0, "cgst": 0.0, "sgst": 0.0}

    for rec in contract_records:
        supp_gstin = rec.get("supplier_gstin", "").strip().upper()
        supp_state = supp_gstin[:2] if len(supp_gstin) >= 2 else deductor_state
        pos = str(rec.get("place_of_supply") or supp_state).zfill(2)
        contract_val = float(rec.get("contract_value", 0.0))
        taxable_amt = float(rec.get("taxable_amount", 0.0))
        
        # Section 51 threshold check: Contract value must exceed ₹2.5 Lakhs
        if contract_val <= 250000.0:
            continue
            
        total_taxable += taxable_amt
        is_inter = (deductor_state != pos)
        
        if is_inter:
            tds_igst = round(taxable_amt * 0.02, 2)
            tds_cgst = 0.0
            tds_sgst = 0.0
        else:
            tds_igst = 0.0
            tds_cgst = round(taxable_amt * 0.01, 2)
            tds_sgst = round(taxable_amt * 0.01, 2)

        total_tds["igst"] += tds_igst
        total_tds["cgst"] += tds_cgst
        total_tds["sgst"] += tds_sgst

        tds_entries.append({
            "supplier_gstin": supp_gstin,
            "contract_value": contract_val,
            "taxable_amount": taxable_amt,
            "place_of_supply": pos,
            "tds_deducted": {
                "igst": tds_igst,
                "cgst": tds_cgst,
                "sgst": tds_sgst,
                "total": round(tds_igst + tds_cgst + tds_sgst, 2)
            }
        })

    return {
        "form": "GSTR-7",
        "deductor_gstin": deductor_gstin,
        "financial_period": fp,
        "total_suppliers_deducted": len(tds_entries),
        "total_taxable_value": round(total_taxable, 2),
        "total_tds_liability": {
            "igst": round(total_tds["igst"], 2),
            "cgst": round(total_tds["cgst"], 2),
            "sgst": round(total_tds["sgst"], 2),
            "total_tds_deposit_pmt06": round(total_tds["igst"] + total_tds["cgst"] + total_tds["sgst"], 2)
        },
        "records": tds_entries
    }


def compute_gstr8_tcs(
    supplies_data: List[Dict[str, Any]],
    eco_gstin: str,
    fp: str
) -> Dict[str, Any]:
    """
    Computes Form GSTR-8 for Tax Collected at Source (TCS) by E-Commerce Operators under Section 52.
    Rate: 1% (0.5% CGST + 0.5% SGST or 1% IGST) on Net Taxable Supplies (Gross - Returns).
    """
    eco_state = eco_gstin[:2]
    supplier_tcs = {}
    total_net_val = 0.0
    total_tcs = {"igst": 0.0, "cgst": 0.0, "sgst": 0.0}

    for sup in supplies_data:
        sgstin = sup.get("supplier_gstin", "").strip().upper()
        gross_val = float(sup.get("gross_supplies", 0.0))
        returned_val = float(sup.get("returned_supplies", 0.0))
        net_val = max(0.0, gross_val - returned_val)
        pos = str(sup.get("place_of_supply") or eco_state).zfill(2)
        
        is_inter = (eco_state != pos)
        if is_inter:
            tcs_igst = round(net_val * 0.01, 2)
            tcs_cgst = 0.0
            tcs_sgst = 0.0
        else:
            tcs_igst = 0.0
            tcs_cgst = round(net_val * 0.005, 2)
            tcs_sgst = round(net_val * 0.005, 2)

        total_net_val += net_val
        total_tcs["igst"] += tcs_igst
        total_tcs["cgst"] += tcs_cgst
        total_tcs["sgst"] += tcs_sgst

        supplier_tcs[sgstin] = {
            "supplier_gstin": sgstin,
            "gross_value": gross_val,
            "returned_value": returned_val,
            "net_taxable_value": net_val,
            "tcs_collected": {
                "igst": tcs_igst,
                "cgst": tcs_cgst,
                "sgst": tcs_sgst,
                "total": round(tcs_igst + tcs_cgst + tcs_sgst, 2)
            }
        }

    return {
        "form": "GSTR-8",
        "eco_gstin": eco_gstin,
        "financial_period": fp,
        "total_registered_sellers": len(supplier_tcs),
        "total_net_value_of_supplies": round(total_net_val, 2),
        "total_tcs_liability": {
            "igst": round(total_tcs["igst"], 2),
            "cgst": round(total_tcs["cgst"], 2),
            "sgst": round(total_tcs["sgst"], 2),
            "total_tcs_deposit": round(total_tcs["igst"] + total_tcs["cgst"] + total_tcs["sgst"], 2)
        },
        "seller_wise_details": list(supplier_tcs.values())
    }

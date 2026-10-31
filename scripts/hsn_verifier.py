"""
HSN / SAC Code Verifier & Rate Validator.
Validates HSN code length, format, standard GST tax slabs, and known item tax rates.
"""

from typing import Dict, Any, Optional

# Valid GST Slabs in India
VALID_GST_RATES = {0.0, 0.1, 0.25, 1.5, 3.0, 5.0, 12.0, 18.0, 28.0}

# Common HSN & SAC codes benchmark catalog (can be extended or fetched via Swipe/GSTN API)
COMMON_HSN_CATALOG = {
    # Services (SAC starting with 99)
    "9983": {"description": "IT and Professional, Technical and Business Services", "standard_rate": 18.0, "type": "SAC"},
    "998311": {"description": "Management consulting services", "standard_rate": 18.0, "type": "SAC"},
    "998313": {"description": "IT design and development services", "standard_rate": 18.0, "type": "SAC"},
    "998314": {"description": "IT infrastructure and network management", "standard_rate": 18.0, "type": "SAC"},
    "998319": {"description": "Other information technology services", "standard_rate": 18.0, "type": "SAC"},
    "9982": {"description": "Legal and accounting services (RCM applies to individual advocates)", "standard_rate": 18.0, "type": "SAC", "rcm_eligible": True},
    "9965": {"description": "Goods Transport Agency (GTA) Services", "standard_rate": 5.0, "type": "SAC", "rcm_eligible": True},
    "9967": {"description": "Supporting services in transport, storage and courier", "standard_rate": 18.0, "type": "SAC"},
    "9973": {"description": "Leasing or rental services concerning machinery", "standard_rate": 18.0, "type": "SAC"},
    "9954": {"description": "Construction services", "standard_rate": 18.0, "type": "SAC"},

    # Goods (HSN)
    "8471": {"description": "Automatic data processing machines (Laptops, Computers)", "standard_rate": 18.0, "type": "HSN"},
    "8517": {"description": "Smartphones and telephone sets", "standard_rate": 18.0, "type": "HSN"},
    "8504": {"description": "Electrical transformers, static converters (Chargers/Adapters)", "standard_rate": 18.0, "type": "HSN"},
    "8528": {"description": "Monitors and Projectors", "standard_rate": 18.0, "type": "HSN"},
    "4820": {"description": "Registers, account books, note books, order books", "standard_rate": 12.0, "type": "HSN"},
    "4901": {"description": "Printed books, brochures, leaflets", "standard_rate": 0.0, "type": "HSN"},
    "1209": {"description": "Seeds, fruit and spores, of a kind used for sowing (Agri seeds)", "standard_rate": 0.0, "type": "HSN"},
    "3101": {"description": "Animal or vegetable fertilizers", "standard_rate": 5.0, "type": "HSN"},
    "3102": {"description": "Mineral or chemical fertilizers, nitrogenous", "standard_rate": 5.0, "type": "HSN"},
    "3808": {"description": "Insecticides, rodenticides, fungicides, herbicides", "standard_rate": 18.0, "type": "HSN"},
    "8703": {"description": "Motor cars and motor vehicles for transport", "standard_rate": 28.0, "type": "HSN", "blocked_itc": True},
}


def verify_hsn_sac(hsn_code: Optional[str], rate: float, turnover_crores: float = 5.0) -> Dict[str, Any]:
    """
    Validates HSN/SAC code format, minimum digit requirement based on turnover,
    valid GST tax slab, and compares with catalog standard rates if known.
    """
    issues = []
    normalized_code = str(hsn_code).strip() if hsn_code else ""
    
    # 1. Check if HSN code is provided
    if not normalized_code:
        return {
            "valid": False,
            "hsn_code": "",
            "issues": ["HSN/SAC code is missing. Mandatory on all B2B and export invoices."]
        }
        
    # Remove any non-alphanumeric (like dots or spaces)
    cleaned_code = "".join(c for c in normalized_code if c.isdigit())
    
    # 2. Check digit length
    # Rule: Turnover <= 5 Cr -> min 4 digits for B2B; Turnover > 5 Cr -> min 6 digits. Export invoices -> 8 digits.
    min_digits = 6 if turnover_crores > 5.0 else 4
    if len(cleaned_code) < min_digits:
        issues.append(
            f"HSN/SAC code '{cleaned_code}' has only {len(cleaned_code)} digits. "
            f"Businesses with turnover > ₹{turnover_crores} Cr require at least {min_digits} digits."
        )
        
    # 3. Check rate against standard Indian GST slabs
    rounded_rate = round(float(rate), 2)
    if rounded_rate not in VALID_GST_RATES:
        issues.append(
            f"GST rate {rounded_rate}% is not a recognized GST slab. "
            f"Valid slabs are: {sorted(list(VALID_GST_RATES))}%"
        )
        
    # 4. Check known catalog benchmark
    catalog_match = None
    for prefix_len in [6, 4, 2]:
        sub = cleaned_code[:prefix_len]
        if sub in COMMON_HSN_CATALOG:
            catalog_match = COMMON_HSN_CATALOG[sub]
            break
            
    if catalog_match:
        expected_rate = catalog_match.get("standard_rate")
        if expected_rate is not None and abs(expected_rate - rounded_rate) > 0.01:
            issues.append(
                f"Rate mismatch for HSN/SAC {cleaned_code} ({catalog_match.get('description')}): "
                f"Invoice applied {rounded_rate}%, standard benchmark rate is {expected_rate}%."
            )
            
    return {
        "valid": len(issues) == 0,
        "hsn_code": cleaned_code,
        "rate": rounded_rate,
        "catalog_info": catalog_match,
        "issues": issues
    }

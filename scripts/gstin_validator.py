"""
GSTIN Validator - Algorithmic validation for Indian Goods & Services Tax Identification Number.
Verifies format, state code, PAN structure, and calculates Mod-36 checksum.
"""

import re
from typing import Dict, Any, Optional

CODE_POINT_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")

# Official State Codes defined by GST Council
STATE_CODES = {
    "01": "Jammu & Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "25": "Daman and Diu (Legacy)",
    "26": "Dadra & Nagar Haveli and Daman & Diu",
    "27": "Maharashtra",
    "28": "Andhra Pradesh (Old)",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman & Nicobar Islands",
    "36": "Telangana",
    "37": "Andhra Pradesh (New)",
    "38": "Ladakh",
    "97": "Other Territory",
    "99": "Centre Jurisdiction / Special"
}


def calculate_checksum_char(gstin_14: str) -> str:
    """Calculates the 15th check digit for the first 14 characters using Mod-36 Luhn variant."""
    factor = 1
    total = 0
    mod = len(CODE_POINT_CHARS)
    
    for char in gstin_14:
        code_index = CODE_POINT_CHARS.find(char)
        if code_index < 0:
            raise ValueError(f"Invalid character '{char}' in GSTIN string.")
        
        digit = factor * code_index
        digit = (digit // mod) + (digit % mod)
        total += digit
        factor = 2 if factor == 1 else 1
        
    remainder = total % mod
    check_code_index = (mod - remainder) % mod
    return CODE_POINT_CHARS[check_code_index]


def validate_gstin(gstin: Optional[str]) -> Dict[str, Any]:
    """
    Validates a 15-character Indian GSTIN.
    Returns details on validity, state, PAN, and specific error reason if invalid.
    """
    if not gstin or not isinstance(gstin, str):
        return {
            "valid": False,
            "gstin": gstin,
            "reason": "GSTIN is missing or empty"
        }
        
    clean_gstin = gstin.strip().upper()
    
    if len(clean_gstin) != 15:
        return {
            "valid": False,
            "gstin": clean_gstin,
            "reason": f"Expected 15 characters, got {len(clean_gstin)}"
        }
        
    if not GSTIN_REGEX.match(clean_gstin):
        return {
            "valid": False,
            "gstin": clean_gstin,
            "reason": "Does not conform to Indian GSTIN regex pattern (2 digits + 10 char PAN + 1 entity + 'Z' + 1 checksum)"
        }
        
    state_code = clean_gstin[:2]
    if state_code not in STATE_CODES:
        return {
            "valid": False,
            "gstin": clean_gstin,
            "state_code": state_code,
            "reason": f"State code '{state_code}' is not a recognized GST state code"
        }
        
    expected_check_char = calculate_checksum_char(clean_gstin[:14])
    if clean_gstin[14] != expected_check_char:
        return {
            "valid": False,
            "gstin": clean_gstin,
            "state_code": state_code,
            "state_name": STATE_CODES[state_code],
            "pan": clean_gstin[2:12],
            "reason": f"Checksum mismatch: 15th character is '{clean_gstin[14]}', expected '{expected_check_char}'"
        }
        
    return {
        "valid": True,
        "gstin": clean_gstin,
        "state_code": state_code,
        "state_name": STATE_CODES[state_code],
        "pan": clean_gstin[2:12],
        "entity_number": clean_gstin[12],
        "reason": "Valid GSTIN format and checksum"
    }

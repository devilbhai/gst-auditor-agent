# Comprehensive Indian GST Statutory Rules & Compliance Reference

## 1. Goods and Services Tax Identification Number (GSTIN)
A 15-character alphanumeric code structured as follows:
- **Digits 1–2**: 2-digit State Code (as per Census 2011). E.g., `27` for Maharashtra, `24` for Gujarat, `07` for Delhi, `29` for Karnataka.
- **Digits 3–12**: 10-character Permanent Account Number (PAN) of the business entity.
- **Digit 13**: Entity code representing the number of registrations under the same PAN within the same state (1-9, followed by A-Z).
- **Digit 14**: Default character 'Z'.
- **Digit 15**: Check digit derived mathematically from the first 14 characters using the **Mod-36 Luhn variant** algorithm.

## 2. Place of Supply & Tax Type Allocation
- **Intra-State Supply** (Section 8 of the IGST Act):
  - Location of Supplier and Place of Supply are in the same State or Union Territory.
  - Taxes charged: **CGST + SGST/UTGST** in equal proportions (50% each).
  - IGST must be ZERO. Charging IGST is an unlawful jurisdiction levy.
- **Inter-State Supply** (Section 7 of the IGST Act):
  - Location of Supplier and Place of Supply are in different States or Union Territories.
  - Taxes charged: **IGST** only.
  - CGST and SGST must be ZERO.

## 3. E-Way Bill Regulations (Rule 138)
- Every registered person who causes movement of goods of consignment value exceeding ₹50,000 must generate an e-Way Bill before dispatch.
- **Exceptions & State Variations**:
  - Intra-state movement within Delhi, Maharashtra, West Bengal, Bihar, and Gujarat has an elevated exemption threshold of ₹1,00,000 for specific classes of goods.
  - Services (SAC starting with 99) are exempt from E-Way bills.

## 4. E-Invoicing / IRN Mandate (Rule 48(4))
- Registered taxpayers whose aggregate turnover in any preceding financial year from 2017-18 onward exceeds **₹5 Crore** are mandated to generate e-Invoices with a 64-character Invoice Reference Number (IRN) and signed QR code from the Invoice Registration Portal (IRP).
- Any B2B invoice issued without an IRN by such taxpayers is legally deemed null and void, disabling the buyer from claiming Input Tax Credit (ITC).

## 5. Blocked Input Tax Credit (Section 17(5) of CGST Act)
Input Tax Credit shall NOT be available in respect of:
1. Motor vehicles for transportation of persons with seating capacity $\le 13$ persons (unless used for further supply, passenger transportation, or driving school training).
2. Food and beverages, outdoor catering, beauty treatment, health services, cosmetic surgery.
3. Club, health and fitness centre membership fees.
4. Travel benefits extended to employees on vacation.
5. Goods lost, stolen, destroyed, written off, or disposed of by way of gift or free samples.

# CustomsGuard Compliance Audit Report

**Shipment ID**: SHP-2026-0089  
**Generated At**: 2026-09-27T12:00:00Z  
**Verdict**: NON_COMPLIANT_HIGH_RISK

### Executive Summary

- **Importer**: PT Medika Nusantara Sejahtera
- **Destination Port**: Tanjung Perak, Surabaya (IDTPS)
- **Container Count**: 3
- **Container Detention Risk**: YES
- **Total Duty Shortfall**: $0.00 USD
- **Estimated Daily Demurrage**: $1,050.00 USD / day ($350.00/day \* 3 containers)

### Critical Discrepancies & Regulatory Violations

1. **Declared HS Code Mismatch**: Declared HS `8471.50` (Computing processing units) conflicts with matched official HS `9018.12` (Ultrasonic scanning apparatus).
2. **Missing Mandatory Regulatory Import License**: Cargo requires **Distribution License (Izin Edar Alat Kesehatan / Kemenkes RI)** prior to customs clearance.

### Itemized Audit Findings

| Item ID | Declared Description                         | Declared HS | Matched HS | Declared Duty | Official Duty | Shortfall (USD) | Restricted | Mandatory Permits                |
| :-----: | :------------------------------------------- | :---------: | :--------: | :-----------: | :-----------: | :-------------: | :--------: | :------------------------------- |
|    1    | Siemens Acuson Ultrasound Diagnostic Scanner |   8471.50   |  9018.12   |     0.0%      |     0.0%      |      $0.00      |    Yes     | Kemenkes RI Distribution License |

### Automated Actions Taken

- Multi-container demurrage risk evaluated: $1,050.00 USD per day across 3 containers.
- Audit dossier saved to disk.
- Urgent detention alert queued in Mailpit (`http://localhost:8025`).

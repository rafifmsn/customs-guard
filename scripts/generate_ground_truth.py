#!/usr/bin/env python3
"""Generates the 50-item Ground Truth Customs Tariff Benchmark dataset."""

import json
import os

ITEMS_DATA = [
    ("Apple iPhone 15 Pro Max 256GB Dual SIM Smartphone", "8517.13"),
    ("Dell Latitude 5540 Laptop 15.6 inch Core i7 16GB RAM", "8471.30"),
    ("Siemens Acuson Freestyle Ultrasound Probe System", "9018.12"),
    ("Submarine Armored Optical Fiber Cable Single Mode 48 Core", "8544.70"),
    ("Nike Canvas Running Shoes with Rubber Soles", "6404.11"),
    ("Rotary Screw Industrial Air Compressor 500L 10 Bar", "8414.80"),
    ("Cisco Catalyst 9300 48-Port Network Switch Router", "8517.62"),
    ("Rechargeable Lithium-ion Battery Pack 48V 100Ah", "8507.60"),
    ("Split Wall Mounted Air Conditioner 1.5 PK Inverter", "8415.10"),
    ("Paracetamol Oral Suspension 120mg/5ml Pediatric Formulation", "3004.90"),
    ("Chocolate Coated Sweet Biscuits in Retail Pack 200g", "1905.31"),
    ("Enterprise Server Rack 2U Intel Xeon Scalable Dual Socket", "8471.50"),
    ("Switching Power Supply Adapter 24V 10A DC Output", "8504.40"),
    ("LED Backlit LCD Computer Monitor 27 Inch 4K UHD", "8528.52"),
    ("Digital Infrared Surveillance Camera 4K Dome", "8525.89"),
    ("Polypropylene Polymer Granules Injection Grade", "3902.10"),
    ("Seamless Stainless Steel Industrial Hydraulic Pipes", "7304.41"),
    ("Automotive Disc Brake Pad Set Front Axle", "8708.30"),
    ("Automatic Hemodialysis Blood Filtration Machine", "9018.90"),
    ("Electric Motor Three Phase Induction 15kW", "8501.52"),
    ("Centrifugal Water Pump Impeller Assembly Cast Iron", "8413.70"),
    ("Monolithic Integrated Circuit Microcontroller ARM Cortex-M4", "8542.31"),
    ("N95 Medical Protective Face Mask Particulate Respirator", "6307.90"),
    ("Unroasted Decaffeinated Arabica Green Coffee Beans", "0901.12"),
    ("Refined Palm Olein Cooking Oil Fractionated", "1511.90"),
    ("Hydraulic Excavator Crawler Track Shoe Link", "8431.49"),
    ("Pneumatic Radial Passenger Car Tires Tubeless 205/55R16", "4011.10"),
    ("Photovoltaic Solar Panel Module Monocrystalline 550W", "8541.43"),
    ("Industrial Robotic Arm 6-Axis Welding Automation", "8479.50"),
    ("Dental Examination Chair Unit with LED Operating Light", "9018.49"),
    ("Diagnostic Magnetic Resonance Imaging MRI System Superconducting", "9018.13"),
    ("Frozen Boneless Beef Meat Cuts Vacuum Packed", "0202.30"),
    ("Synthetic Lubricating Motor Oil 5W-30 Fully Synthetic", "2710.19"),
    ("Solid State Drive SSD 2TB NVMe M.2 PCIe 4.0", "8471.70"),
    ("Wireless Bluetooth Audio Headset Noise Cancelling", "8518.30"),
    ("Laboratory Analytical Electronic Precision Balance 0.1mg", "9016.00"),
    ("Thermal Receipt Printer Direct Thermal 80mm USB Ethernet", "8443.32"),
    ("Corrugated Paperboard Packaging Cartons Folding Box", "4819.10"),
    ("Extruded Aluminium Alloy Profile Architectural Anodized", "7604.29"),
    ("Diesel Internal Combustion Generator Set 100kVA Standby", "8502.11"),
    ("Insulated Copper Electric Wire 2.5mm PVC Sheathed", "8544.49"),
    ("Automated External Defibrillator AED Biphasic Portable", "9018.90"),
    ("Water Purification Filtration Membrane Reverse Osmosis Cartridge", "8421.21"),
    ("Polyvinyl Chloride PVC Rigid Sheet Transparent 2mm", "3920.49"),
    ("Gasoline Internal Combustion Engine 150cc 4-Stroke Air Cooled", "8407.32"),
    ("Stainless Steel Kitchen Sink Double Bowl Pressed", "7324.10"),
    ("Digital Multimeter Handheld True RMS Voltage Tester", "9030.31"),
    ("Cosmetic Skin Moisturizing Facial Cream Anti-Aging 50ml", "3304.99"),
    ("Men Formal Leather Oxford Dress Shoes Leather Sole", "6403.59"),
    ("Household Combined Refrigerator-Freezer Double Door Inverter", "8418.10"),
]

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tariff_file = os.path.join(base_dir, "data", "seed", "tariff_database.json")
    out_file = os.path.join(base_dir, "data", "seed", "ground_truth_benchmark_50.json")

    with open(tariff_file, "r", encoding="utf-8") as f:
        tariffs = {t["hs_code"]: t for t in json.load(f)}

    benchmark_items = []
    for idx, (desc, hs_code) in enumerate(ITEMS_DATA, start=1):
        tariff_meta = tariffs.get(hs_code, {})
        benchmark_items.append({
            "id": idx,
            "query_description": desc,
            "ground_truth_hs": hs_code,
            "official_description": tariff_meta.get("description", ""),
            "chapter": tariff_meta.get("chapter", hs_code.split(".")[0]),
            "duty_rate": tariff_meta.get("duty_rate", 0.0),
            "vat_rate": tariff_meta.get("vat_rate", 11.0),
            "restricted": tariff_meta.get("restricted", False),
            "required_permits": tariff_meta.get("required_permits", []),
        })

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_items, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated {len(benchmark_items)} ground truth benchmark items in {out_file}")

if __name__ == "__main__":
    main()

"use client";

import React, { useMemo, useState } from "react";

type ContainerSize = "20" | "40" | "45";
type ContainerType = "DRY" | "REEFER";

interface LineItem {
  item_id: number;
  declared_description: string;
  declared_hs: string;
  matched_hs: string;
  declared_duty: number;
  official_duty: number;
  total_value: number;
  restricted: boolean;
  required_permits: string[];
}

interface ScenarioPreset {
  id: string;
  pillLabel: string;
  shipment_id: string;
  invoice_number: string;
  importer_name: string;
  carrier: string;
  destination_port: string;
  default_container_count: number;
  default_container_size: ContainerSize;
  default_container_type: ContainerType;
  default_days_held: number;
  verdict: string;
  detention_risk: boolean;
  summary_note: string;
  items: LineItem[];
}

const SCENARIOS: ScenarioPreset[] = [
  {
    id: "high-risk-sdppi",
    pillLabel: "1. High-Risk Red Lane Hold",
    shipment_id: "SHP-2026-0042",
    invoice_number: "INV-2026-APL-091",
    importer_name: "PT Nexus Indo Tech",
    carrier: "CMA CGM / APL",
    destination_port: "Tanjung Priok, Jakarta (IDTPP)",
    default_container_count: 4,
    default_container_size: "40",
    default_container_type: "DRY",
    default_days_held: 10,
    verdict: "NON_COMPLIANT_HIGH_RISK",
    detention_risk: true,
    summary_note:
      "Declared HS 8471.30 (Portable computers) conflicts with matched official HS 8517.11 (Cellular smartphones). Mandatory SDPPI Type Approval certification required prior to port arrival.",
    items: [
      {
        item_id: 1,
        declared_description:
          "Apple iPhone 15 Pro Max 256GB Dual SIM Smartphone",
        declared_hs: "8471.30",
        matched_hs: "8517.11",
        declared_duty: 0.0,
        official_duty: 0.0,
        total_value: 115000.0,
        restricted: true,
        required_permits: ["SDPPI Type Approval Certification (Kemkominfo)"],
      },
    ],
  },
  {
    id: "multi-container-demurrage",
    pillLabel: "2. Multi-Container Demurrage Bleed",
    shipment_id: "SHP-2026-0089",
    invoice_number: "INV-2026-MED-442",
    importer_name: "PT Medika Nusantara Sejahtera",
    carrier: "CMA CGM / CNC",
    destination_port: "Tanjung Perak, Surabaya (IDSUB)",
    default_container_count: 3,
    default_container_size: "20",
    default_container_type: "DRY",
    default_days_held: 12,
    verdict: "NON_COMPLIANT_HIGH_RISK",
    detention_risk: true,
    summary_note:
      "Declared HS 8471.50 (Processing units, 0% duty) conflicts with official HS 9018.12 (Ultrasonic diagnostic scanners, 5% duty). Missing mandatory Kemenkes RI Medical Device Distribution License (Izin Edar Alat Kesehatan).",
    items: [
      {
        item_id: 1,
        declared_description:
          "Siemens Acuson Ultrasonic Diagnostic Scanner Probe System",
        declared_hs: "8471.50",
        matched_hs: "9018.12",
        declared_duty: 0.0,
        official_duty: 5.0,
        total_value: 120000.0,
        restricted: true,
        required_permits: [
          "Kemenkes RI Medical Distribution License (Izin Edar)",
        ],
      },
    ],
  },
  {
    id: "duty-restitution",
    pillLabel: "3. Duty Restitution Discovery",
    shipment_id: "SHP-2026-0099",
    invoice_number: "INV-2026-SRV-990",
    importer_name: "PT Cloud Data Raya",
    carrier: "CMA CGM",
    destination_port: "Tanjung Priok, Jakarta (IDTPP)",
    default_container_count: 1,
    default_container_size: "40",
    default_container_type: "DRY",
    default_days_held: 5,
    verdict: "COMPLIANT",
    detention_risk: false,
    summary_note:
      "HS 8471.50 classification matches official schedule with zero detention risk, but importer over-declared 15.0% import duty vs 0.0% official MFN rate. Qualifies for $15,000.00 USD customs duty restitution recovery.",
    items: [
      {
        item_id: 1,
        declared_description: "Enterprise Processing Server Rack Unit",
        declared_hs: "8471.50",
        matched_hs: "8471.50",
        declared_duty: 15.0,
        official_duty: 0.0,
        total_value: 100000.0,
        restricted: false,
        required_permits: [],
      },
    ],
  },
  {
    id: "compliant-green-lane",
    pillLabel: "4. Compliant Green-Lane Manifest",
    shipment_id: "SHP-2026-0105",
    invoice_number: "INV-2026-SRV-810",
    importer_name: "PT Cloud Infrastructure Indonesia",
    carrier: "CMA CGM",
    destination_port: "Tanjung Priok, Jakarta (IDTPP)",
    default_container_count: 1,
    default_container_size: "40",
    default_container_type: "DRY",
    default_days_held: 5,
    verdict: "COMPLIANT",
    detention_risk: false,
    summary_note:
      "Declared HS 8471.50 and 0.0% MFN duty rate match the official Indonesian customs tariff schedule with zero Lartas restrictions. Cleared for immediate Green-Lane release.",
    items: [
      {
        item_id: 1,
        declared_description: "Dell PowerEdge R750 Rack Server Processing Unit",
        declared_hs: "8471.50",
        matched_hs: "8471.50",
        declared_duty: 0.0,
        official_duty: 0.0,
        total_value: 65000.0,
        restricted: false,
        required_permits: [],
      },
    ],
  },
];

const CMA_CGM_RATES = {
  DRY: {
    freeDays: 5,
    slabs: [
      {
        maxDay: 5,
        label: "Days 1 to 5 (Free)",
        rates: { "20": 0, "40": 0, "45": 0 },
      },
      {
        maxDay: 10,
        label: "Days 6 to 10 (Slab 1)",
        rates: { "20": 66, "40": 101, "45": 141 },
      },
      {
        maxDay: 15,
        label: "Days 11 to 15 (Slab 2)",
        rates: { "20": 86, "40": 121, "45": 171 },
      },
      {
        maxDay: 20,
        label: "Days 16 to 20 (Slab 3)",
        rates: { "20": 96, "40": 151, "45": 181 },
      },
      {
        maxDay: 999,
        label: "Days 21+ (Slab 4)",
        rates: { "20": 106, "40": 161, "45": 191 },
      },
    ],
  },
  REEFER: {
    freeDays: 3,
    slabs: [
      {
        maxDay: 3,
        label: "Days 1 to 3 (Free)",
        rates: { "20": 0, "40": 0, "45": 0 },
      },
      {
        maxDay: 5,
        label: "Days 4 to 5 (Slab 1)",
        rates: { "20": 89, "40": 141, "45": 141 },
      },
      {
        maxDay: 7,
        label: "Days 6 to 7 (Slab 2)",
        rates: { "20": 126, "40": 176, "45": 176 },
      },
      {
        maxDay: 999,
        label: "Days 8+ (Slab 3)",
        rates: { "20": 130, "40": 180, "45": 180 },
      },
    ],
  },
};

function computeCmaCgmDemurrage(
  count: number,
  size: ContainerSize,
  type: ContainerType,
  daysProjected: number,
  detentionRisk: boolean,
) {
  const schedule = CMA_CGM_RATES[type];
  if (!detentionRisk) {
    return {
      freeDays: schedule.freeDays,
      detentionDays: 0,
      dailyRatePerContainer: 0,
      dailyBurnTotal: 0,
      cumulativeLiability: 0,
      activeSlabLabel: `Within free time allowance (${schedule.freeDays} free days)`,
    };
  }

  let cumulativePerContainer = 0;
  let activeRate = 0;
  let activeSlabLabel = "";

  for (let d = 1; d <= daysProjected; d++) {
    for (const slab of schedule.slabs) {
      if (d <= slab.maxDay) {
        const rate = slab.rates[size];
        cumulativePerContainer += rate;
        if (d === daysProjected) {
          activeRate = rate;
          activeSlabLabel = `${slab.label} - $${rate}/day`;
        }
        break;
      }
    }
  }

  return {
    freeDays: schedule.freeDays,
    detentionDays: Math.max(0, daysProjected - schedule.freeDays),
    dailyRatePerContainer: activeRate,
    dailyBurnTotal: activeRate * count,
    cumulativeLiability: cumulativePerContainer * count,
    activeSlabLabel,
  };
}

export default function LandingPage() {
  const [selectedScenarioIdx, setSelectedScenarioIdx] = useState<number>(0);
  const activeScenario = SCENARIOS[selectedScenarioIdx];

  const [containerCount, setContainerCount] = useState<number>(
    SCENARIOS[0].default_container_count,
  );
  const [containerSize, setContainerSize] = useState<ContainerSize>(
    SCENARIOS[0].default_container_size,
  );
  const [containerType, setContainerType] = useState<ContainerType>(
    SCENARIOS[0].default_container_type,
  );
  const [daysProjected, setDaysProjected] = useState<number>(
    SCENARIOS[0].default_days_held,
  );
  const [evidenceTab, setEvidenceTab] = useState<"dossier" | "mailpit">(
    "dossier",
  );
  const [monthlyManifests, setMonthlyManifests] = useState<number>(180);

  const handleSelectScenario = (idx: number) => {
    const preset = SCENARIOS[idx];
    setSelectedScenarioIdx(idx);
    setContainerCount(preset.default_container_count);
    setContainerSize(preset.default_container_size);
    setContainerType(preset.default_container_type);
    setDaysProjected(preset.default_days_held);
  };

  const demurrage = useMemo(
    () =>
      computeCmaCgmDemurrage(
        containerCount,
        containerSize,
        containerType,
        daysProjected,
        activeScenario.detention_risk,
      ),
    [
      containerCount,
      containerSize,
      containerType,
      daysProjected,
      activeScenario.detention_risk,
    ],
  );

  const financialTotals = useMemo(() => {
    let shortfall = 0;
    let restitution = 0;
    for (const item of activeScenario.items) {
      const diff = item.official_duty - item.declared_duty;
      if (diff > 0) {
        shortfall += (diff / 100) * item.total_value;
      } else if (diff < 0) {
        restitution += (Math.abs(diff) / 100) * item.total_value;
      }
    }
    return { shortfall, restitution };
  }, [activeScenario]);

  const generatedMarkdownDossier = useMemo(() => {
    const item = activeScenario.items[0];
    const permits =
      item.required_permits.length > 0
        ? item.required_permits.join(", ")
        : "None";
    return `# CustomsGuard Compliance Audit Report

**Shipment ID**: ${activeScenario.shipment_id}  
**Importer**: ${activeScenario.importer_name}  
**Verdict**: ${activeScenario.verdict}

### Executive Summary
- **Destination Port**: ${activeScenario.destination_port}
- **Container Specifications**: ${containerCount}x ${containerSize}ft Standard ${containerType}
- **Container Detention Risk**: ${activeScenario.detention_risk ? "YES" : "NO"}
- **Total Duty Shortfall**: $${financialTotals.shortfall.toLocaleString("en-US", { minimumFractionDigits: 2 })} USD
- **Potential Duty Restitution**: $${financialTotals.restitution.toLocaleString("en-US", { minimumFractionDigits: 2 })} USD
- **Carrier Benchmark**: CMA CGM Indonesia (Merged Import D&D Tariff, Effective July 1, 2026)
- **Active Daily Burn Rate**: $${demurrage.dailyBurnTotal.toLocaleString("en-US", { minimumFractionDigits: 2 })} USD/day ($${demurrage.dailyRatePerContainer}/day/cntr, ${demurrage.activeSlabLabel})
- **Projected ${demurrage.detentionDays}-Day Hold Liability**: $${demurrage.cumulativeLiability.toLocaleString("en-US", { minimumFractionDigits: 2 })} USD

### Critical Discrepancies & Regulatory Notes
1. ${activeScenario.summary_note}

### Itemized Audit Findings
| Item ID | Declared Description | Declared HS | Matched HS | Declared Duty | Official Duty | Restricted | Mandatory Permits |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| ${item.item_id} | ${item.declared_description} | ${item.declared_hs} | ${item.matched_hs} | ${item.declared_duty.toFixed(1)}% | ${item.official_duty.toFixed(1)}% | ${item.restricted ? "Yes" : "No"} | ${permits} |`;
  }, [
    activeScenario,
    containerCount,
    containerSize,
    containerType,
    demurrage,
    financialTotals,
  ]);

  const generatedMailpitPreview = useMemo(() => {
    return `From: alerts@customsguard.local
To: compliance-officer@customsguard.local
Subject: [CustomsGuard Alert] ${activeScenario.verdict}: Shipment ${activeScenario.shipment_id}

====================================================================
CUSTOMSGUARD AUTONOMOUS COMPLIANCE & DETENTION ALERT
====================================================================

SHIPMENT OVERVIEW
-----------------
Shipment ID             : ${activeScenario.shipment_id}
Official Verdict        : ${activeScenario.verdict}
Importer                : ${activeScenario.importer_name}
Container Specifications: ${containerCount}x ${containerSize}ft Standard ${containerType} (${demurrage.activeSlabLabel})

FINANCIAL & DEMURRAGE EXPOSURE
------------------------------
Total Duty Shortfall    : $${financialTotals.shortfall.toLocaleString("en-US", { minimumFractionDigits: 2 })} USD
CMA CGM Daily Burn Rate : $${demurrage.dailyBurnTotal.toLocaleString("en-US", { minimumFractionDigits: 2 })} USD / day
Projected Hold Liability: $${demurrage.cumulativeLiability.toLocaleString("en-US", { minimumFractionDigits: 2 })} USD

CRITICAL DISCREPANCY NOTES
--------------------------
- ${activeScenario.summary_note}

Preview in Mailpit: http://localhost:8025
====================================================================`;
  }, [
    activeScenario,
    containerCount,
    containerSize,
    containerType,
    demurrage,
    financialTotals,
  ]);

  const roiMetrics = useMemo(() => {
    const preventedHoldsPerMonth = Math.max(
      1,
      Math.round(monthlyManifests * 0.06),
    );
    const demurrageSaved = preventedHoldsPerMonth * 2020;
    const restitutionRecovered = Math.round(monthlyManifests * 0.03) * 4500;
    const totalMonthlyValue = demurrageSaved + restitutionRecovered;
    return {
      preventedHoldsPerMonth,
      demurrageSaved,
      restitutionRecovered,
      totalMonthlyValue,
    };
  }, [monthlyManifests]);

  return (
    <div className="min-h-screen bg-[#121212] text-[#F8FAFC]">
      {/* Sticky Top Navigation (Dub Feature-Stack Macrostructure) */}
      <header className="sticky top-0 z-50 border-b border-[#2A2A35] bg-[#0B0B0F]/60 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <a href="#" className="flex items-center gap-3 focus:outline-none">
            <img src="/logo.svg" alt="CustomsGuard" className="h-3.5 w-auto" />
          </a>

          <nav className="hidden items-center gap-8 text-sm text-[#94A3B8] md:flex">
            <a href="#bottleneck" className="transition hover:text-[#F8FAFC]">
              Problem
            </a>
            <a
              href="#scenario-explorer"
              className="transition hover:text-[#F8FAFC]"
            >
              Interactive Demo
            </a>
            <a href="#architecture" className="transition hover:text-[#F8FAFC]">
              Architecture
            </a>
            <a href="#pricing" className="transition hover:text-[#F8FAFC]">
              Pricing
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <a
              href="https://github.com/rafifmsn/customs-guard/blob/main/docs/technical/api_reference.md"
              target="_blank"
              rel="noreferrer"
              className="hidden rounded-full border border-[#2A2A35] bg-[#16161E] px-4 py-2 text-sm font-medium text-[#F8FAFC] transition hover:border-[#A78BFA] sm:inline-block"
            >
              API Reference
            </a>
            <a
              href="https://cgd.rafifmsn.com"
              className="rounded-full bg-[#A78BFA] px-4 py-2 text-sm font-semibold text-[#0B0B0F] transition hover:bg-[#C4B5FD]"
            >
              Dashboard
            </a>
          </div>
        </div>
      </header>

      {/* Hero Section & Feature-Stack Gateway */}
      <section className="pt-16 pb-20">
        <div className="mx-auto max-w-5xl px-6 text-center">
          <h1 className="mx-auto max-w-4xl font-display text-4xl font-medium leading-[1.15] tracking-tight text-[#F8FAFC] sm:text-5xl text-balance">
            Eliminate customs Red-Lane holds before cargo reaches port
          </h1>

          <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-[#94A3B8]">
            CustomsGuard audits commercial shipping declarations against 5,612
            official Indonesian HS-6 subheadings, verifies mandatory Lartas
            ministry permits, and models progressive CMA CGM container detention
            exposure in milliseconds.
          </p>

          {/* Dual Pill CTAs */}
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <a
              href="https://cgd.rafifmsn.com"
              className="rounded-full bg-[#A78BFA] px-6 py-3 text-sm font-semibold text-[#0B0B0F] transition hover:bg-[#C4B5FD]"
            >
              Dashboard
            </a>
            <a
              href="https://github.com/rafifmsn/customs-guard/blob/main/docs/technical/api_reference.md"
              target="_blank"
              rel="noreferrer"
              className="rounded-full border border-[#2A2A35] bg-[#1A1A22] px-6 py-3 text-sm font-medium text-[#F8FAFC] transition hover:border-[#A78BFA]"
            >
              API Reference
            </a>
          </div>

          {/* Dub Signature: 3 Accented Feature Pills Gateway */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-3">
            <div className="inline-flex items-center gap-2.5 rounded-full border border-[#2A2A35] bg-[#1A1A22] px-4 py-2 text-xs font-medium text-[#F8FAFC] shadow-sm">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: "#ec8434" }}
              />
              <span>Autonomous Tariff RAG (5,612 HS-6)</span>
            </div>
            <div className="inline-flex items-center gap-2.5 rounded-full border border-[#2A2A35] bg-[#1A1A22] px-4 py-2 text-xs font-medium text-[#F8FAFC] shadow-sm">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: "#86c1a1" }}
              />
              <span>CMA CGM Demurrage Engine (July 2026 Tariff)</span>
            </div>
            <div className="inline-flex items-center gap-2.5 rounded-full border border-[#2A2A35] bg-[#1A1A22] px-4 py-2 text-xs font-medium text-[#F8FAFC] shadow-sm">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: "#A78BFA" }}
              />
              <span>Lartas Permit Guard (SDPPI, Kemenkes, BPOM)</span>
            </div>
          </div>

          {/* Main Application Showcase Container with Interactive Video Play Trigger */}
          <div className="mt-8 overflow-hidden rounded-2xl border border-[#2A2A35] bg-[#16161E] p-3 shadow-sm">
            <div className="overflow-hidden rounded-xl border border-[#2A2A35] bg-[#0B0B0F]">
              <a
                href="https://www.youtube.com/watch?v=demo"
                target="_blank"
                rel="noreferrer"
                className="group relative block aspect-[16/9] w-full overflow-hidden bg-[#0B0B0F] cursor-pointer"
                aria-label="CustomsGuard Autonomous Compliance Engine Walkthrough"
              >
                {/* Background Dashboard Mockup Poster */}
                <img
                  src="https://placehold.co/1920x1080/16161E/94A3B8?text=CustomsGuard+Compliance+Engine+Walkthrough"
                  alt="CustomsGuard Application Walkthrough"
                  className="h-full w-full object-cover transition-transform duration-500 ease-out group-hover:scale-[1.02] opacity-85 group-hover:opacity-100"
                />

                {/* Subtle Vignette Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-[#0B0B0F]/80 via-transparent to-[#0B0B0F]/30 transition-opacity duration-300 group-hover:opacity-60" />

                {/* Centered Circular Play Button Badge */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="flex size-14 md:size-20 items-center justify-center rounded-full border border-[#2A2A35] bg-[#0B0B0F]/80 backdrop-blur-md shadow-2xl transition-all duration-300 ease-out group-hover:scale-110 group-hover:border-[#A78BFA] group-hover:shadow-[0_0_30px_rgba(167,139,250,0.35)] group-hover:bg-[#1A1A22]/90">
                    <svg
                      className="size-6 md:size-8 text-[#F8FAFC] transition-colors duration-300 group-hover:text-[#A78BFA]"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  </div>
                </div>
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Section 2: Domain Bottleneck & Value Metrics */}
      <section id="bottleneck" className="py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="max-w-3xl">
            <p className="font-mono text-xs font-medium uppercase tracking-wider text-[#A78BFA]">
              Indonesian Cross-Border Bottleneck
            </p>
            <h2 className="mt-2 font-display text-3xl font-medium tracking-tight text-[#F8FAFC] sm:text-4xl text-balance">
              Why manual manifest verification fails at port scale
            </h2>
            <p className="mt-3 text-base leading-relaxed text-[#94A3B8]">
              Indonesian import declarations are audited by the Directorate
              General of Customs and Excise (DJBC) against 5,612 Harmonized
              System subheadings. A single misclassified line item or overlooked
              ministry permit locks the entire multi-container consignment in
              port detention.
            </p>
          </div>

          <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-[#2A2A35] bg-[#1A1A22] p-6">
              <div className="font-mono text-xs text-[#64748B]">
                WTO / UNCTAD ITC MACMAP
              </div>
              <div className="mt-2 font-display text-3xl font-medium text-[#F8FAFC]">
                5,612 HS-6
              </div>
              <p className="mt-2 text-sm leading-relaxed text-[#94A3B8]">
                Standardized 6-digit Indonesian tariff subheadings indexed
                locally inside Qdrant for deterministic sub-second retrieval.
              </p>
            </div>

            <div className="rounded-xl border border-[#2A2A35] bg-[#1A1A22] p-6">
              <div className="font-mono text-xs text-[#64748B]">
                MANDATORY LARTAS PERMITS
              </div>
              <div className="mt-2 font-display text-3xl font-medium text-[#F8FAFC]">
                9.73% Restricted
              </div>
              <p className="mt-2 text-sm leading-relaxed text-[#94A3B8]">
                546 high-scrutiny tariff codes require pre-arrival approvals
                from SDPPI Kemkominfo, Kemenkes RI, or BPOM.
              </p>
            </div>

            <div className="rounded-xl border border-[#2A2A35] bg-[#1A1A22] p-6">
              <div className="font-mono text-xs text-[#64748B]">
                CUSTOMS LAW NO. 17/2006
              </div>
              <div className="mt-2 font-display text-3xl font-medium text-[#F87171]">
                100% - 1,000%
              </div>
              <p className="mt-2 text-sm leading-relaxed text-[#94A3B8]">
                Statutory administrative penalty surcharges assessed under
                Article 82(5) on import duty shortfalls caused by
                misdeclaration.
              </p>
            </div>

            <div className="rounded-xl border border-[#2A2A35] bg-[#1A1A22] p-6">
              <div className="font-mono text-xs text-[#64748B]">
                ON-PREMISE DOCKER STACK
              </div>
              <div className="mt-2 font-display text-3xl font-medium text-[#34D399]">
                ~87% Lower Cost
              </div>
              <p className="mt-2 text-sm leading-relaxed text-[#94A3B8]">
                Self-hosted local execution eliminates recurring cloud SaaS
                per-page OCR fees while keeping commercial invoices inside your
                perimeter.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Section 3: Interactive 1-Click Scenario Explorer */}
      <section id="scenario-explorer" className="py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
            <div className="max-w-3xl">
              <p className="font-mono text-xs font-medium uppercase tracking-wider text-[#A78BFA]">
                Interactive 1-Click Scenario Explorer
              </p>
              <h2 className="mt-2 font-display text-3xl font-medium tracking-tight text-[#F8FAFC] sm:text-4xl text-balance">
                Deterministic Tariff Audit & CMA CGM Demurrage Simulator
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[#94A3B8]">
                Select any of the 4 canonical shipment manifests below and
                adjust container equipment or port hold duration to compute
                real-time CMA CGM Indonesia (Effective July 1, 2026) progressive
                day-slab liabilities.
              </p>
            </div>
          </div>

          {/* 4 Scenario Selector Pills */}
          <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {SCENARIOS.map((scen, idx) => {
              const isSelected = idx === selectedScenarioIdx;
              return (
                <button
                  key={scen.id}
                  type="button"
                  onClick={() => handleSelectScenario(idx)}
                  className={`flex flex-col justify-between rounded-xl border p-4 text-left transition ${
                    isSelected
                      ? "border-[#A78BFA] bg-[#1A1A22] text-[#F8FAFC] shadow-[0_0_15px_rgba(167,139,250,0.15)] ring-1 ring-[#A78BFA]"
                      : "border-[#2A2A35] bg-[#16161E] text-[#F8FAFC] hover:border-[#3E3E4E] hover:bg-[#1A1A22]"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs opacity-75">
                      {scen.shipment_id}
                    </span>
                    <span
                      className={`rounded-full px-2 py-0.5 font-mono text-[10px] font-medium ${
                        scen.detention_risk
                          ? isSelected
                            ? "border border-[#EF4444]/40 bg-[#EF4444]/20 text-[#F87171]"
                            : "bg-[#EF4444]/10 text-[#F87171]"
                          : isSelected
                            ? "border border-[#10B981]/40 bg-[#10B981]/20 text-[#34D399]"
                            : "bg-[#10B981]/10 text-[#34D399]"
                      }`}
                    >
                      {scen.verdict}
                    </span>
                  </div>
                  <div className="mt-3 text-sm font-medium leading-snug">
                    {scen.pillLabel}
                  </div>
                  <div className="mt-2 text-xs text-[#94A3B8]">
                    {scen.importer_name}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Interactive Container & Demurrage Controls */}
          <div className="mt-6 rounded-2xl border border-[#2A2A35] bg-[#1A1A22] p-6">
            <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
              <div>
                <div className="flex items-center justify-between text-xs font-medium text-[#F8FAFC]">
                  <span>Container Count</span>
                  <span className="font-mono text-xs font-semibold text-[#A78BFA]">
                    {containerCount} container
                  </span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={10}
                  value={containerCount}
                  onChange={(e) => setContainerCount(Number(e.target.value))}
                  className="mt-3 w-full accent-[#A78BFA]"
                />
                <div className="mt-1 flex justify-between font-mono text-[10px] text-[#64748B]">
                  <span>1</span>
                  <span>5</span>
                  <span>10</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-[#F8FAFC]">
                  Container Size (CMA CGM Schedule)
                </label>
                <div className="mt-2 grid grid-cols-3 gap-2">
                  {(["20", "40", "45"] as ContainerSize[]).map((sz) => (
                    <button
                      key={sz}
                      type="button"
                      onClick={() => setContainerSize(sz)}
                      className={`rounded-lg border py-2 font-mono text-xs font-medium transition ${
                        containerSize === sz
                          ? "border-[#A78BFA] bg-[#A78BFA] text-[#0B0B0F] font-semibold"
                          : "border-[#2A2A35] bg-[#16161E] text-[#94A3B8] hover:border-[#3E3E4E] hover:text-[#F8FAFC]"
                      }`}
                    >
                      {sz}ft
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-[#F8FAFC]">
                  Equipment Type
                </label>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  {(
                    [
                      { key: "DRY", label: "Standard Dry" },
                      { key: "REEFER", label: "Reefer" },
                    ] as { key: ContainerType; label: string }[]
                  ).map((eq) => (
                    <button
                      key={eq.key}
                      type="button"
                      onClick={() => setContainerType(eq.key)}
                      className={`rounded-lg border px-2 py-2 font-mono text-xs font-medium transition ${
                        containerType === eq.key
                          ? "border-[#A78BFA] bg-[#A78BFA] text-[#0B0B0F] font-semibold"
                          : "border-[#2A2A35] bg-[#16161E] text-[#94A3B8] hover:border-[#3E3E4E] hover:text-[#F8FAFC]"
                      }`}
                    >
                      {eq.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between text-xs font-medium text-[#F8FAFC]">
                  <span>Projected Port Hold Duration</span>
                  <span className="font-mono text-xs font-semibold text-[#A78BFA]">
                    {daysProjected} days
                  </span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={25}
                  value={daysProjected}
                  onChange={(e) => setDaysProjected(Number(e.target.value))}
                  className="mt-3 w-full accent-[#A78BFA]"
                />
                <div className="mt-1 flex justify-between font-mono text-[10px] text-[#64748B]">
                  <span>Day 1</span>
                  <span>Day 12</span>
                  <span>Day 25</span>
                </div>
              </div>
            </div>

            {/* Real-Time Computed Financial & Demurrage Cards */}
            <div className="mt-6 grid grid-cols-1 gap-4 pt-2 sm:grid-cols-2 lg:grid-cols-5">
              <div className="rounded-xl border border-[#2A2A35] bg-[#16161E] p-4">
                <div className="font-mono text-[11px] text-[#64748B]">
                  OFFICIAL VERDICT
                </div>
                <div
                  className={`mt-1 font-mono text-sm font-semibold truncate ${
                    activeScenario.detention_risk
                      ? "text-[#F87171]"
                      : "text-[#34D399]"
                  }`}
                >
                  {activeScenario.verdict}
                </div>
                <div className="mt-1 text-xs text-[#94A3B8]">
                  {activeScenario.detention_risk
                    ? "Red-Lane Hold Triggered"
                    : "Green-Lane Clearance"}
                </div>
              </div>

              <div className="rounded-xl border border-[#2A2A35] bg-[#16161E] p-4">
                <div className="font-mono text-[11px] text-[#64748B]">
                  DUTY SHORTFALL
                </div>
                <div className="mt-1 font-mono text-xl font-semibold text-[#F8FAFC]">
                  $
                  {financialTotals.shortfall.toLocaleString("en-US", {
                    minimumFractionDigits: 2,
                  })}
                </div>
                <div className="mt-1 text-xs text-[#94A3B8]">
                  {financialTotals.shortfall > 0
                    ? "Subject to Art. 82(5) Fine"
                    : "Zero Underpayment"}
                </div>
              </div>

              <div className="rounded-xl border border-[#2A2A35] bg-[#16161E] p-4">
                <div className="font-mono text-[11px] text-[#64748B]">
                  DUTY RESTITUTION
                </div>
                <div className="mt-1 font-mono text-xl font-semibold text-[#34D399]">
                  $
                  {financialTotals.restitution.toLocaleString("en-US", {
                    minimumFractionDigits: 2,
                  })}
                </div>
                <div className="mt-1 text-xs text-[#94A3B8]">
                  {financialTotals.restitution > 0
                    ? "Eligible for Tax Refund"
                    : "No Overpayment"}
                </div>
              </div>

              <div className="rounded-xl border border-[#2A2A35] bg-[#16161E] p-4">
                <div className="font-mono text-[11px] text-[#64748B]">
                  CMA CGM DAILY BURN
                </div>
                <div className="mt-1 font-mono text-xl font-semibold text-[#F8FAFC]">
                  $
                  {demurrage.dailyBurnTotal.toLocaleString("en-US", {
                    minimumFractionDigits: 2,
                  })}
                  /d
                </div>
                <div className="mt-1 truncate text-xs text-[#94A3B8]">
                  {demurrage.activeSlabLabel}
                </div>
              </div>

              <div className="rounded-xl border border-[#2A2A35] bg-[#16161E] p-4">
                <div className="font-mono text-[11px] text-[#64748B]">
                  PROJECTED HOLD ({daysProjected}D)
                </div>
                <div className="mt-1 font-mono text-xl font-semibold text-[#F87171]">
                  $
                  {demurrage.cumulativeLiability.toLocaleString("en-US", {
                    minimumFractionDigits: 2,
                  })}
                </div>
                <div className="mt-1 text-xs text-[#94A3B8]">
                  {demurrage.detentionDays} billable detention days
                </div>
              </div>
            </div>

            {/* Itemized Findings Table & Dossier / Mailpit Preview */}
            <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-12">
              <div className="lg:col-span-7">
                <div className="rounded-xl border border-[#2A2A35] bg-[#16161E] p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-[#F8FAFC]">
                      Lartas Permit Comparison
                    </h3>
                    <span className="hidden md:block font-mono text-xs text-[#64748B]">
                      Port: {activeScenario.destination_port}
                    </span>
                  </div>
                  <div className="mt-3 overflow-x-auto">
                    <table className="w-full min-w-[640px] border-collapse text-left text-xs">
                      <thead>
                        <tr className="border-b border-[#2A2A35] bg-[#121212] font-mono text-[11px] text-[#94A3B8]">
                          <th className="py-2.5 px-3 whitespace-nowrap">
                            Commodity
                          </th>
                          <th className="py-2.5 px-3 whitespace-nowrap">
                            Declared HS
                          </th>
                          <th className="py-2.5 px-3 whitespace-nowrap">
                            Official HS
                          </th>
                          <th className="py-2.5 px-3 whitespace-nowrap">
                            Declared / Official Duty
                          </th>
                          <th className="py-2.5 px-3 whitespace-nowrap">
                            Mandatory Lartas Permits
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {activeScenario.items.map((item) => (
                          <tr
                            key={item.item_id}
                            className="border-b border-[#2A2A35]"
                          >
                            <td className="py-3 px-3 font-medium text-[#F8FAFC] truncate">
                              {item.declared_description}
                            </td>
                            <td className="py-3 px-3 font-mono text-[#F87171] whitespace-nowrap">
                              {item.declared_hs}
                            </td>
                            <td className="py-3 px-3 font-mono font-semibold text-[#34D399] whitespace-nowrap">
                              {item.matched_hs}
                            </td>
                            <td className="py-3 px-3 font-mono text-[#E2E8F0] whitespace-nowrap">
                              {item.declared_duty.toFixed(1)}% /{" "}
                              {item.official_duty.toFixed(1)}%
                            </td>
                            <td className="py-3 px-3 whitespace-nowrap">
                              {item.required_permits.length > 0 ? (
                                <span className="inline-block rounded border border-[#EF4444]/30 bg-[#EF4444]/15 px-2 py-0.5 font-mono text-[11px] text-[#F87171]">
                                  {item.required_permits.join(", ")}
                                </span>
                              ) : (
                                <span className="font-mono text-[11px] text-[#34D399]">
                                  None (Unrestricted)
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="mt-3 text-xs leading-relaxed text-[#94A3B8]">
                    <strong className="text-[#F8FAFC]">Audit Advisory:</strong>{" "}
                    {activeScenario.summary_note}
                  </p>
                </div>
              </div>

              <div className="lg:col-span-5">
                <div className="flex h-full flex-col rounded-xl border border-[#2A2A35] bg-[#16161E] p-4">
                  <div className="flex flex-col items-start gap-y-2 md:flex-row md:items-center md:justify-between pb-2">
                    <span className="text-sm font-medium text-[#F8FAFC]">
                      Automated Reporting
                    </span>
                    <div className="flex gap-1.5">
                      <button
                        type="button"
                        onClick={() => setEvidenceTab("dossier")}
                        className={`rounded-md px-2.5 py-1 font-mono text-[11px] transition ${
                          evidenceTab === "dossier"
                            ? "bg-[#A78BFA] text-[#0B0B0F] font-semibold"
                            : "bg-[#121212] text-[#94A3B8] border border-[#2A2A35] hover:text-[#F8FAFC]"
                        }`}
                      >
                        Markdown Dossier
                      </button>
                      <button
                        type="button"
                        onClick={() => setEvidenceTab("mailpit")}
                        className={`rounded-md px-2.5 py-1 font-mono text-[11px] transition ${
                          evidenceTab === "mailpit"
                            ? "bg-[#A78BFA] text-[#0B0B0F] font-semibold"
                            : "bg-[#121212] text-[#94A3B8] border border-[#2A2A35] hover:text-[#F8FAFC]"
                        }`}
                      >
                        Mail SMTP
                      </button>
                    </div>
                  </div>
                  <pre className="mt-3 max-h-60 flex-1 overflow-auto rounded-lg border border-[#2A2A35] bg-[#0B0B0F] p-3 font-mono text-[11px] leading-relaxed text-[#E2E8F0]">
                    {evidenceTab === "dossier"
                      ? generatedMarkdownDossier
                      : generatedMailpitPreview}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section 4: Air-Gapped Security & Split-Channel Architecture */}
      <section id="architecture" className="py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="max-w-3xl">
            <p className="font-mono text-xs font-medium uppercase tracking-wider text-[#A78BFA]">
              Split-Channel On-Premise Topology
            </p>
            <h2 className="mt-2 font-display text-3xl font-medium tracking-tight text-[#F8FAFC] sm:text-4xl text-balance">
              Air-gapped commercial privacy with deterministic execution
            </h2>
            <p className="mt-3 text-base leading-relaxed text-[#94A3B8]">
              Commercial invoices contain sensitive supplier pricing, HS
              classifications, and importer tax identifiers. CustomsGuard runs
              inside a self-contained 6-service Docker stack where deterministic
              tariff math and bounded AI orchestration remain strictly inside
              your network perimeter.
            </p>
          </div>

          <div className="mt-10 rounded-2xl border border-dashed border-[#3E3E4E] bg-[#1A1A22] p-6">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3 lg:grid-cols-6">
              {[
                {
                  name: "streamlit",
                  port: ":8501",
                  stack: "Streamlit",
                  desc: "Declarative compliance workspace, scenario loader, and dossier archive.",
                },
                {
                  name: "fastapi",
                  port: ":8000",
                  stack: "FastAPI + Asyncio",
                  desc: "Centralized REST controller, Swagger UI, and bounded Bob CLI worker pool.",
                },
                {
                  name: "langflow",
                  port: ":7860",
                  stack: "Langflow + MCP",
                  desc: "Hosts Pipeline A (Core Audit + Guardrails) and legacy IBM Bob MCP endpoint.",
                },
                {
                  name: "qdrant",
                  port: ":6333",
                  stack: "Qdrant Vector DB",
                  desc: "Stores 5,612 Indonesian HS-6 tariff records and Lartas permit triggers.",
                },
                {
                  name: "mailpit",
                  port: ":1025 / :8025",
                  stack: "Mock SMTP & UI",
                  desc: "Captures real-time structured detention alerts for compliance officers.",
                },
                {
                  name: "postgres",
                  port: ":5432",
                  stack: "PostgreSQL 16",
                  desc: "Persists Langflow workflow definitions and execution state.",
                },
              ].map((svc) => (
                <div
                  key={svc.name}
                  className="rounded-xl border border-[#2A2A35] bg-[#16161E] p-4 shadow-sm hover:border-[#A78BFA]/50 transition"
                >
                  <div className="flex items-center justify-between font-mono text-xs">
                    <span className="font-semibold text-[#F8FAFC]">
                      {svc.name}
                    </span>
                    <span className="rounded bg-[#2A2A35] px-1.5 py-0.5 text-[10px] text-[#94A3B8]">
                      {svc.port}
                    </span>
                  </div>
                  <div className="mt-1 font-mono text-[11px] text-[#A78BFA]">
                    {svc.stack}
                  </div>
                  <p className="mt-2 text-xs leading-relaxed text-[#94A3B8]">
                    {svc.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Section 5: Commercial Pricing Tiers & Payback Calculator */}
      <section id="pricing" className="py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center">
            <p className="font-mono text-xs font-medium uppercase tracking-wider text-[#A78BFA]">
              Commercial Viability & ROI
            </p>
            <h2 className="mt-2 font-display text-3xl font-medium tracking-tight text-[#F8FAFC] sm:text-4xl text-balance">
              Single prevented Red-Lane hold pays for an entire year
            </h2>
            <p className="mx-auto mt-3 max-w-2xl text-base leading-relaxed text-[#94A3B8]">
              Transparent commercial tiers built for Indonesian customs brokers
              (PPJK), freight forwarders, and enterprise import compliance
              teams.
            </p>
          </div>

          {/* Interactive Payback Calculator */}
          <div className="mx-auto mt-10 max-w-4xl rounded-2xl border border-[#2A2A35] bg-[#1A1A22] p-6">
            <div>
              <div className="text-sm font-medium text-[#F8FAFC] pb-2">
                Interactive Monthly ROI & Demurrage Savings Estimator
              </div>
              <div className="text-xs text-[#94A3B8]">
                Adjust your monthly import manifest volume to estimate prevented
                CMA CGM detention holds and duty restitution recovery.
              </div>
            </div>
            <input
              type="range"
              min={20}
              max={1000}
              step={20}
              value={monthlyManifests}
              onChange={(e) => setMonthlyManifests(Number(e.target.value))}
              className="mt-4 w-full accent-[#A78BFA]"
            />
            <div className="text-xs text-[#A78BFA] font-semibold mt-1">
              {monthlyManifests} manifests / month
            </div>
            <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded-xl border border-[#2A2A35] bg-[#16161E] p-4">
                <div className="font-mono text-[11px] text-[#64748B]">
                  EST. PREVENTED RED-LANE HOLDS
                </div>
                <div className="mt-1 font-mono text-2xl font-semibold text-[#F8FAFC]">
                  {roiMetrics.preventedHoldsPerMonth} holds / mo
                </div>
                <div className="mt-1 text-xs text-[#94A3B8]">
                  ~$
                  {roiMetrics.demurrageSaved.toLocaleString("en-US")} CMA CGM
                  demurrage avoided
                </div>
              </div>
              <div className="rounded-xl border border-[#2A2A35] bg-[#16161E] p-4">
                <div className="font-mono text-[11px] text-[#64748B]">
                  EST. DUTY RESTITUTION RECOVERY
                </div>
                <div className="mt-1 font-mono text-2xl font-semibold text-[#34D399]">
                  ${roiMetrics.restitutionRecovered.toLocaleString("en-US")} /
                  mo
                </div>
                <div className="mt-1 text-xs text-[#94A3B8]">
                  Overpaid MFN tariff refund discovery
                </div>
              </div>
              <div className="rounded-xl border border-[#2A2A35] bg-[#16161E] p-4">
                <div className="font-mono text-[11px] text-[#64748B]">
                  NET MONTHLY COMPLIANCE VALUE
                </div>
                <div className="mt-1 font-mono text-2xl font-semibold text-[#A78BFA]">
                  ${roiMetrics.totalMonthlyValue.toLocaleString("en-US")} / mo
                </div>
                <div className="mt-1 text-xs text-[#94A3B8]">
                  &gt;15x payback vs Professional tier
                </div>
              </div>
            </div>
          </div>

          {/* 4 Commercial Tiers */}
          <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
            <div className="flex flex-col justify-between rounded-2xl border border-[#2A2A35] bg-[#1A1A22] p-6">
              <div>
                <div className="font-mono text-xs font-semibold uppercase text-[#64748B]">
                  Starter
                </div>
                <div className="mt-3 flex items-baseline gap-1">
                  <span className="font-display text-3xl font-medium text-[#F8FAFC]">
                    $129
                  </span>
                  <span className="text-xs text-[#64748B]">
                    /mo (~2.0M IDR)
                  </span>
                </div>
                <p className="mt-1 text-xs text-[#64748B]">Billed annually</p>
                <ul className="mt-6 space-y-2.5 text-xs text-[#94A3B8]">
                  <li>Up to 250 shipment audits / month</li>
                  <li>Full 5,612 Indonesian HS-6 search</li>
                  <li>Lartas permit verification (SDPPI, Kemenkes, BPOM)</li>
                  <li>Automated Mailpit / SMTP detention alerts</li>
                  <li>Standard Markdown & JSON dossier exports</li>
                </ul>
              </div>
              <a
                href="https://cgd.rafifmsn.com"
                className="mt-8 block rounded-full border border-[#2A2A35] bg-[#16161E] py-2.5 text-center text-xs font-medium text-[#F8FAFC] transition hover:border-[#A78BFA]"
              >
                Try Free for 14 Days
              </a>
            </div>

            <div className="flex flex-col justify-between rounded-2xl border-2 border-[#A78BFA] bg-[#1A1A22] p-6 shadow-[0_0_25px_rgba(167,139,250,0.15)]">
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold uppercase text-[#A78BFA]">
                    Professional
                  </span>
                  <span className="rounded-full bg-[#A78BFA] px-2.5 py-0.5 font-mono text-[10px] font-bold text-[#0B0B0F]">
                    Most Popular
                  </span>
                </div>
                <div className="mt-3 flex items-baseline gap-1">
                  <span className="font-display text-3xl font-medium text-[#F8FAFC]">
                    $499
                  </span>
                  <span className="text-xs text-[#64748B]">
                    /mo (~7.8M IDR)
                  </span>
                </div>
                <p className="mt-1 text-xs text-[#64748B]">Billed annually</p>
                <ul className="mt-6 space-y-2.5 text-xs text-[#E2E8F0]">
                  <li>Up to 2,500 shipment audits / month</li>
                  <li>CMA CGM progressive day-slab demurrage engine</li>
                  <li>Duty overpayment restitution analyzer</li>
                  <li>Multi-seat compliance broker workspace</li>
                  <li>Direct FastAPI REST & Swagger access</li>
                </ul>
              </div>
              <a
                href="https://cgd.rafifmsn.com"
                className="mt-8 block rounded-full bg-[#A78BFA] py-2.5 text-center text-xs font-semibold text-[#0B0B0F] transition hover:bg-[#C4B5FD]"
              >
                Try Free for 14 Days
              </a>
            </div>

            <div className="flex flex-col justify-between rounded-2xl border border-[#2A2A35] bg-[#1A1A22] p-6">
              <div>
                <div className="font-mono text-xs font-semibold uppercase text-[#64748B]">
                  Enterprise On-Premise
                </div>
                <div className="mt-3 flex items-baseline gap-1">
                  <span className="font-display text-3xl font-medium text-[#F8FAFC]">
                    $1,499
                  </span>
                  <span className="text-xs text-[#64748B]">
                    /mo (~23.5M IDR)
                  </span>
                </div>
                <p className="mt-1 text-xs text-[#64748B]">
                  Custom air-gapped deployment
                </p>
                <ul className="mt-6 space-y-2.5 text-xs text-[#94A3B8]">
                  <li>Unlimited commercial manifest audits</li>
                  <li>Air-gapped on-premise Docker appliance</li>
                  <li>Custom vector embeddings & CEISA / ERP integration</li>
                  <li>Priority DJBC & Lartas regulatory updates</li>
                  <li>Dedicated compliance engineering SLA</li>
                </ul>
              </div>
              <a
                href="https://cgd.rafifmsn.com"
                className="mt-8 block rounded-full border border-[#2A2A35] bg-[#16161E] py-2.5 text-center text-xs font-medium text-[#F8FAFC] transition hover:border-[#A78BFA]"
              >
                Contact Sales
              </a>
            </div>

            <div className="flex flex-col justify-between rounded-2xl border border-[#2A2A35] bg-[#1A1A22] p-6">
              <div>
                <div className="font-mono text-xs font-semibold uppercase text-[#64748B]">
                  Developer API
                </div>
                <div className="mt-3 flex items-baseline gap-1">
                  <span className="font-display text-3xl font-medium text-[#F8FAFC]">
                    $0.75
                  </span>
                  <span className="text-xs text-[#64748B]">/ audit</span>
                </div>
                <p className="mt-1 text-xs text-[#64748B]">Pay-as-you-go</p>
                <ul className="mt-6 space-y-2.5 text-xs text-[#94A3B8]">
                  <li>Standard Model Context Protocol (MCP) tool</li>
                  <li>Programmatic FastAPI `/api/v1/audit` webhook</li>
                  <li>Machine-readable JSON + Markdown dossier response</li>
                  <li>Compatible with IBM Bob Desktop & CLI</li>
                </ul>
              </div>
              <a
                href="https://cgd.rafifmsn.com"
                className="mt-8 block rounded-full border border-[#2A2A35] bg-[#16161E] py-2.5 text-center text-xs font-medium text-[#F8FAFC] transition hover:border-[#A78BFA]"
              >
                Get an API Key
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#2A2A35] bg-[#0B0B0F] py-12">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            {/* Left side: Logo & Brand description */}
            <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center">
              <a href="#" className="flex items-center">
                <img
                  src="/logo.svg"
                  alt="CustomsGuard"
                  className="h-3 w-auto"
                />
              </a>
              <span className="hidden text-[#2A2A35] sm:inline">|</span>
              <span className="text-xs text-[#94A3B8]">
                Autonomous Indonesian Trade Compliance & Tariff Discrepancy
                Engine
              </span>
            </div>

            {/* Right side: Navigation anchors */}
            <div className="flex flex-wrap items-center gap-6 font-mono text-xs text-[#94A3B8]">
              <a
                href="https://rmsn.notion.site/CustomsGuard-402ecf518bfa80f88309efb2ecc8cb3f?source=copy_link"
                onClick={(e) => {
                  e.preventDefault();
                  alert(
                    "CustomsGuard operates strictly on-premise within your air-gapped Docker perimeter. Commercial invoices and shipment data remain confidential inside your infrastructure.",
                  );
                }}
                className="transition hover:text-[#A78BFA]"
              >
                Privacy
              </a>
              <a
                href="https://rmsn.notion.site/CustomsGuard-402ecf518bfa80f88309efb2ecc8cb3f?source=copy_link"
                onClick={(e) => {
                  e.preventDefault();
                  alert(
                    "CustomsGuard provides advisory customs audit intelligence. Final cargo release authorizations remain with certified trade compliance officers and PPJK brokers.",
                  );
                }}
                className="transition hover:text-[#A78BFA]"
              >
                Terms of Service
              </a>
              <a
                href="mailto:rafif@rafifmsn.com"
                className="transition hover:text-[#A78BFA]"
              >
                Contact
              </a>
            </div>
          </div>

          {/* Bottom metadata strip */}
          <div className="mt-8 flex flex-col items-start justify-between gap-3 border-t border-[#2A2A35]/60 pt-6 font-mono text-[11px] text-[#64748B] sm:flex-row sm:items-center">
            <span>
              WTO/UNCTAD ITC MAcMap (5,612 HS-6) · CMA CGM July 2026 Tariff ·
              Air-Gapped Docker Stack
            </span>
            <span>
              © {new Date().getFullYear()} CustomsGuard. All rights reserved.
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

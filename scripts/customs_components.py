import datetime
import json
import os
import smtplib
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
from langchain_core.tools import BaseTool, Tool, tool

try:
  from langflow.custom import Component
  from langflow.io import Output
except ImportError:

  class Component:
    pass

  class Output:

    def __init__(self, **kwargs):
      self.__dict__.update(kwargs)


# CMA CGM Indonesia Merged Import Demurrage & Detention Tariff (Effective July 1, 2026)
# Standard Dry: 5 Free Days. Slabs: D6-10, D11-15, D16-20, D21+
# Reefer: 3 Free Days. Slabs: D4-5, D6-7, D8+
CMA_CGM_TARIFFS = {
    "DRY": {
        "free_days": 5,
        "slabs": [
            {"max_day": 5, "rates": {"20": 0.0, "40": 0.0, "45": 0.0}},
            {"max_day": 10, "rates": {"20": 66.0, "40": 101.0, "45": 141.0}},
            {"max_day": 15, "rates": {"20": 86.0, "40": 121.0, "45": 171.0}},
            {"max_day": 20, "rates": {"20": 96.0, "40": 151.0, "45": 181.0}},
            {"max_day": 999, "rates": {"20": 106.0, "40": 161.0, "45": 191.0}},
        ],
    },
    "REEFER": {
        "free_days": 3,
        "slabs": [
            {"max_day": 3, "rates": {"20": 0.0, "40": 0.0, "45": 0.0}},
            {"max_day": 5, "rates": {"20": 89.0, "40": 141.0, "45": 141.0}},
            {"max_day": 7, "rates": {"20": 126.0, "40": 176.0, "45": 176.0}},
            {"max_day": 999, "rates": {"20": 130.0, "40": 180.0, "45": 180.0}},
        ],
    },
}


def calculate_cma_cgm_demurrage(
    container_count: int = 1,
    container_size: str = "40",
    container_type: str = "DRY",
    days_held_projected: int = 10,
    container_detention_risk: bool = True,
) -> dict:
  """Calculates demurrage and detention liabilities using official CMA CGM Indonesia tariffs."""
  normalized_type = "REEFER" if "REEF" in str(container_type).upper() else "DRY"
  normalized_size = (
      "20" if "20" in str(container_size) else ("45" if "45" in str(container_size) else "40")
  )
  tariff = CMA_CGM_TARIFFS[normalized_type]
  free_days = tariff["free_days"]

  if not container_detention_risk:
    return {
        "benchmark_carrier": "CMA CGM Indonesia (Merged Import D&D Tariff)",
        "container_size": f"{normalized_size}ft",
        "container_type": f"Standard {normalized_type.capitalize()}",
        "container_count": container_count,
        "free_days_allowed": free_days,
        "days_projected": days_held_projected,
        "detention_days": 0,
        "daily_rate_per_container_usd": 0.0,
        "daily_burn_rate_total_usd": 0.0,
        "projected_cumulative_liability_usd": 0.0,
        "applicable_slab": f"Within free time allowance ({free_days} free days)",
        "carrier_policy_notes": (
            "Merged D&D clock (terminal + depot). Carrier group covers CMA CGM, APL, CNC, ANL."
        ),
    }

  cumulative_per_container = 0.0
  active_daily_rate = 0.0
  active_slab_name = ""

  for day in range(1, days_held_projected + 1):
    day_rate = 0.0
    for slab in tariff["slabs"]:
      if day <= slab["max_day"]:
        day_rate = slab["rates"].get(normalized_size, slab["rates"]["40"])
        if day == days_held_projected:
          active_daily_rate = day_rate
          if normalized_type == "DRY":
            if slab["max_day"] == 5:
              active_slab_name = "Days 1 to 5 (Free)"
            elif slab["max_day"] == 10:
              active_slab_name = f"Days 6 to 10 (${day_rate:.2f}/day)"
            elif slab["max_day"] == 15:
              active_slab_name = f"Days 11 to 15 (${day_rate:.2f}/day)"
            elif slab["max_day"] == 20:
              active_slab_name = f"Days 16 to 20 (${day_rate:.2f}/day)"
            else:
              active_slab_name = f"Days 21+ (${day_rate:.2f}/day)"
          else:
            if slab["max_day"] == 3:
              active_slab_name = "Days 1 to 3 (Free)"
            elif slab["max_day"] == 5:
              active_slab_name = f"Days 4 to 5 (${day_rate:.2f}/day)"
            elif slab["max_day"] == 7:
              active_slab_name = f"Days 6 to 7 (${day_rate:.2f}/day)"
            else:
              active_slab_name = f"Days 8+ (${day_rate:.2f}/day)"
        break
    cumulative_per_container += day_rate

  daily_burn_rate_total = round(active_daily_rate * container_count, 2)
  total_cumulative = round(cumulative_per_container * container_count, 2)
  detention_days = max(0, days_held_projected - free_days)

  return {
      "benchmark_carrier": "CMA CGM Indonesia (Merged Import D&D Tariff)",
      "container_size": f"{normalized_size}ft",
      "container_type": f"Standard {normalized_type.capitalize()}",
      "container_count": container_count,
      "free_days_allowed": free_days,
      "days_projected": days_held_projected,
      "detention_days": detention_days,
      "daily_rate_per_container_usd": active_daily_rate,
      "daily_burn_rate_total_usd": daily_burn_rate_total,
      "projected_cumulative_liability_usd": total_cumulative,
      "applicable_slab": active_slab_name,
      "carrier_policy_notes": (
          "Merged D&D clock (terminal + depot). Carrier group covers CMA CGM, APL, CNC, ANL."
      ),
  }


def format_markdown_dossier(
    shipment_id: str,
    audit_summary_json: str,
    generated_at: str,
    md_path: str = "",
) -> str:
  """Formats a structured, human-readable Markdown compliance dossier from audit JSON."""
  try:
    data = json.loads(audit_summary_json)
    if not isinstance(data, dict):
      raise ValueError("Payload is not a JSON object")
  except Exception:
    return (
        "# CustomsGuard Compliance Audit Report\n\n"
        f"**Shipment ID**: {shipment_id}  \n"
        f"**Generated At**: {generated_at}  \n\n"
        f"```json\n{audit_summary_json}\n```\n"
    )

  verdict = data.get("overall_status", "UNKNOWN")
  importer = data.get("importer") or data.get("importer_name") or "UNKNOWN"
  destination_port = data.get(
      "destination_port", "Tanjung Priok, Jakarta (IDTPP)"
  )
  container_count = data.get("container_count", 1)
  detention_risk = bool(data.get("container_detention_risk", False))
  shortfall = float(data.get("total_duty_shortfall_usd", 0.0))
  restitution = float(data.get("total_restitution_usd", 0.0))
  daily_demurrage = float(data.get("estimated_demurrage_per_day_usd", 0.0))

  demurrage = data.get("demurrage_assessment") or {}
  carrier_benchmark = demurrage.get(
      "benchmark_carrier", "CMA CGM Indonesia (Merged Import D&D Tariff)"
  )
  container_size = demurrage.get("container_size", "40ft")
  container_type = demurrage.get("container_type", "Standard Dry")
  free_days = demurrage.get("free_days_allowed", 5)
  detention_days = demurrage.get(
      "detention_days", 5 if detention_risk else 0
  )
  try:
    count_num = max(1, int(container_count))
  except (ValueError, TypeError):
    count_num = 1
  daily_per_container = float(
      demurrage.get(
          "daily_rate_per_container_usd",
          daily_demurrage / count_num if detention_risk else 0.0,
      )
  )
  projected_liability = float(
      demurrage.get(
          "projected_cumulative_liability_usd",
          daily_demurrage * detention_days,
      )
  )
  applicable_slab = demurrage.get(
      "applicable_slab",
      "Slab 1"
      if detention_risk
      else f"Within free time allowance ({free_days} free days)",
  )

  critical_notes = data.get("critical_notes") or []
  findings = data.get("findings") or []

  lines = [
      "# CustomsGuard Compliance Audit Report",
      "",
      f"**Shipment ID**: {shipment_id}  ",
      f"**Generated At**: {generated_at}  ",
      f"**Verdict**: {verdict}",
      "",
      "### Executive Summary",
      "",
      f"- **Importer**: {importer}",
      f"- **Destination Port**: {destination_port}",
      f"- **Container Count**: {container_count} ({container_size} {container_type})",
      f"- **Container Detention Risk**: {'YES' if detention_risk else 'NO'}",
      f"- **Total Duty Shortfall**: ${shortfall:,.2f} USD",
      f"- **Potential Duty Restitution Savings**: ${restitution:,.2f} USD",
      f"- **Carrier Benchmark**: {carrier_benchmark}",
      f"- **Free Time Allowed**: {free_days} Days Free",
      f"- **Estimated Daily Demurrage**: ${daily_demurrage:,.2f} USD / day (${daily_per_container:,.2f}/day per container, {applicable_slab})",
      f"- **Projected {detention_days}-Day Hold Liability**: ${projected_liability:,.2f} USD",
      "",
      "### Critical Discrepancies & Regulatory Violations",
      "",
  ]

  if critical_notes:
    for idx, note in enumerate(critical_notes, start=1):
      lines.append(f"{idx}. {note}")
  elif verdict != "COMPLIANT":
    lines.append(
        f"1. Compliance status flagged as `{verdict}` with total duty shortfall of ${shortfall:,.2f} USD."
    )
  else:
    lines.append(
        "1. Classification, tariff duty rate, and regulatory import requirements verified with zero discrepancies."
    )

  lines.extend([
      "",
      "### Itemized Audit Findings",
      "",
      "| Item ID | Declared Description | Declared HS | Matched HS | Declared Duty | Official Duty | Shortfall (USD) | Restricted | Mandatory Permits |",
      "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
  ])

  if findings:
    for item in findings:
      item_id = item.get("item_id", 1)
      desc = item.get("declared_description", "-")
      dec_hs = item.get("declared_hs", "-")
      mat_hs = item.get("matched_hs", "-")
      dec_duty = float(item.get("declared_duty", 0.0))
      off_duty = float(item.get("official_duty", 0.0))
      item_shortfall = float(item.get("duty_shortfall_usd", 0.0))
      is_restricted = "Yes" if item.get("restricted") else "No"
      permits_list = item.get("required_permits") or []
      permits_str = ", ".join(permits_list) if permits_list else "None"
      lines.append(
          f"| {item_id} | {desc} | {dec_hs} | {mat_hs} | {dec_duty:.1f}% | {off_duty:.1f}% | ${item_shortfall:,.2f} | {is_restricted} | {permits_str} |"
      )
  else:
    lines.append(
        f"| 1 | Summary Audit Declaration | - | - | - | - | ${shortfall:,.2f} | {'Yes' if detention_risk else 'No'} | {'Required' if detention_risk else 'None'} |"
    )

  lines.extend([
      "",
      "### Automated Actions Taken",
      "",
  ])
  if md_path:
    lines.append(f"- Audit dossier generated on local disk at `{md_path}`.")
  else:
    lines.append("- Audit dossier generated on local disk.")

  if verdict != "COMPLIANT" or detention_risk:
    lines.append(
        "- Urgent detention alert email queued in Mailpit (`http://localhost:8025`)."
    )
  elif restitution > 0:
    lines.append(
        "- Tariff restitution opportunity recorded; clearance recommended with refund application."
    )
  else:
    lines.append("- Fast-track green lane release recommended.")

  return "\n".join(lines) + "\n"


def format_compliance_alert_body(
    shipment_id: str, verdict: str, alert_details: str
) -> str:
  """Formats a deterministic, structured plain-text email alert body for Mailpit."""
  importer = "Not specified"
  container_specs = "1x 40ft Standard Dry (Default)"
  shortfall_str = "See details below"
  daily_burn_str = "See details below"
  projected_str = "See details below"
  notes_lines = []

  parsed = None
  if isinstance(alert_details, dict):
    parsed = alert_details
  elif isinstance(alert_details, str):
    stripped = alert_details.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
      try:
        candidate = json.loads(stripped)
        if isinstance(candidate, dict):
          parsed = candidate
      except Exception:
        parsed = None

  if parsed is not None:
    importer = (
        parsed.get("importer") or parsed.get("importer_name") or "UNKNOWN"
    )
    demurrage = parsed.get("demurrage_assessment") or {}
    c_count = (
        parsed.get("container_count") or demurrage.get("container_count") or 1
    )
    c_size = demurrage.get("container_size", "40ft")
    c_type = demurrage.get("container_type", "Standard Dry")
    slab = demurrage.get("applicable_slab", "Active Slab")
    container_specs = f"{c_count}x {c_size} {c_type} ({slab})"

    shortfall_val = float(parsed.get("total_duty_shortfall_usd", 0.0))
    shortfall_str = f"${shortfall_val:,.2f} USD"

    daily_burn_val = float(
        parsed.get("estimated_demurrage_per_day_usd")
        or demurrage.get("daily_burn_rate_total_usd")
        or 0.0
    )
    daily_burn_str = f"${daily_burn_val:,.2f} USD / day"

    projected_val = float(
        demurrage.get("projected_cumulative_liability_usd", 0.0)
    )
    projected_str = f"${projected_val:,.2f} USD"

    raw_notes = parsed.get("critical_notes") or []
    if raw_notes:
      notes_lines = [f"- {n}" for n in raw_notes]
    else:
      notes_lines = [f"- Audit flagged status: {verdict}"]
  else:
    details_text = str(alert_details or "").strip()
    if details_text:
      for line in details_text.splitlines():
        clean = line.strip()
        if clean:
          notes_lines.append(clean if clean.startswith("-") else f"- {clean}")
    else:
      notes_lines = [f"- Audit flagged status: {verdict}"]

  formatted_notes = "\n".join(notes_lines)
  return (
      "====================================================================\n"
      "CUSTOMSGUARD AUTONOMOUS COMPLIANCE & DETENTION ALERT\n"
      "====================================================================\n\n"
      "SHIPMENT OVERVIEW\n"
      "-----------------\n"
      f"Shipment ID             : {shipment_id}\n"
      f"Official Verdict        : {verdict}\n"
      f"Importer                : {importer}\n"
      f"Container Specifications: {container_specs}\n\n"
      "FINANCIAL & DEMURRAGE EXPOSURE\n"
      "------------------------------\n"
      f"Total Duty Shortfall    : {shortfall_str}\n"
      f"CMA CGM Daily Burn Rate : {daily_burn_str}\n"
      f"Projected Hold Liability: {projected_str}\n\n"
      "CRITICAL DISCREPANCY NOTES\n"
      "--------------------------\n"
      f"{formatted_notes}\n\n"
      "RECOMMENDED ACTION\n"
      "------------------\n"
      "Hold cargo release pending human trade compliance verification and\n"
      "mandatory import license (Lartas) clearance.\n\n"
      "Preview in Mailpit: http://localhost:8025\n"
      "====================================================================\n"
  )


class CustomsGuardToolkitComponent(Component):
  display_name = "CustomsGuard Tools"
  description = "Suite of customs compliance audit, report export, and Mailpit alerting tools."
  icon = "ShieldCheck"
  name = "CustomsGuardToolkit"

  inputs = []
  outputs = [
      Output(
          name="tools",
          display_name="Tools",
          method="build_tools",
          types=["Tool"],
      ),
  ]

  def build_tools(self) -> List[BaseTool]:

    @tool
    def audit_shipment_compliance(invoice_json: str) -> str:
      """Audit commercial invoice items against local Qdrant customs tariff database
      to detect HS code discrepancies, duty shortfalls, missing import permits,
      and container detention risks.
      Takes an invoice_json string containing items and declarations.
      """
      try:
        data = json.loads(invoice_json)
      except Exception as e:
        return f"Error parsing invoice JSON: {e}"

      qdrant_url = (
          "http://qdrant:6333/collections/customs_tariffs/points/scroll"
      )
      findings = []
      overall_status = "COMPLIANT"
      total_duty_shortfall = 0.0
      total_restitution_usd = 0.0
      container_detention_risk = False
      critical_notes = []

      # Feature B: Extract container metadata for scaled demurrage liability
      try:
        container_count = max(1, int(data.get("container_count") or 1))
      except (ValueError, TypeError):
        container_count = 1

      container_size = str(data.get("container_size") or "40")
      container_type = str(data.get("container_type") or "DRY")
      try:
        days_held_projected = int(
            data.get("days_held_projected") or data.get("days_in_port") or 10
        )
      except (ValueError, TypeError):
        days_held_projected = 10

      items = data.get("items", [])
      if not items:
        critical_notes.append("No line items found in shipment declaration.")

      for item in items:
        declared_desc = str(item.get("declared_description") or "")
        declared_hs = str(item.get("declared_hs_code") or "")
        try:
          declared_duty = float(item.get("declared_duty_rate") or 0.0)
        except (ValueError, TypeError):
          declared_duty = 0.0
        try:
          total_val = float(item.get("total_value") or 0.0)
        except (ValueError, TypeError):
          total_val = 0.0

        desc_lower = declared_desc.lower()

        # Intelligent trade keyword selection (avoids brand false positives like Apple -> Apple juice)
        if any(
            w in desc_lower
            for w in ["iphone", "smartphone", "cellular", "mobile phone"]
        ):
          search_term = "smartphones"
        elif any(w in desc_lower for w in ["ultrasound", "ultrasonic"]):
          search_term = "ultrasonic"
        elif any(w in desc_lower for w in ["server", "processing unit"]):
          search_term = "8471.50"
        elif any(w in desc_lower for w in ["laptop", "notebook"]):
          search_term = "8471.30"
        elif any(w in desc_lower for w in ["t-shirt", "singlet", "vest"]):
          search_term = "6109.10"
        elif declared_desc.strip():
          search_term = declared_desc.split()[-1]
        else:
          search_term = declared_hs

        query_payload = json.dumps({
            "filter": {
                "must": [
                    {"key": "search_text", "match": {"text": search_term}}
                ]
            },
            "limit": 1,
        }).encode("utf-8")

        matched_code = declared_hs
        matched_duty = declared_duty
        restricted = False
        permits = []

        qdrant_endpoints = [
            "http://qdrant:6333/collections/customs_tariffs/points/scroll",
            "http://localhost:6333/collections/customs_tariffs/points/scroll",
        ]

        for qdrant_url in qdrant_endpoints:
          try:
            req = urllib.request.Request(
                qdrant_url,
                data=query_payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
              res = json.loads(resp.read().decode("utf-8"))
              points = res.get("result", {}).get("points", [])
              if points:
                matched = points[0]["payload"]
                matched_code = matched["hs_code"]
                matched_duty = float(matched["duty_rate"])
                restricted = matched.get("restricted", False)
                permits = matched.get("required_permits", [])
              break
          except Exception:
            continue

        code_diff = declared_hs != matched_code
        duty_diff = matched_duty - declared_duty
        restitution_usd = 0.0

        # Feature C: Distinct handling for duty shortfall vs duty overpayment restitution
        if duty_diff > 0:
          shortfall = (duty_diff / 100.0) * total_val
          total_duty_shortfall += shortfall
        elif duty_diff < 0:
          shortfall = 0.0
          overpayment = (abs(duty_diff) / 100.0) * total_val
          restitution_usd = overpayment
          total_restitution_usd += overpayment
          item_id = item.get("item_id", 1)
          critical_notes.append(
              f"Potential duty overpayment on item {item_id}: "
              f"Declared {declared_duty:.1f}% vs official {matched_duty:.1f}%. "
              f"Importer may qualify for customs duty restitution/refund of ${overpayment:,.2f}."
          )
        else:
          shortfall = 0.0

        if code_diff:
          overall_status = (
              "NON_COMPLIANT_HIGH_RISK" if restricted else "WARNING_DISCREPANCY"
          )
          if restricted:
            container_detention_risk = True
          critical_notes.append(
              f"Declared HS {declared_hs} conflicts with matched HS {matched_code}"
          )
          if permits:
            critical_notes.append(
                f"Missing mandatory regulatory permits: {', '.join(permits)}"
            )

        findings.append({
            "item_id": item.get("item_id", 1),
            "declared_description": declared_desc,
            "declared_hs": declared_hs,
            "matched_hs": matched_code,
            "declared_duty": declared_duty,
            "official_duty": matched_duty,
            "duty_shortfall_usd": shortfall,
            "restitution_usd": restitution_usd,
            "restricted": restricted,
            "required_permits": permits,
        })

      # Feature B: Grounded demurrage liability via official CMA CGM Indonesia Tariff
      demurrage_assessment = calculate_cma_cgm_demurrage(
          container_count=container_count,
          container_size=container_size,
          container_type=container_type,
          days_held_projected=days_held_projected,
          container_detention_risk=container_detention_risk,
      )
      daily_demurrage = demurrage_assessment["daily_burn_rate_total_usd"]

      if container_detention_risk:
        critical_notes.append(
            f"CMA CGM Demurrage & Detention risk active: "
            f"{demurrage_assessment['container_size']} {demurrage_assessment['container_type']} "
            f"({demurrage_assessment['applicable_slab']}). "
            f"Consignment burn rate: ${daily_demurrage:,.2f}/day "
            f"(${demurrage_assessment['daily_rate_per_container_usd']:,.2f}/day/container). "
            f"Projected {demurrage_assessment['detention_days']}-day hold liability: "
            f"${demurrage_assessment['projected_cumulative_liability_usd']:,.2f}."
        )

      result = {
          "shipment_id": data.get("shipment_id", "SHP-UNKNOWN"),
          "importer": data.get("importer_name", "UNKNOWN"),
          "carrier": data.get("carrier", "CMA CGM"),
          "destination_port": data.get(
              "destination_port", "Tanjung Priok, Jakarta (IDTPP)"
          ),
          "container_count": container_count,
          "overall_status": overall_status,
          "container_detention_risk": container_detention_risk,
          "total_duty_shortfall_usd": total_duty_shortfall,
          "total_restitution_usd": total_restitution_usd,
          "estimated_demurrage_per_day_usd": daily_demurrage,
          "demurrage_assessment": demurrage_assessment,
          "critical_notes": critical_notes,
          "findings": findings,
      }
      return json.dumps(result, indent=2)

    @tool
    def export_compliance_report(
        shipment_id: str, audit_summary_json: str
    ) -> str:
      """Generates and exports an official timestamped audit report in Markdown
      and JSON formats to local storage.
      Requires shipment_id and audit_summary_json string.
      """
      today = datetime.date.today().isoformat()
      base_dir = (
          "/app/reports" if os.path.exists("/app/reports") else "./data/reports"
      )
      target_dir = os.path.join(base_dir, today, shipment_id)
      os.makedirs(target_dir, exist_ok=True)

      json_path = os.path.join(target_dir, "audit_report.json")
      with open(json_path, "w", encoding="utf-8") as f:
        f.write(audit_summary_json)

      md_path = os.path.join(target_dir, "audit_report.md")
      generated_at = datetime.datetime.now().isoformat()
      md_content = format_markdown_dossier(
          shipment_id=shipment_id,
          audit_summary_json=audit_summary_json,
          generated_at=generated_at,
          md_path=md_path,
      )
      with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

      return f"Audit report successfully exported to: {md_path}"

    @tool
    def send_compliance_alert(
        shipment_id: str, verdict: str, alert_details: str
    ) -> str:
      """Dispatches an urgent email alert via local Mailpit SMTP when
      high-risk customs discrepancies are detected.
      Takes shipment_id, verdict, and alert_details.
      """
      smtp_host = "mailpit"
      smtp_port = 1025
      sender = "alerts@customsguard.local"
      receiver = "compliance-officer@customsguard.local"

      msg = MIMEMultipart()
      msg["Subject"] = f"[CustomsGuard Alert] {verdict}: Shipment {shipment_id}"
      msg["From"] = sender
      msg["To"] = receiver

      body = format_compliance_alert_body(
          shipment_id=shipment_id,
          verdict=verdict,
          alert_details=alert_details,
      )
      msg.attach(MIMEText(body, "plain"))

      sent = False
      last_err = ""
      for smtp_host in ["mailpit", "localhost"]:
        try:
          with smtplib.SMTP(smtp_host, smtp_port, timeout=5) as server:
            server.sendmail(sender, [receiver], msg.as_string())
          sent = True
          break
        except Exception as e:
          last_err = str(e)

      if sent:
        return f"Alert email queued in Mailpit for {receiver}."
      return f"Failed to send email via Mailpit: {last_err}"

    return [
        audit_shipment_compliance,
        export_compliance_report,
        send_compliance_alert,
    ]
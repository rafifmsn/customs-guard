import datetime
import json
import os
import smtplib
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
from langchain_core.tools import BaseTool, Tool, tool
from langflow.custom import Component
from langflow.io import Output


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

        # Feature C: Distinct handling for duty shortfall vs duty overpayment restitution
        if duty_diff > 0:
          shortfall = (duty_diff / 100.0) * total_val
          total_duty_shortfall += shortfall
        elif duty_diff < 0:
          shortfall = 0.0
          overpayment = (abs(duty_diff) / 100.0) * total_val
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
          "container_count": container_count,
          "overall_status": overall_status,
          "container_detention_risk": container_detention_risk,
          "total_duty_shortfall_usd": total_duty_shortfall,
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
      with open(md_path, "w", encoding="utf-8") as f:
        f.write("# CustomsGuard Compliance Audit Report\n\n")
        f.write(f"**Shipment ID**: {shipment_id}  \n")
        f.write(
            f"**Generated At**: {datetime.datetime.now().isoformat()}  \n\n"
        )
        f.write(f"```json\n{audit_summary_json}\n```\n")

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

      body = (
          "CustomsGuard Compliance Notification\n"
          f"Shipment: {shipment_id}\n"
          f"Verdict: {verdict}\n\n"
          f"Details:\n{alert_details}\n\n"
          "Preview in Mailpit: http://localhost:8025\n"
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
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

      # Feature B: Extract container count for scaled demurrage liability
      try:
        container_count = max(1, int(data.get("container_count") or 1))
      except (ValueError, TypeError):
        container_count = 1

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

      # Feature B: Scale estimated demurrage by container_count ($350/day/container)
      daily_demurrage = (
          (350.0 * container_count) if container_detention_risk else 0.0
      )

      result = {
          "shipment_id": data.get("shipment_id", "SHP-UNKNOWN"),
          "importer": data.get("importer_name", "UNKNOWN"),
          "container_count": container_count,
          "overall_status": overall_status,
          "container_detention_risk": container_detention_risk,
          "total_duty_shortfall_usd": total_duty_shortfall,
          "estimated_demurrage_per_day_usd": daily_demurrage,
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
"""
PDF incident report generator for RAN-Copilot.

Uses ReportLab to build a compact incident report summarizing:
- KPI summary
- Alarm summary
- Backhaul summary
- Attach summary
- RCA result and recommended actions
"""

from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Table, TableStyle
from reportlab.lib import colors

# Import thresholds for pass/fail checking
try:
    from engine.rca import THRESHOLDS
except ImportError:
    THRESHOLDS = {}


def _p(text: str, style_name: str = "Normal"):
    styles = getSampleStyleSheet()
    return Paragraph(text.replace("\n", "<br/>"), styles[style_name])


def _clean_markdown(text: str) -> str:
    """
    Remove markdown formatting symbols and convert to plain text.
    """
    # Remove markdown headers (##, ###, etc.)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    # Remove bold markers (**text** -> text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    # Remove italic markers (*text* -> text, but be careful with bullet points)
    text = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'\1', text)
    # Remove list markers (- item -> item)
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    # Remove numbered list markers (1. item -> item)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    # Remove code blocks (```text``` -> text)
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    # Remove inline code (`text` -> text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Clean up multiple spaces
    text = re.sub(r' +', ' ', text)
    # Clean up multiple newlines
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    return text.strip()


def generate_incident_report_pdf(payload: Dict[str, Any]) -> bytes:
    """
    Build a PDF document from the incident-report payload coming from the UI.

    Expected keys in `payload` (all optional, best-effort):
      - siteId, timestampRange
      - kpiSummary
      - alarmSummary
      - backhaulSummary
      - attachSummary
      - rcaResult
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story: List[Any] = []

    site_id = payload.get("siteId", "Unknown Site")
    ts_range = payload.get("timestampRange") or {}
    start = ts_range.get("start") or "-"
    end = ts_range.get("end") or "-"

    story.append(_p(f"<b>RAN-Copilot Incident Report</b>", "Title"))
    story.append(Spacer(1, 12))
    story.append(_p(f"<b>Site:</b> {site_id}"))
    story.append(_p(f"<b>Time Window:</b> {start} → {end}"))
    story.append(Spacer(1, 12))

    # RCA section
    rca = payload.get("rcaResult") or {}
    if rca:
        story.append(_p("<b>Root Cause Analysis</b>", "Heading2"))
        story.append(_p(f"<b>Primary Root Cause:</b> {rca.get('root_cause', 'N/A')}"))
        story.append(_p(f"<b>Severity:</b> {rca.get('severity', 'N/A').upper() if rca.get('severity') else 'N/A'}"))
        story.append(Spacer(1, 8))

        # Add AI Summary if available
        ai_summary = rca.get("ai_summary")
        if ai_summary:
            story.append(_p("<b>AI Analysis Summary</b>", "Heading3"))
            # Clean markdown formatting from AI summary
            cleaned_summary = _clean_markdown(ai_summary)
            # Process line by line to handle structure properly
            lines = cleaned_summary.split("\n")
            current_para = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    # Empty line - flush current paragraph
                    if current_para:
                        story.append(_p(" ".join(current_para)))
                        current_para = []
                    story.append(Spacer(1, 4))
                elif ':' in line:
                    # Check if line has a label ending with colon
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        label = parts[0].strip()
                        content = parts[1].strip()
                        # Flush current paragraph first
                        if current_para:
                            story.append(_p(" ".join(current_para)))
                            current_para = []
                        # Bold the label part ending with colon
                        if content:
                            story.append(_p(f"<b>{label}:</b> {content}"))
                        else:
                            story.append(_p(f"<b>{label}:</b>"))
                    else:
                        # Line ends with colon but no content after
                        if current_para:
                            story.append(_p(" ".join(current_para)))
                            current_para = []
                        story.append(_p(f"<b>{line}</b>"))
                elif line.startswith('- ') or line.startswith('• '):
                    # List item - flush paragraph and add as list item
                    if current_para:
                        story.append(_p(" ".join(current_para)))
                        current_para = []
                    # Remove the bullet marker and add as hyphenated item
                    item_text = line[2:].strip() if len(line) > 2 else line
                    story.append(_p(f"- {item_text}"))
                else:
                    # Regular text line - check if it contains multiple action items that should be split
                    # Check for patterns that indicate multiple actions in one line
                    # Pattern 1: Numbered items (1. action 2. action)
                    if re.search(r'\d+\.\s+[A-Z]', line):
                        if current_para:
                            story.append(_p(" ".join(current_para)))
                            current_para = []
                        # Split by numbered patterns
                        items = re.split(r'\d+\.\s+', line)
                        items = [item.strip() for item in items if item.strip()]
                        for item in items:
                            story.append(_p(f"- {item}"))
                    # Pattern 2: Actions separated by common verbs (Check... Consider... Perform...)
                    elif re.search(r'\b(Check|Consider|Perform|Review|Ensure|Verify|Inspect|Monitor|Evaluate|Optimize)\s+[A-Z]', line, re.IGNORECASE):
                        # Try to split by action verbs
                        if current_para:
                            story.append(_p(" ".join(current_para)))
                            current_para = []
                        # Split by action verbs at start of sentences
                        items = re.split(r'(?=\b(?:Check|Consider|Perform|Review|Ensure|Verify|Inspect|Monitor|Evaluate|Optimize)\s+)', line, flags=re.IGNORECASE)
                        items = [item.strip() for item in items if item.strip() and len(item) > 5]
                        if len(items) > 1:
                            for item in items:
                                story.append(_p(f"- {item}"))
                        else:
                            current_para.append(line)
                    else:
                        # Regular text line
                        current_para.append(line)
            
            # Flush any remaining paragraph
            if current_para:
                story.append(_p(" ".join(current_para)))
            story.append(Spacer(1, 8))

        recs = rca.get("recommendations") or []
        if isinstance(recs, list) and recs:
            story.append(_p("<b>Recommended Actions</b>", "Heading3"))
            # Clean any markdown from recommendations
            cleaned_recs = [_clean_markdown(str(r)) for r in recs]
            story.append(
                ListFlowable(
                    [ListItem(_p(r)) for r in cleaned_recs],
                    bulletType="bullet",
                )
            )
        story.append(Spacer(1, 12))

    # KPI section
    if payload.get("kpiSummary"):
        story.append(_p("<b>KPI Summary</b>", "Heading2"))
        kpi_summary = payload["kpiSummary"]
        
        # Format KPI data as a table
        if isinstance(kpi_summary, dict):
            # Create table data with Status column
            table_data = [["KPI", "Mean", "Min", "Max", "Count", "Status"]]
            
            def check_kpi_status(kpi_name: str, mean_value: Any) -> tuple[str, colors.Color]:
                """Check if KPI passes or fails threshold, returns (status, color)"""
                threshold = THRESHOLDS.get(kpi_name)
                if not threshold or not isinstance(mean_value, (int, float)):
                    return ("-", colors.HexColor('#95A5A6'))  # Grey for no threshold
                
                if "min" in threshold:
                    if mean_value >= threshold["min"]:
                        return ("PASS", colors.HexColor('#27AE60'))  # Green
                    else:
                        return ("FAIL", colors.HexColor('#E74C3C'))  # Red
                elif "max" in threshold:
                    if mean_value <= threshold["max"]:
                        return ("PASS", colors.HexColor('#27AE60'))  # Green
                    else:
                        return ("FAIL", colors.HexColor('#E74C3C'))  # Red
                return ("-", colors.HexColor('#95A5A6'))  # Grey for no threshold
            
            for kpi_name, kpi_stats in kpi_summary.items():
                if isinstance(kpi_stats, dict):
                    mean = kpi_stats.get("mean", "N/A")
                    min_val = kpi_stats.get("min", "N/A")
                    max_val = kpi_stats.get("max", "N/A")
                    count = kpi_stats.get("count", "N/A")
                    
                    # Format numbers nicely
                    mean_str = mean
                    if isinstance(mean, (int, float)):
                        mean_str = f"{mean:.2f}" if isinstance(mean, float) else str(mean)
                    if isinstance(min_val, (int, float)):
                        min_val = f"{min_val:.2f}" if isinstance(min_val, float) else str(min_val)
                    if isinstance(max_val, (int, float)):
                        max_val = f"{max_val:.2f}" if isinstance(max_val, float) else str(max_val)
                    
                    # Check pass/fail status
                    status, status_color = check_kpi_status(kpi_name, mean if isinstance(mean, (int, float)) else None)
                    
                    table_data.append([kpi_name, mean_str, min_val, max_val, str(count), status])
            
            if len(table_data) > 1:  # If we have data rows
                table = Table(table_data, colWidths=[2.2*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.5*inch, 0.6*inch])
                
                # Build style with dynamic row colors for status column
                style_commands = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),  # Dark blue-grey header
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (4, -1), 'RIGHT'),  # Right-align numeric columns
                    ('ALIGN', (5, 0), (5, -1), 'CENTER'),  # Center-align Status column
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),  # Light grey grid
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTNAME', (5, 1), (5, -1), 'Helvetica-Bold'),  # Bold status text
                    ('TOPPADDING', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ]
                
                # Add status column background colors based on pass/fail
                for row_idx in range(1, len(table_data)):
                    kpi_name = table_data[row_idx][0]
                    mean_val = kpi_summary.get(kpi_name, {}).get("mean") if isinstance(kpi_summary.get(kpi_name), dict) else None
                    _, status_color = check_kpi_status(kpi_name, mean_val if isinstance(mean_val, (int, float)) else None)
                    style_commands.append(('BACKGROUND', (5, row_idx), (5, row_idx), status_color))
                    style_commands.append(('TEXTCOLOR', (5, row_idx), (5, row_idx), colors.white))
                
                # Add alternating row backgrounds (but preserve status column colors)
                for row_idx in range(1, len(table_data)):
                    if row_idx % 2 == 0:
                        style_commands.append(('BACKGROUND', (0, row_idx), (4, row_idx), colors.HexColor('#F8F9FA')))
                
                table.setStyle(TableStyle(style_commands))
                story.append(table)
            else:
                story.append(_p("No KPI data available"))
        else:
            story.append(_p(str(kpi_summary)))
        story.append(Spacer(1, 12))

    # Alarm section
    if payload.get("alarmSummary"):
        alarm_summary = payload["alarmSummary"]
        total = alarm_summary.get("total_count", 0)
        story.append(_p("<b>Alarm Summary</b>", "Heading2"))
        story.append(_p(f"Total alarms in window: {total}"))
        by_sev = alarm_summary.get("by_severity") or {}
        if by_sev:
            sev_lines = [f"{sev}: {count}" for sev, count in by_sev.items()]
            story.append(_p("By severity: " + ", ".join(sev_lines)))
        story.append(Spacer(1, 12))

    # Backhaul section
    if payload.get("backhaulSummary"):
        bh = payload["backhaulSummary"]
        story.append(_p("<b>Backhaul Summary</b>", "Heading2"))
        story.append(
            _p(
                f"Impairment score: {bh.get('impairment_score', 0.0) * 100:.1f}% "
                f"(samples: {bh.get('total_samples', 0)})"
            )
        )
        err = bh.get("error_summary") or {}
        if err:
            story.append(
                _p(
                    f"TX errors: {err.get('tx_errors', 0)}, "
                    f"RX errors: {err.get('rx_errors', 0)}"
                )
            )
        story.append(Spacer(1, 12))

    # Attach section
    if payload.get("attachSummary"):
        at = payload["attachSummary"]
        story.append(_p("<b>Attach Log Summary</b>", "Heading2"))
        rate = at.get("overall_attach_success_rate")
        if rate is not None:
            story.append(_p(f"Overall attach success rate: {rate:.1f}%"))
        dom = at.get("dominant_failure_category")
        if dom:
            story.append(_p(f"Dominant failure category: {dom}"))
        story.append(Spacer(1, 12))

    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data


__all__ = ["generate_incident_report_pdf"]



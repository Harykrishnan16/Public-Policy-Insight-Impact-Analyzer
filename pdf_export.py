"""
pdf_export.py
Generates a downloadable PDF summary of a bill analysis, matching the
platform's "Downloadable Summary in PDF form" deliverable.
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
    Table,
    TableStyle,
    HRFlowable,
)


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleBig", fontSize=18, leading=22, spaceAfter=10, textColor=colors.HexColor("#1a1a2e")))
    styles.add(ParagraphStyle(name="SectionHeading", fontSize=13, leading=16, spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#16213e")))
    styles.add(ParagraphStyle(name="Body", fontSize=10, leading=14))
    styles.add(ParagraphStyle(name="Meta", fontSize=9, leading=12, textColor=colors.grey))
    return styles


def build_pdf_report(analysis: dict) -> bytes:
    """Build a PDF summary report from an analysis dict and return its bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )
    styles = _styles()
    story = []

    # Title
    story.append(Paragraph(analysis.get("title", "Bill Summary"), styles["TitleBig"]))
    meta_bits = []
    if analysis.get("ministry"):
        meta_bits.append(f"Ministry: {analysis['ministry']}")
    if analysis.get("introduced_in"):
        meta_bits.append(f"Introduced in: {analysis['introduced_in']}")
    if analysis.get("introduction_date"):
        meta_bits.append(f"Introduced: {analysis['introduction_date']}")
    if meta_bits:
        story.append(Paragraph(" | ".join(meta_bits), styles["Meta"]))
    story.append(Paragraph(f"Report generated: {datetime.now().strftime('%d %b %Y, %H:%M')}", styles["Meta"]))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#cccccc"), spaceBefore=8, spaceAfter=10))

    # Objective
    if analysis.get("objective"):
        story.append(Paragraph("Objective", styles["SectionHeading"]))
        story.append(Paragraph(analysis["objective"], styles["Body"]))

    # Citizen summary
    if analysis.get("citizen_summary"):
        story.append(Paragraph("What This Means For You", styles["SectionHeading"]))
        story.append(Paragraph(analysis["citizen_summary"], styles["Body"]))

    # Key provisions
    if analysis.get("key_provisions"):
        story.append(Paragraph("Key Provisions", styles["SectionHeading"]))
        story.append(
            ListFlowable(
                [ListItem(Paragraph(p, styles["Body"])) for p in analysis["key_provisions"]],
                bulletType="bullet",
            )
        )

    # Chronology
    if analysis.get("chronology"):
        story.append(Paragraph("Timeline", styles["SectionHeading"]))
        rows = [["Date", "Event"]] + [[c.get("date", ""), c.get("event", "")] for c in analysis["chronology"]]
        t = Table(rows, colWidths=[3.5 * cm, 11.5 * cm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                ]
            )
        )
        story.append(t)

    # Sector impact
    if analysis.get("sector_impact"):
        story.append(Paragraph("Sector / Industry Impact", styles["SectionHeading"]))
        rows = [["Sector", "Impact", "Direction"]] + [
            [s.get("sector", ""), s.get("impact", ""), s.get("direction", "")]
            for s in analysis["sector_impact"]
        ]
        t = Table(rows, colWidths=[4 * cm, 8.5 * cm, 2.5 * cm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                ]
            )
        )
        story.append(t)

    # Impact forecast
    forecast = analysis.get("impact_forecast") or {}
    if forecast:
        story.append(Paragraph("Impact Forecast", styles["SectionHeading"]))
        for label, key in [("Short-term (0-1 yr)", "short_term"), ("Medium-term (1-5 yrs)", "medium_term"), ("Long-term (5+ yrs)", "long_term")]:
            if forecast.get(key):
                story.append(Paragraph(f"<b>{label}:</b> {forecast[key]}", styles["Body"]))
                story.append(Spacer(1, 4))

    # Positives / Negatives
    pos = analysis.get("positives") or []
    neg = analysis.get("negatives") or []
    if pos or neg:
        story.append(Paragraph("Positives and Negatives", styles["SectionHeading"]))
        max_len = max(len(pos), len(neg))
        rows = [["Positives", "Negatives"]]
        for i in range(max_len):
            rows.append([pos[i] if i < len(pos) else "", neg[i] if i < len(neg) else ""])
        t = Table(rows, colWidths=[7.5 * cm, 7.5 * cm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(t)

    # Risks & opportunities
    ro = analysis.get("risks_and_opportunities") or {}
    if ro.get("risks") or ro.get("opportunities"):
        story.append(Paragraph("Risks and Opportunities", styles["SectionHeading"]))
        if ro.get("risks"):
            story.append(Paragraph("<b>Risks:</b>", styles["Body"]))
            story.append(ListFlowable([ListItem(Paragraph(r, styles["Body"])) for r in ro["risks"]], bulletType="bullet"))
        if ro.get("opportunities"):
            story.append(Paragraph("<b>Opportunities:</b>", styles["Body"]))
            story.append(ListFlowable([ListItem(Paragraph(o, styles["Body"])) for o in ro["opportunities"]], bulletType="bullet"))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#cccccc")))
    story.append(
        Paragraph(
            "Generated by Bill Simplifier -- an AI-assisted civic literacy tool. "
            "This summary is for general understanding only and is not a substitute "
            "for the official Gazette text or legal advice.",
            styles["Meta"],
        )
    )

    doc.build(story)
    return buffer.getvalue()

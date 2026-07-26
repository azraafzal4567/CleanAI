"""
reports.py
----------
Export functionality for CleanAI:
- Cleaned dataset -> CSV bytes
- Cleaned dataset -> Excel bytes (XlsxWriter, styled header)
- Cleaning summary -> PDF report (ReportLab)
"""

from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

from utils.config import APP_NAME, APP_VERSION, COLOR_PRIMARY


# ----------------------------------------------------------------------------
# CSV EXPORT
# ----------------------------------------------------------------------------
def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert a dataframe to CSV bytes for download."""
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


# ----------------------------------------------------------------------------
# EXCEL EXPORT
# ----------------------------------------------------------------------------
def dataframe_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Cleaned Data") -> bytes:
    """Convert a dataframe to a styled Excel file (bytes) using XlsxWriter."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        header_format = workbook.add_format(
            {
                "bold": True,
                "font_color": "white",
                "bg_color": "#2563EB",
                "border": 1,
                "align": "center",
                "valign": "vcenter",
            }
        )
        cell_format = workbook.add_format({"border": 1})

        for col_num, column_name in enumerate(df.columns):
            worksheet.write(0, col_num, column_name, header_format)
            # NA-safe string length: newer pandas string dtypes can leave missing
            # values as NaN (not the text "nan") after .astype(str), which would
            # otherwise raise a TypeError when measuring length.
            str_lengths = df[column_name].apply(lambda v: len(str(v)) if pd.notna(v) else 0)
            max_len = max(str_lengths.max() if len(df) else 0, len(str(column_name))) + 4
            worksheet.set_column(col_num, col_num, min(max_len, 40), cell_format)

        worksheet.freeze_panes(1, 0)

    return buffer.getvalue()


# ----------------------------------------------------------------------------
# PDF CLEANING REPORT
# ----------------------------------------------------------------------------
def generate_pdf_report(
    file_name: str,
    profiling: dict,
    report: dict,
    column_report_df: pd.DataFrame,
    quality_score: float,
) -> bytes:
    """
    Generate a professional PDF cleaning report summarizing all actions taken.
    Returns the PDF as bytes, ready for st.download_button.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle", parent=styles["Title"], textColor=colors.HexColor(COLOR_PRIMARY), fontSize=22
    )
    heading_style = ParagraphStyle(
        "HeadingStyle", parent=styles["Heading2"], textColor=colors.HexColor(COLOR_PRIMARY), spaceBefore=14
    )
    normal_style = styles["Normal"]

    elements = []

    # Title block
    elements.append(Paragraph(f"{APP_NAME} {APP_VERSION} - Cleaning Report", title_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"File: {file_name or 'N/A'}", normal_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    elements.append(Paragraph(f"Overall Data Quality Score: {quality_score}/100", normal_style))
    elements.append(Spacer(1, 12))

    # Profiling summary table
    elements.append(Paragraph("Dataset Profile (Before Cleaning)", heading_style))
    profile_data = [
        ["Metric", "Value"],
        ["Total Rows", profiling.get("total_rows", "-")],
        ["Total Columns", profiling.get("total_columns", "-")],
        ["Missing Values", profiling.get("missing_values", "-")],
        ["Duplicate Rows", profiling.get("duplicate_rows", "-")],
        ["Duplicate Percentage", f"{profiling.get('duplicate_pct', '-')}%"],
    ]
    elements.append(_build_table(profile_data))
    elements.append(Spacer(1, 12))

    # Cleaning actions summary table
    elements.append(Paragraph("Cleaning Actions Summary", heading_style))
    actions_data = [
        ["Action", "Count"],
        ["Leading Spaces Removed", report.get("leading_spaces_removed", 0)],
        ["Extra Spaces Removed", report.get("extra_spaces_removed", 0)],
        ["Missing Text Replaced", report.get("missing_text_replaced", 0)],
        ["Missing Numeric Replaced", report.get("missing_numeric_replaced", 0)],
        ["Duplicate Rows Removed", report.get("duplicate_rows_removed", 0)],
        ["Emails Validated", report.get("emails_validated", 0)],
        ["Invalid Emails Found", report.get("invalid_emails", 0)],
        ["Phone Numbers Validated", report.get("phones_validated", 0)],
        ["Invalid Phone Numbers Found", report.get("invalid_phones", 0)],
        ["Dates Standardized", report.get("dates_standardized", 0)],
        ["Missing Dates Filled", report.get("dates_missing_filled", 0)],
    ]
    elements.append(_build_table(actions_data))
    elements.append(Spacer(1, 12))

    # Column-level report table
    elements.append(Paragraph("Column-Level Report", heading_style))
    if column_report_df is not None and not column_report_df.empty:
        safe_df = column_report_df.map(lambda v: str(v) if pd.notna(v) else "")
        col_data = [list(safe_df.columns)] + safe_df.values.tolist()
        elements.append(_build_table(col_data, col_widths=[3.2 * cm, 2.5 * cm, 2.3 * cm, 2.3 * cm, 6 * cm]))
    else:
        elements.append(Paragraph("No column-level data available.", normal_style))

    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph(
            f"Report generated automatically by {APP_NAME} {APP_VERSION} - Smart Data Cleaning Assistant.",
            ParagraphStyle("Footer", parent=normal_style, textColor=colors.grey, fontSize=8),
        )
    )

    doc.build(elements)
    return buffer.getvalue()


def _build_table(data: list, col_widths=None) -> Table:
    """Build a consistently styled ReportLab table."""
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLOR_PRIMARY)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table

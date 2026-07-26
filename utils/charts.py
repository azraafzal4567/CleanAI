"""
charts.py
---------
Plotly chart builders used on the Dashboard page:
- Missing values by column (bar chart)
- Data types distribution (donut chart)
- Duplicate vs unique rows (donut chart)
- Cleaning impact summary (bar chart)
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from utils.config import (
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_ACCENT,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_DANGER,
    CHART_COLOR_SEQUENCE,
    COLOR_TEXT_DARK,
)

CHART_FONT = dict(family="Segoe UI, Arial, sans-serif", size=13, color=COLOR_TEXT_DARK)


def _base_layout(title: str) -> dict:
    return dict(
        title=dict(text=title, font=dict(size=16, family=CHART_FONT["family"], color=COLOR_TEXT_DARK)),
        font=CHART_FONT,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=30, r=20, t=60, b=30),
        height=340,
    )


def missing_values_chart(df: pd.DataFrame) -> go.Figure:
    """Bar chart showing missing value counts per column."""
    missing_counts = df.isna().sum()
    missing_counts = missing_counts[missing_counts >= 0].sort_values(ascending=True)

    fig = go.Figure(
        go.Bar(
            x=missing_counts.values,
            y=missing_counts.index.astype(str),
            orientation="h",
            marker=dict(color=COLOR_PRIMARY, line=dict(width=0)),
            hovertemplate="%{y}: %{x} missing<extra></extra>",
        )
    )
    fig.update_layout(**_base_layout("Missing Values by Column"))
    fig.update_xaxes(title="Missing Count", gridcolor="#E5E7EB")
    fig.update_yaxes(title="")
    return fig


def dtypes_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Donut chart showing the distribution of column data types."""
    dtype_counts = df.dtypes.astype(str).value_counts()

    fig = go.Figure(
        go.Pie(
            labels=dtype_counts.index,
            values=dtype_counts.values,
            hole=0.55,
            marker=dict(colors=CHART_COLOR_SEQUENCE),
            textinfo="label+percent",
        )
    )
    fig.update_layout(**_base_layout("Data Types Distribution"))
    return fig


def duplicate_analysis_chart(total_rows: int, duplicate_rows: int) -> go.Figure:
    """Donut chart comparing unique vs duplicate rows."""
    unique_rows = max(total_rows - duplicate_rows, 0)

    fig = go.Figure(
        go.Pie(
            labels=["Unique Rows", "Duplicate Rows"],
            values=[unique_rows, duplicate_rows],
            hole=0.55,
            marker=dict(colors=[COLOR_SUCCESS, COLOR_DANGER]),
            textinfo="label+percent",
        )
    )
    fig.update_layout(**_base_layout("Duplicate Analysis"))
    return fig


def cleaning_impact_chart(report: dict) -> go.Figure:
    """Bar chart summarizing how many issues were fixed by each cleaning step."""
    labels = [
        "Leading/Trailing\nSpaces",
        "Extra Spaces",
        "Missing Text",
        "Missing Numeric",
        "Duplicate Rows",
        "Invalid Emails",
        "Invalid Phones",
        "Dates Filled",
    ]
    values = [
        report.get("leading_spaces_removed", 0),
        report.get("extra_spaces_removed", 0),
        report.get("missing_text_replaced", 0),
        report.get("missing_numeric_replaced", 0),
        report.get("duplicate_rows_removed", 0),
        report.get("invalid_emails", 0),
        report.get("invalid_phones", 0),
        report.get("dates_missing_filled", 0),
    ]

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker=dict(color=COLOR_SECONDARY),
            hovertemplate="%{x}: %{y}<extra></extra>",
        )
    )
    fig.update_layout(**_base_layout("Cleaning Impact Summary"))
    fig.update_yaxes(title="Count", gridcolor="#E5E7EB")
    return fig

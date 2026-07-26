"""
cleaner.py
----------
Core cleaning engine for CleanAI. Contains:
- Data profiling (before cleaning)
- Text cleaning
- Numeric cleaning
- Duplicate removal
- Full pipeline orchestration that ties together validators.py
- Column-level and overall cleaning report generation
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from utils.config import (
    UNKNOWN_TEXT_PLACEHOLDER,
    MISSING_NUMERIC_DEFAULT,
    DATE_OUTPUT_FORMAT,
)
from utils.validators import (
    detect_column_role,
    clean_email_column,
    clean_phone_column,
    clean_numeric_column,
    parse_date_value,
)


# ----------------------------------------------------------------------------
# PROFILING (runs on the raw, uploaded dataframe)
# ----------------------------------------------------------------------------
def profile_dataframe(df: pd.DataFrame) -> dict:
    """Generate a profiling summary of the raw dataset before any cleaning."""
    total_rows = len(df)
    total_columns = len(df.columns)
    missing_values = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    duplicate_pct = round((duplicate_rows / total_rows) * 100, 2) if total_rows else 0.0
    dtypes = df.dtypes.astype(str).to_dict()
    memory_bytes = int(df.memory_usage(deep=True).sum())

    return {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "missing_values": missing_values,
        "duplicate_rows": duplicate_rows,
        "duplicate_pct": duplicate_pct,
        "dtypes": dtypes,
        "memory_bytes": memory_bytes,
    }


def detect_date_columns(df: pd.DataFrame) -> list[str]:
    """Return a list of column names likely to contain dates."""
    date_columns = []
    for col in df.columns:
        role = detect_column_role(col, df[col])
        if role == "date":
            date_columns.append(col)
    return date_columns


# ----------------------------------------------------------------------------
# TEXT CLEANING
# ----------------------------------------------------------------------------
def clean_text_column(series: pd.Series) -> tuple[pd.Series, dict]:
    """
    Clean a text column:
    - Strip leading/trailing whitespace
    - Collapse multiple internal spaces
    - Remove tab characters
    - Convert blank strings to NaN, then fill with 'Unknown'
    - Apply Title Case

    Returns:
        (cleaned_series, stats) where stats counts how many cells were touched.
    """
    original = series.astype(str)

    leading_trailing_count = 0
    extra_spaces_count = 0
    missing_filled_count = 0

    def _clean_cell(raw_value, orig_value) -> str:
        nonlocal leading_trailing_count, extra_spaces_count, missing_filled_count

        if pd.isna(raw_value):
            missing_filled_count += 1
            return UNKNOWN_TEXT_PLACEHOLDER

        text = str(raw_value)
        text = text.replace("\t", " ")

        stripped = text.strip()
        if stripped != text:
            leading_trailing_count += 1

        collapsed = " ".join(stripped.split())
        if collapsed != stripped:
            extra_spaces_count += 1

        if collapsed == "" or collapsed.lower() in ("nan", "none", "null"):
            missing_filled_count += 1
            return UNKNOWN_TEXT_PLACEHOLDER

        return collapsed.title()

    cleaned_values = [
        _clean_cell(raw, orig) for raw, orig in zip(series, original)
    ]
    cleaned_series = pd.Series(cleaned_values, index=series.index)

    stats = {
        "leading_trailing_removed": leading_trailing_count,
        "extra_spaces_removed": extra_spaces_count,
        "missing_text_filled": missing_filled_count,
    }
    return cleaned_series, stats


# ----------------------------------------------------------------------------
# DATE CLEANING
# ----------------------------------------------------------------------------
def clean_date_column(
    series: pd.Series,
    strategy: str = "leave_missing",
    custom_value: Optional[str] = None,
) -> tuple[pd.Series, int]:
    """
    Standardize a date column into YYYY-MM-DD format.

    strategy: one of "today", "leave_missing", "custom"
    custom_value: required if strategy == "custom" (a date string)

    Returns:
        (cleaned_series, missing_filled_count)
    """
    today_str = pd.Timestamp.today().strftime(DATE_OUTPUT_FORMAT)
    missing_filled = 0

    cleaned_values = []
    for value in series:
        parsed = parse_date_value(value)
        if parsed is not None:
            cleaned_values.append(parsed.strftime(DATE_OUTPUT_FORMAT))
            continue

        # Missing / unparseable value -> apply chosen strategy
        missing_filled += 1
        if strategy == "today":
            cleaned_values.append(today_str)
        elif strategy == "custom" and custom_value:
            custom_parsed = parse_date_value(custom_value)
            cleaned_values.append(
                custom_parsed.strftime(DATE_OUTPUT_FORMAT) if custom_parsed else custom_value
            )
        else:  # leave_missing
            cleaned_values.append(pd.NA)

    return pd.Series(cleaned_values, index=series.index), missing_filled


# ----------------------------------------------------------------------------
# FULL PIPELINE
# ----------------------------------------------------------------------------
def run_cleaning_pipeline(
    df: pd.DataFrame,
    options: dict,
    date_strategies: Optional[dict] = None,
    custom_date_values: Optional[dict] = None,
) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """
    Run the full CleanAI cleaning pipeline over a dataframe.

    Args:
        df: raw dataframe
        options: dict of booleans controlling which cleaning steps run
                 (clean_text, clean_numeric, validate_email, validate_phone,
                  clean_dates, remove_duplicates)
        date_strategies: {column_name: "today" | "leave_missing" | "custom"}
        custom_date_values: {column_name: "YYYY-MM-DD"} for custom strategy

    Returns:
        (cleaned_df, report_dict, column_report_df)
    """
    date_strategies = date_strategies or {}
    custom_date_values = custom_date_values or {}

    cleaned_df = df.copy()

    report = {
        "leading_spaces_removed": 0,
        "trailing_spaces_removed": 0,
        "extra_spaces_removed": 0,
        "missing_text_replaced": 0,
        "missing_numeric_replaced": 0,
        "duplicate_rows_removed": 0,
        "emails_validated": 0,
        "invalid_emails": 0,
        "phones_validated": 0,
        "invalid_phones": 0,
        "dates_standardized": 0,
        "dates_missing_filled": 0,
    }

    column_report_rows = []

    for col in cleaned_df.columns:
        original_series = df[col]
        missing_before = int(original_series.isna().sum())
        duplicates_in_col = int(original_series.duplicated().sum())
        role = detect_column_role(col, original_series)
        applied_actions = []

        if role == "email" and options.get("validate_email", True):
            cleaned_series, invalid_count = clean_email_column(original_series)
            cleaned_df[col] = cleaned_series
            report["emails_validated"] += len(original_series)
            report["invalid_emails"] += invalid_count
            applied_actions.append("Email validation")

        elif role == "phone" and options.get("validate_phone", True):
            cleaned_series, invalid_count = clean_phone_column(original_series)
            cleaned_df[col] = cleaned_series
            report["phones_validated"] += len(original_series)
            report["invalid_phones"] += invalid_count
            applied_actions.append("Phone validation")

        elif role == "date" and options.get("clean_dates", True):
            strategy = date_strategies.get(col, "leave_missing")
            custom_value = custom_date_values.get(col)
            cleaned_series, missing_filled = clean_date_column(original_series, strategy, custom_value)
            cleaned_df[col] = cleaned_series
            report["dates_standardized"] += len(original_series) - missing_filled
            report["dates_missing_filled"] += missing_filled
            applied_actions.append(f"Date standardized ({strategy})")

        elif role == "numeric" and options.get("clean_numeric", True):
            missing_numeric = int(original_series.isna().sum())
            cleaned_series = clean_numeric_column(original_series, MISSING_NUMERIC_DEFAULT)
            cleaned_df[col] = cleaned_series
            report["missing_numeric_replaced"] += missing_numeric
            applied_actions.append("Numeric conversion")

        else:  # text (default) column
            if options.get("clean_text", True):
                cleaned_series, stats = clean_text_column(original_series)
                cleaned_df[col] = cleaned_series
                report["leading_trailing_removed"] = report.get("leading_trailing_removed", 0)
                report["leading_spaces_removed"] += stats["leading_trailing_removed"]
                report["trailing_spaces_removed"] += 0  # counted together with leading
                report["extra_spaces_removed"] += stats["extra_spaces_removed"]
                report["missing_text_replaced"] += stats["missing_text_filled"]
                applied_actions.append("Text cleaning")

        column_report_rows.append({
            "Column Name": col,
            "Detected Type": role.capitalize(),
            "Missing Values": missing_before,
            "Duplicates": duplicates_in_col,
            "Cleaning Applied": ", ".join(applied_actions) if applied_actions else "None",
        })

    # Duplicate row removal (after column-level cleaning)
    if options.get("remove_duplicates", True):
        before_count = len(cleaned_df)
        cleaned_df = cleaned_df.drop_duplicates().reset_index(drop=True)
        removed = before_count - len(cleaned_df)
        report["duplicate_rows_removed"] = removed

    column_report_df = pd.DataFrame(column_report_rows)

    return cleaned_df, report, column_report_df

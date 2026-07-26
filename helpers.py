"""
helpers.py
----------
General-purpose helper functions used across the CleanAI app:
- Session state initialization / reset
- File reading (CSV / Excel) with error handling
- Memory usage formatting
- Data quality score calculation
- Small formatting utilities
"""

from __future__ import annotations

import io
from typing import Any, Optional

import pandas as pd
import streamlit as st


# ----------------------------------------------------------------------------
# SESSION STATE MANAGEMENT
# ----------------------------------------------------------------------------
DEFAULT_SESSION_STATE: dict[str, Any] = {
    "raw_df": None,               # original uploaded dataframe
    "cleaned_df": None,           # cleaned dataframe
    "file_name": None,            # original file name
    "file_size_kb": None,         # original file size in KB
    "cleaning_report": None,      # dict summary of cleaning actions
    "column_report": None,        # per-column report (DataFrame)
    "profiling": None,            # profiling dict (missing, duplicates, etc.)
    "date_columns": [],           # detected date columns
    "date_strategy": {},          # user chosen strategy per date column
    "custom_date_values": {},     # custom date value per column (if chosen)
    "cleaning_done": False,       # whether cleaning has been executed
    "invalid_emails_count": 0,
    "invalid_phones_count": 0,
    "duplicates_removed": 0,
    "cleaning_options": {
        "clean_text": True,
        "clean_numeric": True,
        "validate_email": True,
        "validate_phone": True,
        "clean_dates": True,
        "remove_duplicates": True,
    },
}


def init_session_state() -> None:
    """Initialize all required keys in st.session_state if not already present."""
    for key, default_value in DEFAULT_SESSION_STATE.items():
        if key not in st.session_state:
            # Use a fresh copy for mutable defaults (dict/list)
            if isinstance(default_value, (dict, list)):
                st.session_state[key] = type(default_value)(default_value)
            else:
                st.session_state[key] = default_value


def reset_session_state() -> None:
    """Completely reset the application to its initial state."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()


# ----------------------------------------------------------------------------
# FILE READING
# ----------------------------------------------------------------------------
def read_uploaded_file(uploaded_file) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Safely read an uploaded CSV or Excel file into a pandas DataFrame.

    Returns:
        (dataframe, error_message). If reading succeeds, error_message is None.
        If reading fails, dataframe is None and error_message describes the issue.
    """
    if uploaded_file is None:
        return None, "No file provided."

    file_name = uploaded_file.name
    extension = file_name.split(".")[-1].lower()

    try:
        if extension == "csv":
            # Try a few common encodings gracefully
            for encoding in ("utf-8", "latin1", "cp1252"):
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            else:
                return None, "Unable to decode CSV file. Please check the file encoding."
        elif extension == "xlsx":
            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        else:
            return None, f"Unsupported file type: .{extension}. Please upload a CSV or XLSX file."

        if df.empty:
            return None, "The uploaded file is empty."

        # Drop fully empty unnamed columns often created by stray commas
        df = df.loc[:, ~df.columns.astype(str).str.match(r"^Unnamed.*")]

        return df, None

    except Exception as exc:  # noqa: BLE001 - we want to catch and surface any error gracefully
        return None, f"Failed to read file: {exc}"


# ----------------------------------------------------------------------------
# FORMATTING UTILITIES
# ----------------------------------------------------------------------------
def format_memory_usage(df: pd.DataFrame) -> str:
    """Return a human-readable string of a DataFrame's memory usage."""
    if df is None:
        return "0 KB"
    total_bytes = df.memory_usage(deep=True).sum()
    return format_bytes(total_bytes)


def format_bytes(num_bytes: float) -> str:
    """Convert a byte count into a human-readable string (KB, MB, GB)."""
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024.0:
            return f"{num_bytes:,.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:,.2f} TB"


def get_uploaded_file_size_kb(uploaded_file) -> float:
    """Return the size of an uploaded file object in kilobytes."""
    uploaded_file.seek(0, io.SEEK_END)
    size_bytes = uploaded_file.tell()
    uploaded_file.seek(0)
    return round(size_bytes / 1024, 2)


# ----------------------------------------------------------------------------
# DATA QUALITY SCORE
# ----------------------------------------------------------------------------
def calculate_data_quality_score(
    total_cells: int,
    missing_cells: int,
    duplicate_rows: int,
    total_rows: int,
    invalid_emails: int = 0,
    invalid_phones: int = 0,
) -> float:
    """
    Calculate an overall data quality score (0-100) based on:
    - Completeness (missing values)
    - Uniqueness (duplicate rows)
    - Validity (invalid emails / phone numbers)

    The score is a weighted average of these three dimensions.
    """
    if total_cells == 0 or total_rows == 0:
        return 0.0

    completeness = 1 - (missing_cells / total_cells)
    uniqueness = 1 - (duplicate_rows / total_rows)

    invalid_total = invalid_emails + invalid_phones
    # Avoid division issues when there are no email/phone fields at all
    validity_penalty_base = max(total_rows, 1)
    validity = 1 - (invalid_total / validity_penalty_base)
    validity = max(validity, 0)

    score = (completeness * 0.5 + uniqueness * 0.3 + validity * 0.2) * 100
    return round(max(min(score, 100), 0), 1)


def quality_score_label(score: float) -> tuple[str, str]:
    """Return a (label, color) tuple describing the quality score band."""
    if score >= 90:
        return "Excellent", "#22C55E"
    if score >= 75:
        return "Good", "#3B82F6"
    if score >= 50:
        return "Fair", "#F59E0B"
    return "Needs Attention", "#EF4444"

"""
validators.py
--------------
Validation and conversion helpers:
- Email validation (email_validator)
- Phone number validation (regex + digit-length rule)
- Numeric string -> number conversion (including word numbers via word2number)
- Date column detection (dateutil)
"""

from __future__ import annotations

import re
from typing import Optional

import pandas as pd
from dateutil import parser as date_parser
from email_validator import validate_email, EmailNotValidError
from word2number import w2n

from utils.config import (
    EMAIL_KEYWORDS,
    PHONE_KEYWORDS,
    DATE_KEYWORDS,
    INVALID_EMAIL_PLACEHOLDER,
    INVALID_PHONE_PLACEHOLDER,
    VALID_PHONE_DIGIT_LENGTH,
)


# ----------------------------------------------------------------------------
# COLUMN TYPE DETECTION
# ----------------------------------------------------------------------------
def detect_column_role(column_name: str, series: pd.Series) -> str:
    """
    Heuristically classify a column as 'email', 'phone', 'date', 'numeric',
    or 'text' based on the column name and a sample of its values.
    """
    name_lower = str(column_name).lower()

    if any(keyword in name_lower for keyword in EMAIL_KEYWORDS):
        return "email"
    if any(keyword in name_lower for keyword in PHONE_KEYWORDS):
        return "phone"
    if any(keyword in name_lower for keyword in DATE_KEYWORDS):
        return "date"

    # Fallback: sample non-null values to guess type
    sample = series.dropna().astype(str).head(20)
    if sample.empty:
        return "text"

    email_hits = sample.str.contains(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", regex=True).mean()
    if email_hits > 0.5:
        return "email"

    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    numeric_like = sample.str.replace(",", "", regex=False).str.match(r"^-?\d+(\.\d+)?$").mean()
    if numeric_like > 0.6:
        return "numeric"

    date_hits = 0
    for value in sample:
        if is_probable_date(value):
            date_hits += 1
    if sample.shape[0] and (date_hits / sample.shape[0]) > 0.6:
        return "date"

    return "text"


def is_probable_date(value: str) -> bool:
    """Return True if a string value can plausibly be parsed as a date."""
    if not isinstance(value, str) or not value.strip():
        return False
    # Avoid false positives on plain integers (e.g. "20" parsed as a year)
    if re.match(r"^\d+(\.\d+)?$", value.strip()):
        return False
    try:
        date_parser.parse(value, fuzzy=False)
        return True
    except (ValueError, OverflowError, TypeError):
        return False


# ----------------------------------------------------------------------------
# EMAIL VALIDATION
# ----------------------------------------------------------------------------
def clean_email_value(value) -> tuple[str, bool]:
    """
    Clean and validate a single email value.

    Returns:
        (cleaned_value, was_valid)
    """
    if pd.isna(value) or str(value).strip() == "":
        return INVALID_EMAIL_PLACEHOLDER, False

    text = str(value).strip().lower()

    try:
        result = validate_email(text, check_deliverability=False)
        return result.normalized, True
    except EmailNotValidError:
        return INVALID_EMAIL_PLACEHOLDER, False


def clean_email_column(series: pd.Series) -> tuple[pd.Series, int]:
    """
    Apply email cleaning across an entire column.

    Returns:
        (cleaned_series, invalid_count)
    """
    cleaned_values = []
    invalid_count = 0
    for value in series:
        cleaned, is_valid = clean_email_value(value)
        cleaned_values.append(cleaned)
        if not is_valid:
            invalid_count += 1
    return pd.Series(cleaned_values, index=series.index), invalid_count


# ----------------------------------------------------------------------------
# PHONE VALIDATION
# ----------------------------------------------------------------------------
def clean_phone_value(value) -> tuple[str, bool]:
    """
    Clean and validate a single phone number value.
    Removes spaces, dashes, and parentheses, then checks digit length.

    Returns:
        (cleaned_value, was_valid)
    """
    if pd.isna(value) or str(value).strip() == "":
        return INVALID_PHONE_PLACEHOLDER, False

    text = str(value)
    # Remove spaces, dashes, parentheses
    text = re.sub(r"[\s\-\(\)]", "", text)
    # Keep leading + if present, strip other non-digits
    has_plus = text.startswith("+")
    digits_only = re.sub(r"\D", "", text)

    if len(digits_only) != VALID_PHONE_DIGIT_LENGTH:
        return INVALID_PHONE_PLACEHOLDER, False

    cleaned = ("+" if has_plus else "") + digits_only
    return cleaned, True


def clean_phone_column(series: pd.Series) -> tuple[pd.Series, int]:
    """
    Apply phone cleaning across an entire column.

    Returns:
        (cleaned_series, invalid_count)
    """
    cleaned_values = []
    invalid_count = 0
    for value in series:
        cleaned, is_valid = clean_phone_value(value)
        cleaned_values.append(cleaned)
        if not is_valid:
            invalid_count += 1
    return pd.Series(cleaned_values, index=series.index), invalid_count


# ----------------------------------------------------------------------------
# NUMERIC CONVERSION
# ----------------------------------------------------------------------------
def convert_to_number(value) -> Optional[float]:
    """
    Attempt to convert a value into a number, handling:
    - Plain numeric strings: "20" -> 20
    - Comma-separated thousands: "1,000" -> 1000
    - Word numbers: "twenty" -> 20
    Returns None if conversion is not possible.
    """
    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if text == "":
        return None

    # Remove thousands separators
    cleaned_text = text.replace(",", "")

    # Try direct numeric parse first
    try:
        return float(cleaned_text)
    except ValueError:
        pass

    # Try word-to-number conversion (e.g. "twenty" -> 20)
    try:
        return float(w2n.word_to_num(text.lower()))
    except (ValueError, ArithmeticError):
        return None


def clean_numeric_column(series: pd.Series, fill_value: float = 0) -> pd.Series:
    """Convert an entire column to numeric values, filling unparseable values."""
    converted = series.apply(convert_to_number)
    converted = converted.fillna(fill_value)
    return pd.to_numeric(converted, errors="coerce").fillna(fill_value)


# ----------------------------------------------------------------------------
# DATE PARSING
# ----------------------------------------------------------------------------
def parse_date_value(value) -> Optional[pd.Timestamp]:
    """Attempt to parse a single value into a pandas Timestamp."""
    if pd.isna(value) or str(value).strip() == "":
        return None
    try:
        return pd.Timestamp(date_parser.parse(str(value), fuzzy=False))
    except (ValueError, OverflowError, TypeError):
        return None

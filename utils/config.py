"""
config.py
----------
Central configuration file for CleanAI.
Holds color palette, app metadata, and constant values used across the app.
Keeping these in one place makes the UI easy to re-theme.
"""

from typing import Final

# ----------------------------------------------------------------------------
# APP METADATA
# ----------------------------------------------------------------------------
APP_NAME: Final[str] = "CleanAI"
APP_VERSION: Final[str] = "v1.0"
APP_TAGLINE: Final[str] = "Upload → Analyze → Clean → Download"
PAGE_TITLE: Final[str] = "CleanAI | Smart Data Cleaning Assistant"
PAGE_ICON: Final[str] = "🧹"

# ----------------------------------------------------------------------------
# COLOR PALETTE (Blue & White Professional Theme)
# ----------------------------------------------------------------------------
COLOR_PRIMARY: Final[str] = "#2563EB"
COLOR_SECONDARY: Final[str] = "#3B82F6"
COLOR_ACCENT: Final[str] = "#60A5FA"
COLOR_SUCCESS: Final[str] = "#22C55E"
COLOR_WARNING: Final[str] = "#F59E0B"
COLOR_DANGER: Final[str] = "#EF4444"
COLOR_BACKGROUND: Final[str] = "#F3F4F6"
COLOR_CARD: Final[str] = "#FFFFFF"
COLOR_TEXT_DARK: Final[str] = "#111827"
COLOR_TEXT_MUTED: Final[str] = "#6B7280"
COLOR_BORDER: Final[str] = "#E5E7EB"

CHART_COLOR_SEQUENCE: Final[list] = [
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_ACCENT,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_DANGER,
]

# ----------------------------------------------------------------------------
# CLEANING CONSTANTS
# ----------------------------------------------------------------------------
UNKNOWN_TEXT_PLACEHOLDER: Final[str] = "Unknown"
INVALID_EMAIL_PLACEHOLDER: Final[str] = "Invalid Email"
INVALID_PHONE_PLACEHOLDER: Final[str] = "Invalid Number"
MISSING_NUMERIC_DEFAULT: Final[float] = 0
VALID_PHONE_DIGIT_LENGTH: Final[int] = 11
DATE_OUTPUT_FORMAT: Final[str] = "%Y-%m-%d"

# Column name keyword hints used for heuristic type detection
EMAIL_KEYWORDS: Final[list] = ["email", "e-mail", "mail"]
PHONE_KEYWORDS: Final[list] = ["phone", "mobile", "contact", "cell", "whatsapp", "tel"]
DATE_KEYWORDS: Final[list] = ["date", "dob", "birth", "created", "updated", "joined", "time"]

# ----------------------------------------------------------------------------
# FILE SETTINGS
# ----------------------------------------------------------------------------
ALLOWED_EXTENSIONS: Final[list] = ["csv", "xlsx"]
MAX_FILE_SIZE_MB: Final[int] = 200
OUTPUT_DIR: Final[str] = "outputs"
SAMPLE_DATA_DIR: Final[str] = "sample_data"

# ----------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# ----------------------------------------------------------------------------
NAV_ITEMS: Final[list] = [
    ("📊 Dashboard", "Dashboard"),
    ("📁 Upload File", "Upload File"),
    ("⚙️ Cleaning Options", "Cleaning Options"),
    ("🔍 Preview", "Preview"),
    ("📄 Cleaning Report", "Cleaning Report"),
    ("⬇️ Download", "Download"),
    ("ℹ️ About", "About"),
]

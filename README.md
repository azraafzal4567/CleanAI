# 🧹 CleanAI v1.0 — Smart Data Cleaning Assistant

**Upload → Analyze → Clean → Download**

CleanAI is a production-ready Streamlit application that automatically detects and cleans common
data quality issues in CSV and Excel datasets — text formatting, numeric strings, invalid emails,
malformed phone numbers, inconsistent dates, and duplicate rows — all through a modern, premium
blue-and-white dashboard interface.

---

## ✨ Features

- **📁 Upload** — Drag-and-drop CSV or Excel (.xlsx) files with instant file summary (rows, columns, memory usage).
- **📊 Profiling Dashboard** — Total rows/columns, missing values, duplicate rows & percentage, data types, memory usage, and a data quality score — all visualized with Plotly charts.
- **🔤 Text Cleaning** — Strips leading/trailing/multiple spaces and tabs, fills blanks with `Unknown`, applies Title Case.
- **🔢 Numeric Cleaning** — Converts numeric strings ("20" → 20), comma-formatted numbers ("1,000" → 1000), and word numbers ("twenty" → 20); fills missing numerics with `0`.
- **📧 Email Validation** — Trims and lowercases addresses, validates format, replaces invalid entries with `Invalid Email`.
- **📱 Phone Validation** — Strips spaces/dashes/parentheses, validates 11-digit numbers, replaces invalid entries with `Invalid Number`.
- **📅 Date Standardization** — Auto-detects date columns and converts to `YYYY-MM-DD`. Because guessing missing dates is risky, CleanAI **always asks** you to choose: Today's Date, Leave Missing, or a Custom Date.
- **🧹 Duplicate Removal** — Detects and removes duplicate rows, reporting exactly how many were removed.
- **🔍 Preview** — Side-by-side original vs. cleaned dataset with highlighted changed cells.
- **📄 Cleaning Report** — Full column-by-column breakdown of detected type, missing values, duplicates, and cleaning actions applied.
- **⬇️ Multi-format Download** — Export the cleaned dataset as CSV, styled Excel, or a professional PDF cleaning report.
- **🔄 Full Reset** — One click returns the app to its initial state, clearing all uploaded data, reports, and session state.

---

## 🖥️ Screenshots

> _Add screenshots of the Dashboard, Upload, Cleaning Options, Preview, and Download pages here
> once you've run the app locally, e.g._
>
> `assets/screenshot-dashboard.png`
> `assets/screenshot-upload.png`
> `assets/screenshot-preview.png`

---

## 🚀 Installation
### 1. Clone the repository       
 ```bash
    git clone https://github.com/azraafzal4567/CleanAI.git
    cd CleanAI
```
### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

### 5. Try it with sample data
Use the file at `sample_data/sample_dataset.csv` to explore the app's features — it intentionally
contains messy text, malformed emails/phones, word numbers, and inconsistent dates.

---

## 📂 Project Structure

```
CleanAI/
├── app.py                  # Main Streamlit application (pages, UI, routing)
├── requirements.txt        # Python dependencies
├── README.md                # This file
├── assets/                 # Static assets (screenshots, images)
├── utils/
│   ├── __init__.py
│   ├── config.py            # Colors, constants, app metadata
│   ├── helpers.py           # Session state, file reading, formatting, quality score
│   ├── validators.py        # Email/phone/numeric/date validation & detection
│   ├── cleaner.py           # Core cleaning pipeline & profiling
│   ├── charts.py            # Plotly chart builders for the dashboard
│   └── reports.py           # CSV / Excel / PDF export logic
├── sample_data/
│   └── sample_dataset.csv   # Example messy dataset for testing
└── outputs/                 # (optional) local export destination
```

---

## 🧠 How Column Detection Works

CleanAI classifies each column as **email**, **phone**, **date**, **numeric**, or **text** using a
combination of column-name keywords (e.g. "email", "phone", "date") and content sampling. Detected
date columns are never auto-filled — you are always prompted to choose how missing or invalid dates
should be handled, since guessing dates can silently corrupt a dataset.

---

## 🎨 Design

- Primary `#2563EB` · Secondary `#3B82F6` · Accent `#60A5FA`
- Success `#22C55E` · Warning `#F59E0B`
- Light gray background, white rounded cards (15px radius) with soft shadows and hover animation
- Built to feel like a commercial SaaS analytics dashboard

---

## 🛠️ Tech Stack

Python 3.12+ · Streamlit · Pandas · NumPy · OpenPyXL · Plotly · Regex · word2number ·
python-dateutil · email-validator · phonenumbers · XlsxWriter · ReportLab

---

## 📄 License

This project is provided as-is for portfolio and educational use.

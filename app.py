"""
app.py
------
CleanAI v1.0 - Smart Data Cleaning Assistant
Main Streamlit application entry point.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.config import (
    APP_NAME,
    APP_VERSION,
    APP_TAGLINE,
    PAGE_TITLE,
    PAGE_ICON,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_ACCENT,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_DANGER,
    COLOR_BACKGROUND,
    COLOR_CARD,
    COLOR_TEXT_DARK,
    COLOR_TEXT_MUTED,
    COLOR_BORDER,
    NAV_ITEMS,
    ALLOWED_EXTENSIONS,
)
from utils.helpers import (
    init_session_state,
    reset_session_state,
    read_uploaded_file,
    format_memory_usage,
    format_bytes,
    get_uploaded_file_size_kb,
    calculate_data_quality_score,
    quality_score_label,
)
from utils.cleaner import profile_dataframe, detect_date_columns, run_cleaning_pipeline
from utils.charts import (
    missing_values_chart,
    dtypes_distribution_chart,
    duplicate_analysis_chart,
    cleaning_impact_chart,
)
from utils.reports import (
    dataframe_to_csv_bytes,
    dataframe_to_excel_bytes,
    generate_pdf_report,
)


# ==============================================================================
# PAGE CONFIG
# ==============================================================================
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_session_state()


# ==============================================================================
# CUSTOM CSS - premium blue & white theme
# ==============================================================================
def inject_custom_css() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {COLOR_BACKGROUND};
        }}

        /* Typography */
        html, body, [class*="css"] {{
            font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
        }}

        /* Hide default Streamlit chrome for a cleaner commercial look */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        /* Header banner */
        .cleanai-header {{
            background: linear-gradient(90deg, {COLOR_PRIMARY} 0%, {COLOR_SECONDARY} 100%);
            padding: 28px 34px;
            border-radius: 15px;
            color: white;
            margin-bottom: 22px;
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.25);
        }}
        .cleanai-header h1 {{
            margin: 0;
            font-size: 30px;
            font-weight: 700;
        }}
        .cleanai-header p {{
            margin: 6px 0 0 0;
            font-size: 15px;
            opacity: 0.92;
        }}

        /* Card container */
        .cleanai-card {{
            background-color: {COLOR_CARD};
            border-radius: 15px;
            padding: 22px 24px;
            box-shadow: 0 4px 14px rgba(17, 24, 39, 0.06);
            border: 1px solid {COLOR_BORDER};
            margin-bottom: 18px;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        .cleanai-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 22px rgba(17, 24, 39, 0.10);
        }}

        /* Metric card */
        .metric-card {{
            background-color: {COLOR_CARD};
            border-radius: 15px;
            padding: 18px 20px;
            border: 1px solid {COLOR_BORDER};
            box-shadow: 0 4px 12px rgba(17, 24, 39, 0.05);
            text-align: left;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            height: 100%;
        }}
        .metric-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(37, 99, 235, 0.12);
        }}
        .metric-card .metric-label {{
            color: {COLOR_TEXT_MUTED};
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            margin-bottom: 6px;
        }}
        .metric-card .metric-value {{
            color: {COLOR_TEXT_DARK};
            font-size: 28px;
            font-weight: 800;
        }}
        .metric-card .metric-icon {{
            font-size: 22px;
            margin-bottom: 4px;
        }}

        /* Section title */
        .section-title {{
            font-size: 20px;
            font-weight: 700;
            color: {COLOR_TEXT_DARK};
            margin: 10px 0 14px 0;
            border-left: 5px solid {COLOR_PRIMARY};
            padding-left: 10px;
        }}

        /* Buttons */
        .stButton>button {{
            border-radius: 10px;
            font-weight: 600;
            border: 1px solid {COLOR_PRIMARY};
            transition: all 0.15s ease;
        }}
        .stButton>button:hover {{
            background-color: {COLOR_PRIMARY};
            color: white;
            box-shadow: 0 6px 14px rgba(37, 99, 235, 0.25);
        }}

        /* Reset button special styling */
        div[data-testid="stSidebar"] .stButton>button {{
            width: 100%;
        }}

        /* Dataframe styling */
        [data-testid="stDataFrame"] {{
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid {COLOR_BORDER};
        }}

        /* Badge */
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def app_header() -> None:
    st.markdown(
        f"""
        <div class="cleanai-header">
            <h1>🧹 {APP_NAME} {APP_VERSION}</h1>
            <p>{APP_TAGLINE} &nbsp;|&nbsp; Smart Data Cleaning Assistant</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(col, icon: str, label: str, value: str, color: str = COLOR_PRIMARY) -> None:
    with col:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-icon">{icon}</div>
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="color:{color};">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# SIDEBAR
# ==============================================================================
def render_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align:center; padding: 8px 0 18px 0;">
                <div style="font-size:34px;">🧹</div>
                <div style="font-size:20px; font-weight:800; color:{COLOR_PRIMARY};">{APP_NAME}</div>
                <div style="font-size:12px; color:{COLOR_TEXT_MUTED};">{APP_VERSION}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        labels = [item[0] for item in NAV_ITEMS]
        keys = [item[1] for item in NAV_ITEMS]
        default_index = keys.index(st.session_state.get("active_page", "Dashboard")) \
            if st.session_state.get("active_page", "Dashboard") in keys else 0

        selected_label = st.radio("Navigation", labels, index=default_index, label_visibility="collapsed")
        selected_page = keys[labels.index(selected_label)]
        st.session_state["active_page"] = selected_page

        st.markdown("---")

        if st.session_state.get("raw_df") is not None:
            st.caption(f"📄 {st.session_state.get('file_name', 'N/A')}")
            st.caption(f"Rows: {len(st.session_state['raw_df']):,}")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Reset Application", use_container_width=True, type="secondary"):
            reset_session_state()
            st.rerun()

    return selected_page


# ==============================================================================
# PAGE: UPLOAD FILE
# ==============================================================================
def page_upload() -> None:
    st.markdown('<div class="section-title">📁 Upload Your Dataset</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="cleanai-card">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Drag and drop a CSV or Excel file here",
            type=ALLOWED_EXTENSIONS,
            help="Supported formats: .csv, .xlsx",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file is not None:
        with st.spinner("Reading file..."):
            df, error = read_uploaded_file(uploaded_file)

        if error:
            st.error(f"⚠️ {error}")
            return

        file_size_kb = get_uploaded_file_size_kb(uploaded_file)

        st.session_state["raw_df"] = df
        st.session_state["file_name"] = uploaded_file.name
        st.session_state["file_size_kb"] = file_size_kb
        st.session_state["profiling"] = profile_dataframe(df)
        st.session_state["date_columns"] = detect_date_columns(df)
        st.session_state["cleaning_done"] = False
        st.session_state["cleaned_df"] = None

        st.success(f"✅ File uploaded successfully: **{uploaded_file.name}**")

        st.markdown('<div class="section-title">File Summary</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        metric_card(c1, "📄", "File Name", uploaded_file.name[:22] + ("…" if len(uploaded_file.name) > 22 else ""))
        metric_card(c2, "📊", "Rows", f"{len(df):,}")
        metric_card(c3, "📐", "Columns", f"{len(df.columns):,}")
        metric_card(c4, "💾", "Memory Usage", format_memory_usage(df))

        st.markdown('<div class="section-title">Quick Preview</div>', unsafe_allow_html=True)
        st.dataframe(df.head(20), use_container_width=True)

        st.info("➡️ Head to **Cleaning Options** in the sidebar to configure and run the cleaning pipeline.")

    elif st.session_state.get("raw_df") is not None:
        df = st.session_state["raw_df"]
        st.success(f"✅ Currently loaded: **{st.session_state['file_name']}**")
        c1, c2, c3, c4 = st.columns(4)
        metric_card(c1, "📄", "File Name", st.session_state["file_name"][:22])
        metric_card(c2, "📊", "Rows", f"{len(df):,}")
        metric_card(c3, "📐", "Columns", f"{len(df.columns):,}")
        metric_card(c4, "💾", "Memory Usage", format_memory_usage(df))
        st.dataframe(df.head(20), use_container_width=True)
    else:
        st.info("👆 Upload a CSV or Excel file to get started.")


# ==============================================================================
# PAGE: CLEANING OPTIONS
# ==============================================================================
def page_cleaning_options() -> None:
    st.markdown('<div class="section-title">⚙️ Configure Cleaning Options</div>', unsafe_allow_html=True)

    if st.session_state.get("raw_df") is None:
        st.warning("⚠️ Please upload a file first from the **Upload File** page.")
        return

    df = st.session_state["raw_df"]

    st.markdown('<div class="cleanai-card">', unsafe_allow_html=True)
    st.markdown("##### Select cleaning modules to apply")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state["cleaning_options"]["clean_text"] = st.checkbox(
            "🔤 Text Cleaning", value=st.session_state["cleaning_options"]["clean_text"]
        )
        st.session_state["cleaning_options"]["clean_numeric"] = st.checkbox(
            "🔢 Numeric Cleaning", value=st.session_state["cleaning_options"]["clean_numeric"]
        )
    with col2:
        st.session_state["cleaning_options"]["validate_email"] = st.checkbox(
            "📧 Email Validation", value=st.session_state["cleaning_options"]["validate_email"]
        )
        st.session_state["cleaning_options"]["validate_phone"] = st.checkbox(
            "📱 Phone Validation", value=st.session_state["cleaning_options"]["validate_phone"]
        )
    with col3:
        st.session_state["cleaning_options"]["clean_dates"] = st.checkbox(
            "📅 Date Standardization", value=st.session_state["cleaning_options"]["clean_dates"]
        )
        st.session_state["cleaning_options"]["remove_duplicates"] = st.checkbox(
            "🧹 Remove Duplicate Rows", value=st.session_state["cleaning_options"]["remove_duplicates"]
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Date column handling (ambiguity requires explicit user input) ----
    date_columns = st.session_state.get("date_columns", [])
    if date_columns and st.session_state["cleaning_options"]["clean_dates"]:
        st.markdown('<div class="section-title">📅 Date Column Handling</div>', unsafe_allow_html=True)
        st.caption(
            "CleanAI detected the following date column(s). Missing or unparseable dates are "
            "ambiguous — please choose how each should be handled instead of letting the app guess."
        )
        st.markdown('<div class="cleanai-card">', unsafe_allow_html=True)
        for col in date_columns:
            st.markdown(f"**{col}**")
            choice = st.radio(
                f"How should missing/invalid dates in '{col}' be handled?",
                options=["Today's Date", "Leave Missing", "Custom Date"],
                key=f"date_strategy_radio_{col}",
                horizontal=True,
                label_visibility="collapsed",
            )
            strategy_map = {
                "Today's Date": "today",
                "Leave Missing": "leave_missing",
                "Custom Date": "custom",
            }
            st.session_state["date_strategy"][col] = strategy_map[choice]

            if choice == "Custom Date":
                custom_date = st.date_input(f"Custom date for '{col}'", key=f"custom_date_input_{col}")
                st.session_state["custom_date_values"][col] = str(custom_date)
            st.markdown("---")
        st.markdown("</div>", unsafe_allow_html=True)
    elif date_columns:
        st.info(f"📅 Date columns detected but Date Standardization is disabled: {', '.join(date_columns)}")

    # ---- Run cleaning ----
    st.markdown("<br>", unsafe_allow_html=True)
    run_col, _ = st.columns([1, 3])
    with run_col:
        run_clicked = st.button("🚀 Run Cleaning Pipeline", type="primary", use_container_width=True)

    if run_clicked:
        with st.spinner("Cleaning your data... this may take a moment."):
            cleaned_df, report, column_report_df = run_cleaning_pipeline(
                df,
                st.session_state["cleaning_options"],
                st.session_state["date_strategy"],
                st.session_state["custom_date_values"],
            )

        st.session_state["cleaned_df"] = cleaned_df
        st.session_state["cleaning_report"] = report
        st.session_state["column_report"] = column_report_df
        st.session_state["cleaning_done"] = True
        st.session_state["invalid_emails_count"] = report.get("invalid_emails", 0)
        st.session_state["invalid_phones_count"] = report.get("invalid_phones", 0)
        st.session_state["duplicates_removed"] = report.get("duplicate_rows_removed", 0)

        st.success("✅ Cleaning complete! Visit **Preview**, **Cleaning Report**, or **Download** to continue.")
        st.balloons()


# ==============================================================================
# PAGE: DASHBOARD
# ==============================================================================
def page_dashboard() -> None:
    st.markdown('<div class="section-title">📊 Dashboard</div>', unsafe_allow_html=True)

    if st.session_state.get("raw_df") is None:
        st.info("👆 Upload a dataset from the **Upload File** page to populate the dashboard.")
        return

    df = st.session_state["raw_df"]
    profiling = st.session_state.get("profiling") or profile_dataframe(df)
    cleaned_df = st.session_state.get("cleaned_df")
    report = st.session_state.get("cleaning_report") or {}

    invalid_emails = report.get("invalid_emails", 0)
    invalid_phones = report.get("invalid_phones", 0)
    rows_cleaned = (len(df) - len(cleaned_df)) if cleaned_df is not None else 0
    rows_cleaned = max(rows_cleaned, report.get("duplicate_rows_removed", 0))

    total_cells = profiling["total_rows"] * profiling["total_columns"]
    quality_score = calculate_data_quality_score(
        total_cells=total_cells,
        missing_cells=profiling["missing_values"],
        duplicate_rows=profiling["duplicate_rows"],
        total_rows=profiling["total_rows"],
        invalid_emails=invalid_emails,
        invalid_phones=invalid_phones,
    )
    score_label, score_color = quality_score_label(quality_score)

    # Metric cards row 1
    c1, c2, c3, c4 = st.columns(4)
    metric_card(c1, "📊", "Total Rows", f"{profiling['total_rows']:,}")
    metric_card(c2, "📐", "Columns", f"{profiling['total_columns']:,}")
    metric_card(c3, "❓", "Missing Values", f"{profiling['missing_values']:,}", COLOR_WARNING)
    metric_card(c4, "📑", "Duplicate Rows", f"{profiling['duplicate_rows']:,}", COLOR_DANGER)

    st.markdown("<br>", unsafe_allow_html=True)

    # Metric cards row 2
    c5, c6, c7, c8 = st.columns(4)
    metric_card(c5, "📧", "Invalid Emails", f"{invalid_emails:,}", COLOR_DANGER)
    metric_card(c6, "📱", "Invalid Numbers", f"{invalid_phones:,}", COLOR_DANGER)
    metric_card(c7, "🧹", "Rows Cleaned", f"{rows_cleaned:,}", COLOR_SUCCESS)
    metric_card(c8, "⭐", "Data Quality Score", f"{quality_score} ({score_label})", score_color)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown('<div class="cleanai-card">', unsafe_allow_html=True)
        st.plotly_chart(missing_values_chart(df), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with chart_col2:
        st.markdown('<div class="cleanai-card">', unsafe_allow_html=True)
        st.plotly_chart(dtypes_distribution_chart(df), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    chart_col3, chart_col4 = st.columns(2)
    with chart_col3:
        st.markdown('<div class="cleanai-card">', unsafe_allow_html=True)
        st.plotly_chart(
            duplicate_analysis_chart(profiling["total_rows"], profiling["duplicate_rows"]),
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with chart_col4:
        st.markdown('<div class="cleanai-card">', unsafe_allow_html=True)
        if report:
            st.plotly_chart(cleaning_impact_chart(report), use_container_width=True)
        else:
            st.info("Run the cleaning pipeline to see the cleaning impact chart.")
        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# PAGE: PREVIEW
# ==============================================================================
def page_preview() -> None:
    st.markdown('<div class="section-title">🔍 Data Preview</div>', unsafe_allow_html=True)

    if st.session_state.get("raw_df") is None:
        st.info("👆 Upload a dataset first from the **Upload File** page.")
        return

    df = st.session_state["raw_df"]
    cleaned_df = st.session_state.get("cleaned_df")

    st.markdown("##### Original Dataset")
    st.dataframe(df.head(50), use_container_width=True, height=300)

    st.markdown(
        f'<div style="text-align:center; font-size:26px; color:{COLOR_PRIMARY};">⬇️</div>',
        unsafe_allow_html=True,
    )

    st.markdown("##### Cleaned Dataset")
    if cleaned_df is not None:
        def highlight_changes(row):
            styles = []
            if row.name in df.index:
                for col in cleaned_df.columns:
                    try:
                        original_val = df.loc[row.name, col] if col in df.columns else None
                        changed = str(original_val) != str(row[col])
                    except Exception:
                        changed = False
                    styles.append(f"background-color: {COLOR_ACCENT}33" if changed else "")
            else:
                styles = ["" for _ in cleaned_df.columns]
            return styles

        try:
            styled = cleaned_df.head(50).style.apply(highlight_changes, axis=1)
            st.dataframe(styled, use_container_width=True, height=300)
        except Exception:
            st.dataframe(cleaned_df.head(50), use_container_width=True, height=300)

        st.caption("🟦 Highlighted cells indicate values that changed during cleaning.")
    else:
        st.warning("⚠️ No cleaned data yet. Go to **Cleaning Options** and run the pipeline.")


# ==============================================================================
# PAGE: CLEANING REPORT
# ==============================================================================
def page_cleaning_report() -> None:
    st.markdown('<div class="section-title">📄 Cleaning Report</div>', unsafe_allow_html=True)

    report = st.session_state.get("cleaning_report")
    column_report_df = st.session_state.get("column_report")

    if not st.session_state.get("cleaning_done") or report is None:
        st.warning("⚠️ No cleaning report available yet. Run the cleaning pipeline first.")
        return

    st.markdown('<div class="cleanai-card">', unsafe_allow_html=True)
    st.markdown("##### Summary of Actions")
    r1, r2, r3 = st.columns(3)
    with r1:
        st.metric("Leading Spaces Removed", report.get("leading_spaces_removed", 0))
        st.metric("Extra Spaces Removed", report.get("extra_spaces_removed", 0))
        st.metric("Missing Text Replaced", report.get("missing_text_replaced", 0))
    with r2:
        st.metric("Missing Numeric Replaced", report.get("missing_numeric_replaced", 0))
        st.metric("Duplicate Rows Removed", report.get("duplicate_rows_removed", 0))
        st.metric("Emails Validated", report.get("emails_validated", 0))
    with r3:
        st.metric("Phone Numbers Validated", report.get("phones_validated", 0))
        st.metric("Dates Standardized", report.get("dates_standardized", 0))
        st.metric("Missing Dates Filled", report.get("dates_missing_filled", 0))
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Column-Level Report</div>', unsafe_allow_html=True)
    if column_report_df is not None:
        st.dataframe(column_report_df, use_container_width=True)
    else:
        st.info("No column-level report available.")


# ==============================================================================
# PAGE: DOWNLOAD
# ==============================================================================
def page_download() -> None:
    st.markdown('<div class="section-title">⬇️ Download Your Results</div>', unsafe_allow_html=True)

    cleaned_df = st.session_state.get("cleaned_df")
    if cleaned_df is None:
        st.warning("⚠️ No cleaned data available yet. Run the cleaning pipeline first.")
        return

    file_base = (st.session_state.get("file_name") or "cleaned_data").rsplit(".", 1)[0]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="cleanai-card">', unsafe_allow_html=True)
        st.markdown("##### 📄 CSV File")
        st.caption("Download the cleaned dataset as a CSV file.")
        csv_bytes = dataframe_to_csv_bytes(cleaned_df)
        st.download_button(
            "Download CSV",
            data=csv_bytes,
            file_name=f"{file_base}_cleaned.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="cleanai-card">', unsafe_allow_html=True)
        st.markdown("##### 📊 Excel File")
        st.caption("Download the cleaned dataset as a styled Excel workbook.")
        excel_bytes = dataframe_to_excel_bytes(cleaned_df)
        st.download_button(
            "Download Excel",
            data=excel_bytes,
            file_name=f"{file_base}_cleaned.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="cleanai-card">', unsafe_allow_html=True)
        st.markdown("##### 📑 PDF Report")
        st.caption("Download a full cleaning summary report as PDF.")
        report = st.session_state.get("cleaning_report") or {}
        profiling = st.session_state.get("profiling") or {}
        column_report_df = st.session_state.get("column_report")

        total_cells = profiling.get("total_rows", 0) * profiling.get("total_columns", 0)
        quality_score = calculate_data_quality_score(
            total_cells=total_cells,
            missing_cells=profiling.get("missing_values", 0),
            duplicate_rows=profiling.get("duplicate_rows", 0),
            total_rows=profiling.get("total_rows", 0),
            invalid_emails=report.get("invalid_emails", 0),
            invalid_phones=report.get("invalid_phones", 0),
        )

        pdf_bytes = generate_pdf_report(
            file_name=st.session_state.get("file_name", "N/A"),
            profiling=profiling,
            report=report,
            column_report_df=column_report_df if column_report_df is not None else pd.DataFrame(),
            quality_score=quality_score,
        )
        st.download_button(
            "Download PDF Report",
            data=pdf_bytes,
            file_name=f"{file_base}_cleaning_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# PAGE: ABOUT
# ==============================================================================
def page_about() -> None:
    st.markdown('<div class="section-title">ℹ️ About CleanAI</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="cleanai-card">
        <p style="font-size:16px; color:{COLOR_TEXT_DARK};">
        <b>{APP_NAME} {APP_VERSION}</b> is a smart data cleaning assistant built for data analysts,
        students, and business teams who need fast, reliable dataset cleaning without writing code.
        </p>
        <p style="color:{COLOR_TEXT_MUTED};">{APP_TAGLINE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Key Features</div>', unsafe_allow_html=True)
    features = [
        ("🔤", "Text Cleaning", "Removes leading/trailing/multiple spaces, tabs, and standardizes casing."),
        ("🔢", "Numeric Cleaning", "Converts numeric strings, comma-formatted numbers, and word numbers."),
        ("📧", "Email Validation", "Validates and normalizes email addresses, flags invalid ones."),
        ("📱", "Phone Validation", "Strips formatting and validates numbers by digit length."),
        ("📅", "Date Standardization", "Detects date columns and standardizes to YYYY-MM-DD, asking before guessing."),
        ("📑", "Duplicate Removal", "Identifies and removes duplicate rows, reporting how many were removed."),
        ("📊", "Interactive Dashboard", "Visual profiling with Plotly charts and data quality scoring."),
        ("⬇️", "Multi-format Export", "Download cleaned data as CSV, Excel, or a full PDF report."),
    ]
    cols = st.columns(2)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 2]:
            st.markdown(
                f"""
                <div class="cleanai-card">
                    <div style="font-size:22px;">{icon} <b>{title}</b></div>
                    <div style="color:{COLOR_TEXT_MUTED}; font-size:14px; margin-top:6px;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-title">Tech Stack</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="cleanai-card">
        Python 3.12+, Streamlit, Pandas, NumPy, OpenPyXL, Plotly, Regex, word2number,
        python-dateutil, email-validator, phonenumbers, XlsxWriter, ReportLab.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# MAIN
# ==============================================================================
def main() -> None:
    inject_custom_css()
    app_header()

    active_page = render_sidebar()

    page_router = {
        "Dashboard": page_dashboard,
        "Upload File": page_upload,
        "Cleaning Options": page_cleaning_options,
        "Preview": page_preview,
        "Cleaning Report": page_cleaning_report,
        "Download": page_download,
        "About": page_about,
    }

    page_router.get(active_page, page_dashboard)()


if __name__ == "__main__":
    main()

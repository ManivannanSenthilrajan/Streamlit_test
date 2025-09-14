# app.py
import streamlit as st
import pandas as pd
import json
import os
from glob import glob
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Fund Explorer", page_icon="💹", layout="wide")

# Change these to match your environment
FUND_DATA_FOLDER = "./fund_data"            # folder containing excel files
COMMENTARY_FILE = "fund_commentary.json"    # persistent commentary store
LOG_FILE = "user_activity.json"             # persistent activity log

# Edit this mapping to point file names -> sheet names (strings or lists)
# Example: "filea.xlsx": "Sheet1"  or "fileb.xlsx": ["Sheet1","Sheet2"]
SHEET_MAPPING = {
    "filea.xlsx": "Sheet1",
    "fileb.xlsx": ["Sheet1", "Sheet2"],
    "filec.xlsx": "Sheet1"
}

# ---------------- STYLES (match screenshot: flat tabs, colors, font fallback) ----------------
st.markdown(
    """
    <style>
    /* Font + background */
    html, body, [class*="css"] {
        font-family: 'Frutiger', 'Verdana', 'Arial', sans-serif;
        background-color: #F5F5F5;
        color: #222;
    }

    /* Header */
    .app-header {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 8px 0;
        border-bottom: 1px solid #E6E6E6;
        margin-bottom: 12px;
    }
    .app-title { font-size: 1.6rem; font-weight: 600; color: #1f2937; margin:0; }

    /* Flat rectangular tabs (screenshot style) */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid #ddd;
        margin-bottom: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #F2F2F2 !important;  /* light/grey inactive */
        color: #222 !important;
        font-weight: 600;
        padding: 10px 14px !important;
        margin-right: 6px !important;
        border-radius: 4px 4px 0 0 !important;
        border: none !important;
    }
    .stTabs button[aria-selected="true"] {
        background-color: #8B3E2F !important;  /* reddish-brown selected */
        color: #ffffff !important;
        box-shadow: none !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #ECECEC !important;
    }

    /* Section card container like screenshot */
    .section-card {
        background: #ffffff;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
        margin-bottom: 12px;
    }

    /* Table header sticky */
    table.dataframe thead th {
        position: sticky;
        top: 0;
        background: #fafafa;
        z-index: 2;
    }
    /* Alternating row background */
    table.dataframe tbody tr:nth-child(even) td {
        background: #fbfbfb;
    }
    /* Commentary box */
    .comment-box {
        border: 1px solid #E6E6E6;
        background: #FFF;
        padding: 8px;
        border-radius: 6px;
        margin-bottom: 8px;
    }
    .timestamp { color: #6c757d; font-size: 0.85rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- HELPERS ----------------
def load_json_file(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def log_action(user, action, details=""):
    """Append a log entry (global list)."""
    logs = load_json_file(LOG_FILE, [])
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user if user else "",
        "action": action,
        "details": details
    }
    logs.append(entry)
    save_json_file(LOG_FILE, logs)

def add_comment(fund_name, comment, user):
    commentary = load_json_file(COMMENTARY_FILE, {})
    if fund_name not in commentary:
        commentary[fund_name] = []
    entry = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "user": user if user else "", "comment": comment}
    commentary[fund_name].append(entry)
    save_json_file(COMMENTARY_FILE, commentary)
    # log action with the exact comment in details (useful for history)
    log_action(user, "Added commentary", f"{fund_name}: {comment}")

def load_excel_files_from_folder(folder, sheet_mapping):
    """
    Load excel files from folder according to sheet_mapping.
    Returns dict: { "A (Sheet1)" : dataframe, ... }
    Each dataframe gets a column "Fund Name" with fund_name derived from filename (filea.xlsx -> A).
    Files not in sheet_mapping are silently skipped.
    """
    files = glob(os.path.join(folder, "*.xls*"))
    dataframes = {}
    if not files:
        return dataframes

    for file in files:
        fname = os.path.basename(file)
        # fund name from filename: remove extension, strip "file" prefix and uppercase
        fund_name = os.path.splitext(fname)[0].replace("file", "").upper()
        # Only load if file is present in mapping (silent skip otherwise)
        if fname not in sheet_mapping:
            continue
        sheets = sheet_mapping[fname]
        if isinstance(sheets, str):
            sheets = [sheets]
        try:
            xls = pd.ExcelFile(file)
        except Exception:
            # problem opening file -> skip
            continue
        for sheet in sheets:
            if sheet not in xls.sheet_names:
                # missing sheet in this file -> skip this sheet
                continue
            try:
                df = pd.read_excel(file, sheet_name=sheet)
            except Exception:
                continue
            if df is None or df.empty:
                continue
            df = df.copy()
            df["Fund Name"] = fund_name
            key = f"{fund_name} ({sheet})"
            dataframes[key] = df
    return dataframes

# ---------------- LOAD DATA ----------------
if not os.path.exists(FUND_DATA_FOLDER):
    st.error(f"Fund data folder not found: {FUND_DATA_FOLDER}")
    st.stop()

dataframes = load_excel_files_from_folder(FUND_DATA_FOLDER, SHEET_MAPPING)
if not dataframes:
    st.error("No data loaded. Check FUND_DATA_FOLDER and SHEET_MAPPING.")
    st.stop()

# commentary and logs (persistent)
commentary_data = load_json_file(COMMENTARY_FILE, {})
logs_data = load_json_file(LOG_FILE, [])

# combine selected dataframes (by source) into one combined_df for fund-level operations
# by default include all sources
default_sources = list(dataframes.keys())
# Sidebar: logo (optional), user, source filter, search
with st.sidebar:
    st.image("https://yourcompany.com/logo.png", width=140)  # replace with your logo URL or local path
    st.markdown("---")
    st.header("User")
    username = st.text_input("Name (for commentary & history):", value="")
    st.markdown("---")
    st.header("Data")
    selected_sources = st.multiselect("Choose source files (sheets):", options=default_sources, default=default_sources)
    if not selected_sources:
        st.warning("Pick at least one data source.")
    st.markdown("---")
    st.header("Filters")
    search_term = st.text_input("Search fund", value="").strip().lower()

# Build combined_df from selected_sources
filtered_dfs = [df for k, df in dataframes.items() if k in selected_sources]
if not filtered_dfs:
    st.stop()
combined_df = pd.concat(filtered_dfs, ignore_index=True, sort=False)

# fund list derived from Fund Name column (A, B, ...)
funds = sorted(combined_df["Fund Name"].unique())
if search_term:
    funds = [f for f in funds if search_term in f.lower()]
if not funds:
    st.warning("No funds match your filter.")
    # continue, but tabs will show no fund data

# ---------------- HEADER (left-aligned, screenshot style) ----------------
st.markdown(
    f"""
    <div class="app-header">
        <img src="https://yourcompany.com/logo.png" width="110" style="margin-right:12px;" />
        <div>
            <h1 class="app-title">Fund Explorer Dashboard</h1>
            <div style="color:#6b7280; font-size:0.9rem; margin-top:4px;">View • Compare • Comment</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------- TABS (flat rectangular style like screenshot) ----------------
tab_fund, tab_compare, tab_history = st.tabs(["Fund Details", "Compare Funds", "History"])

# ---------------- FUND DETAILS TAB ----------------
with tab_fund:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    selected_fund = st.selectbox("Select a fund to view", options=funds) if funds else None

    if selected_fund:
        # record view
        if username:
            log_action(username, "Viewed fund", selected_fund)

        # Existing commentary at top
        st.markdown("### 📝 Existing Commentary")
        comments = commentary_data.get(selected_fund, [])
        if comments:
            for c in reversed(comments):
                st.markdown(f"<div class='comment-box'><div class='timestamp'>{c['timestamp']} — {c.get('user','')}</div><div style='margin-top:6px'>{c['comment']}</div></div>", unsafe_allow_html=True)
        else:
            st.info("No commentary for this fund yet.")

        # Fund table (full)
        st.markdown("### 📄 Fund Data")
        fund_df = combined_df[combined_df["Fund Name"] == selected_fund]
        if not fund_df.empty:
            # wrap in horizontal scroll container
            st.markdown("<div style='overflow-x:auto'>", unsafe_allow_html=True)
            st.dataframe(fund_df.reset_index(drop=True), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("No data rows for this fund.")

        # New commentary at bottom using form (clear_on_submit avoids widget state issues)
        st.markdown("---")
        st.markdown("### ✍️ Add Commentary")
        form_key = f"form_fund_{selected_fund}"
        with st.form(key=form_key, clear_on_submit=True):
            new_comment = st.text_area("Write your commentary (visible to all users):", height=120)
            submitted = st.form_submit_button("Append Commentary")
            if submitted:
                if not username:
                    st.warning("Enter your name in the sidebar before adding commentary.")
                elif not new_comment.strip():
                    st.warning("Please enter a non-empty comment.")
                else:
                    add_comment(selected_fund, new_comment.strip(), username)
                    st.success("Comment added.")
                    # reload commentary_data and rerun so comment shows immediately
                    st.experimental_set_query_params(_r=int(datetime.now().timestamp()))  # harmless - forces rerun on some setups
                    st.rerun()
    else:
        st.info("No fund selected or no data available.")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- COMPARE FUNDS TAB ----------------
with tab_compare:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Compare multiple funds side-by-side")
    selected_funds = st.multiselect("Select funds to compare", options=funds)

    if selected_funds:
        if username:
            log_action(username, "Compared funds", ", ".join(selected_funds))

        # horizontally scrollable container with a narrow card per fund (full table inside each)
        st.markdown("<div style='display:flex; gap:12px; overflow-x:auto; padding-bottom:6px;'>", unsafe_allow_html=True)

        for fund in selected_funds:
            st.markdown("<div style='min-width:480px; flex:none;'>", unsafe_allow_html=True)
            st.markdown(f"<div style='background:#fff; padding:12px; border-radius:8px; box-shadow:0 6px 18px rgba(0,0,0,0.06);'>", unsafe_allow_html=True)
            st.markdown(f"#### {fund}")

            # existing commentary at top
            comments = commentary_data.get(fund, [])
            if comments:
                st.markdown("**📝 Existing Commentary**")
                for c in reversed(comments[-5:]):
                    st.markdown(f"<div class='comment-box'><div class='timestamp'>{c['timestamp']} — {c.get('user','')}</div><div style='margin-top:6px'>{c['comment']}</div></div>", unsafe_allow_html=True)
            else:
                st.info("No commentary yet.", icon="ℹ️")

            # full table
            fund_df = combined_df[combined_df["Fund Name"] == fund]
            if not fund_df.empty:
                st.markdown("<div style='overflow-x:auto'>", unsafe_allow_html=True)
                st.dataframe(fund_df.reset_index(drop=True), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("No data for this fund.")

            # add commentary at bottom with per-fund form
            st.markdown("---")
            form_key = f"form_compare_{fund}"
            with st.form(key=form_key, clear_on_submit=True):
                new_comment = st.text_area("Add commentary for this fund:", key=f"ta_{fund}", height=100)
                submitted = st.form_submit_button("Append Commentary")
                if submitted:
                    if not username:
                        st.warning("Enter your name in the sidebar before adding commentary.")
                    elif not new_comment.strip():
                        st.warning("Please write something before submitting.")
                    else:
                        add_comment(fund, new_comment.strip(), username)
                        st.success("Comment added.")
                        st.experimental_set_query_params(_r=int(datetime.now().timestamp()))
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)  # end inner card
            st.markdown("</div>", unsafe_allow_html=True)  # end min-width wrapper

        st.markdown("</div>", unsafe_allow_html=True)  # end horizontal container
    else:
        st.info("Select one or more funds to compare.")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- HISTORY TAB ----------------
with tab_history:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Activity History")
    logs = load_json_file(LOG_FILE, [])
    if logs:
        df_logs = pd.DataFrame(logs).sort_values("timestamp", ascending=False).reset_index(drop=True)
        st.dataframe(df_logs, use_container_width=True)
        st.download_button("Download CSV", df_logs.to_csv(index=False).encode("utf-8"), "activity_log.csv", mime="text/csv")
        st.download_button("Download JSON", json.dumps(logs, indent=2, ensure_ascii=False), "activity_log.json", mime="application/json")
    else:
        st.info("No activity logged yet.")
    st.markdown('</div>', unsafe_allow_html=True)

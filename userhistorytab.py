# app.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from glob import glob

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Fund Explorer", page_icon="💹", layout="wide")

FUND_DATA_FOLDER = "./fund_data"
COMMENTARY_FILE = "fund_commentary.json"
LOG_FILE = "user_activity.json"

# Map file name -> sheet (string) or list of sheets
# Example: adjust to match your actual filenames and sheet names
SHEET_MAPPING = {
    "filea.xlsx": "Sheet1",
    "fileb.xlsx": ["Funds", "OtherFunds"],  # example of multiple sheets from same file
    "filec.xlsx": "FundSheet"
}

# Optional: force a column name per file if the fund column has a nonstandard name
# e.g. { "filea.xlsx": "Fund_Title", "fileb.xlsx": "Fund" }
FILE_FUND_COL_MAPPING = {
    # "filea.xlsx": "Fund_Title",
}

# Candidate fund-name column labels to detect automatically (case-insensitive)
DEFAULT_FUND_COL_CANDIDATES = [
    "Fund Name", "FundName", "Fund", "fund_name", "fund", "Name", "Fund_Code", "Fund Code", "FundId", "Portfolio"
]

# ---------------- STYLES ----------------
st.markdown(
    """
    <style>
    .main { background-color: #f7f8fa; padding: 1.2rem; }
    .fund-card { background: white; padding: 1rem; margin-bottom: 1rem;
                 border-radius: 12px; box-shadow: 0 6px 18px rgba(0,0,0,0.06); }
    .comment-box { border: 1px solid #e6e6e6; border-radius: 8px; background: #fff; padding: 0.6rem; margin-bottom: 0.5rem; }
    .timestamp { color: #6c757d; font-size: 0.85rem; }
    .activity-log { font-size: 0.9rem; margin-bottom: 0.3rem; }
    .kpi { background: white; padding: 0.6rem; border-radius: 8px; box-shadow: 0 3px 8px rgba(0,0,0,0.04); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- HELPERS ----------------
def load_json_file(path):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_json_file(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def log_action(user, action, details=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logs = load_json_file(LOG_FILE)
    if user not in logs:
        logs[user] = []
    logs[user].append({"timestamp": timestamp, "action": action, "details": details})
    save_json_file(LOG_FILE, logs)

def get_user_logs(user):
    logs = load_json_file(LOG_FILE)
    return logs.get(user, [])

def add_comment(fund_name, comment, user):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commentary = load_json_file(COMMENTARY_FILE)
    if fund_name not in commentary:
        commentary[fund_name] = []
    commentary[fund_name].append({"timestamp": timestamp, "comment": comment, "user": user})
    save_json_file(COMMENTARY_FILE, commentary)
    log_action(user, "Added commentary", fund_name)

def _normalize_col_lookup(cols):
    """Return dict mapping lowercase trimmed col -> actual col name"""
    return {c.strip().lower(): c for c in cols}

def detect_fund_column(df, fname):
    """Try to detect fund column using (1) per-file override, (2) candidate names, (3) heuristics"""
    # 1) per-file override
    if fname in FILE_FUND_COL_MAPPING:
        candidate = FILE_FUND_COL_MAPPING[fname]
        # try exact or case-insensitive match
        for c in df.columns:
            if c.strip().lower() == candidate.strip().lower():
                return c
        # not found, proceed to detection but warn
        st.warning(f"FILE_FUND_COL_MAPPING for {fname} set to '{candidate}', but column not found. Will attempt auto-detection.")
    # 2) candidate list match (case-insensitive)
    lookup = _normalize_col_lookup(df.columns)
    for cand in DEFAULT_FUND_COL_CANDIDATES:
        key = cand.strip().lower()
        if key in lookup:
            return lookup[key]
    # 3) heuristic: a column that contains both 'fund' and 'name' or contains 'fund'
    for c in df.columns:
        lc = c.strip().lower()
        if "fund" in lc and "name" in lc:
            return c
    for c in df.columns:
        lc = c.strip().lower()
        if lc == "fund" or lc.startswith("fund") or "fund" in lc:
            return c
    # 4) heuristic: exact 'name' column
    for c in df.columns:
        if c.strip().lower() == "name":
            return c
    return None

def load_excel_files_from_folder(folder, sheet_mapping):
    """
    Loads specified sheets from Excel files and ensures each DataFrame has 'Fund Name' column.
    Returns dict: key => DataFrame (key looks like 'file.xlsx (Sheet1)')
    """
    files = glob(os.path.join(folder, "*.xls*"))
    dataframes = {}
    if not files:
        st.error(f"No excel files found in {folder}")
        return dataframes

    for file in files:
        fname = os.path.basename(file)
        if fname not in sheet_mapping:
            st.warning(f"Skipping {fname} (no entry in SHEET_MAPPING).")
            continue
        sheets = sheet_mapping[fname]
        if isinstance(sheets, str):
            sheets = [sheets]
        try:
            xls = pd.ExcelFile(file)
        except Exception as e:
            st.error(f"Could not open {fname}: {e}")
            continue

        for sheet in sheets:
            if sheet not in xls.sheet_names:
                st.warning(f"Sheet '{sheet}' not found in {fname}. Available: {xls.sheet_names}")
                continue
            try:
                df = pd.read_excel(file, sheet_name=sheet)
            except Exception as e:
                st.error(f"Could not read {fname} - {sheet}: {e}")
                continue

            if df.empty:
                st.warning(f"{fname} - {sheet} is empty, skipping.")
                continue

            fund_col = detect_fund_column(df, fname)
            if not fund_col:
                # show available columns so user can update FILE_FUND_COL_MAPPING for that file
                st.warning(
                    f"Could not detect fund-name column for {fname} - {sheet}. "
                    f"Available columns: {list(df.columns)}. Skipping this sheet."
                )
                continue

            # Standardize and ensure string type
            df = df.copy()
            df["Fund Name"] = df[fund_col].astype(str)
            dataframes[f"{fname} ({sheet})"] = df

    return dataframes

# ---------------- LOAD DATA ----------------
if not os.path.exists(FUND_DATA_FOLDER):
    st.error(f"Fund data folder not found: {FUND_DATA_FOLDER} (create it and add your excel files)")
    st.stop()

dataframes = load_excel_files_from_folder(FUND_DATA_FOLDER, SHEET_MAPPING)
if not dataframes:
    st.error("No data loaded. Check SHEET_MAPPING and FILE_FUND_COL_MAPPING, and examine warnings above.")
    st.stop()

commentary_data = load_json_file(COMMENTARY_FILE)

# ---------------- SIDEBAR (user + filters) ----------------
st.sidebar.header("👤 User")
username = st.sidebar.text_input("Enter your name", placeholder="e.g. Alice").strip()

st.sidebar.header("📂 Data source & filters")
available_sources = list(dataframes.keys())
selected_sources = st.sidebar.multiselect("Choose source file(s)", options=available_sources, default=available_sources)

if not selected_sources:
    st.warning("Select at least one data source on the sidebar.")
    st.stop()

search_term = st.sidebar.text_input("🔎 Search fund name (type and press Enter)").strip().lower()

# Show recent activity (last 5) in sidebar if username filled
if username:
    st.sidebar.subheader("📜 Recent activity")
    logs = get_user_logs(username)
    if logs:
        for entry in reversed(logs[-5:]):
            st.sidebar.markdown(
                f"<div class='activity-log'><span class='timestamp'>{entry['timestamp']}</span><br>"
                f"**{entry['action']}** — {entry['details']}</div>",
                unsafe_allow_html=True,
            )
    else:
        st.sidebar.write("No activity yet")

# ---------------- BUILD COMBINED DF ----------------
filtered_dfs = [df for k, df in dataframes.items() if k in selected_sources]
if not filtered_dfs:
    st.warning("No dataframes selected after filtering; choose at least one source.")
    st.stop()

combined_df = pd.concat(filtered_dfs, ignore_index=True, sort=False)

if "Fund Name" not in combined_df.columns:
    st.error("Internal error: 'Fund Name' not present after loading. Please check the sheet/column mapping.")
    st.stop()

# Apply search filter
funds = sorted(combined_df["Fund Name"].unique())
if search_term:
    funds = [f for f in funds if search_term in f.lower()]

if not funds:
    st.warning("No funds match your search/filter. Adjust search or selected files.")
    st.stop()

# ---------------- MAIN UI ----------------
st.markdown("<h1>💹 Fund Explorer</h1>", unsafe_allow_html=True)
st.markdown("Clean dashboard for viewing, comparing and commenting on funds. History and activity logging included.")

tab_details, tab_compare, tab_history = st.tabs(["🔍 Fund Details", "📊 Compare Funds", "📁 My History"])

# ---------------- TAB: Fund Details ----------------
with tab_details:
    selected_fund = st.selectbox("Select a fund", funds)
    if selected_fund:
        if username:
            log_action(username, "Viewed fund", selected_fund)

        fund_df = combined_df[combined_df["Fund Name"] == selected_fund]
        st.markdown(f"<div class='fund-card'><h3>📄 {selected_fund}</h3></div>", unsafe_allow_html=True)
        st.dataframe(fund_df, use_container_width=True)

        # Commentary
        st.markdown("### 📝 Commentary")
        prev_comments = commentary_data.get(selected_fund, [])
        if prev_comments:
            with st.expander("View previous commentary", expanded=True):
                for entry in reversed(prev_comments):
                    user_info = f" by {entry['user']}" if 'user' in entry else ""
                    st.markdown(
                        f"<div class='comment-box'><span class='timestamp'>{entry['timestamp']}{user_info}</span><br>{entry['comment']}</div>",
                        unsafe_allow_html=True
                    )
        else:
            st.info("No commentary yet for this fund.")

        new_comment = st.text_area("Add commentary (this will be appended):", key="new_comment")
        if st.button("💾 Append Commentary"):
            if not username:
                st.warning("Please enter your name in the sidebar before adding commentary.")
            elif not new_comment.strip():
                st.warning("Write something before saving.")
            else:
                add_comment(selected_fund, new_comment.strip(), username)
                commentary_data = load_json_file(COMMENTARY_FILE)  # reload
                st.success("Comment added.")
                # clear text area (use session_state)
                st.session_state["new_comment"] = ""

# ---------------- TAB: Compare Funds ----------------
with tab_compare:
    selected_funds = st.multiselect("Select funds to compare", funds)
    if selected_funds:
        if username:
            log_action(username, "Compared funds", ", ".join(selected_funds))

        st.markdown(f"<h3>📊 Comparing {len(selected_funds)} funds</h3>", unsafe_allow_html=True)
        selected_data = combined_df[combined_df["Fund Name"].isin(selected_funds)]
        # Show a compact table for comparison
        st.dataframe(selected_data, use_container_width=True)

        st.markdown("### 📝 Commentary for selected funds")
        for fund in selected_funds:
            st.markdown(f"<div class='fund-card'><strong>{fund}</strong></div>", unsafe_allow_html=True)
            comments = commentary_data.get(fund, [])
            if comments:
                for entry in reversed(comments):
                    st.markdown(
                        f"<div class='comment-box'><span class='timestamp'>{entry['timestamp']} by {entry.get('user','')}</span><br>{entry['comment']}</div>",
                        unsafe_allow_html=True
                    )
            else:
                st.markdown("_No commentary yet._")

# ---------------- TAB: My History ----------------
with tab_history:
    st.markdown("<h3>📁 My Activity History</h3>", unsafe_allow_html=True)
    if not username:
        st.info("Enter your name in the sidebar to view your activity history.")
    else:
        logs = get_user_logs(username)
        if not logs:
            st.info("No activity found for your user.")
        else:
            # show full history (most recent first)
            for entry in reversed(logs):
                st.markdown(
                    f"<div class='activity-log'><span class='timestamp'>{entry['timestamp']}</span><br>"
                    f"**{entry['action']}** — {entry['details']}</div>",
                    unsafe_allow_html=True
                )
            # allow download of user's activity
            st.download_button(
                label="Download my activity (JSON)",
                data=json.dumps(logs, indent=2),
                file_name=f"{username.replace(' ','_')}_activity.json",
                mime="application/json"
            )

# ---------------- FOOTER / NOTES ----------------
st.markdown("---")
st.caption("Hints: Edit SHEET_MAPPING near the top of app.py to match each file → sheet. "
           "If fund detection fails for a file, add an entry to FILE_FUND_COL_MAPPING with that file's fund column name.")

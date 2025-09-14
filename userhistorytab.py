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
SHEET_MAPPING = {
    "filea.xlsx": "Sheet1",
    "fileb.xlsx": ["Sheet1", "Sheet2"],
    "filec.xlsx": "Sheet1"
}

# ---------------- STYLES ----------------
st.markdown("""
<style>
.main { background-color: #f7f8fa; padding: 1.2rem; }
.fund-card { background: white; padding: 1rem; margin-bottom: 1rem;
             border-radius: 12px; box-shadow: 0 6px 18px rgba(0,0,0,0.06); }
.comment-box { border: 1px solid #e6e6e6; border-radius: 8px; background: #fff; padding: 0.6rem; margin-bottom: 0.5rem; }
.timestamp { color: #6c757d; font-size: 0.85rem; }
.activity-log { font-size: 0.9rem; margin-bottom: 0.3rem; }
.kpi { background: white; padding: 0.6rem; border-radius: 8px; box-shadow: 0 3px 8px rgba(0,0,0,0.04); }
</style>
""", unsafe_allow_html=True)

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

def load_excel_files_from_folder(folder, sheet_mapping):
    """Load Excel sheets, assign fund name from filename (filea.xlsx -> A)"""
    files = glob(os.path.join(folder, "*.xls*"))
    dataframes = {}
    if not files:
        st.error(f"No excel files found in {folder}")
        return dataframes

    for file in files:
        fname = os.path.basename(file)
        fund_name = os.path.splitext(fname)[0].replace("file", "").upper()  # filea.xlsx -> A
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
            df = df.copy()
            df["Fund Name"] = fund_name
            dataframes[f"{fund_name} ({sheet})"] = df
    return dataframes

# ---------------- LOAD DATA ----------------
if not os.path.exists(FUND_DATA_FOLDER):
    st.error(f"Fund data folder not found: {FUND_DATA_FOLDER} (create it and add Excel files)")
    st.stop()

dataframes = load_excel_files_from_folder(FUND_DATA_FOLDER, SHEET_MAPPING)
if not dataframes:
    st.error("No data loaded. Check SHEET_MAPPING and Excel files.")
    st.stop()

commentary_data = load_json_file(COMMENTARY_FILE)

# ---------------- SIDEBAR ----------------
st.sidebar.header("👤 User")
username = st.sidebar.text_input("Enter your name", placeholder="e.g. Alice").strip()

st.sidebar.header("📂 Data source & filters")
available_sources = list(dataframes.keys())
selected_sources = st.sidebar.multiselect("Choose source file(s)", options=available_sources, default=available_sources)

if not selected_sources:
    st.warning("Select at least one data source on the sidebar.")
    st.stop()

search_term = st.sidebar.text_input("🔎 Search fund name (type and press Enter)").strip().lower()

# Show recent activity (last 5)
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

# ---------------- COMBINE DATA ----------------
filtered_dfs = [df for k, df in dataframes.items() if k in selected_sources]
if not filtered_dfs:
    st.warning("No dataframes selected; choose at least one source.")
    st.stop()

combined_df = pd.concat(filtered_dfs, ignore_index=True, sort=False)

funds = sorted(combined_df["Fund Name"].unique())
if search_term:
    funds = [f for f in funds if search_term in f.lower()]

if not funds:
    st.warning("No funds match your search/filter. Adjust search or selected files.")
    st.stop()

# ---------------- MAIN UI ----------------
st.markdown("<h1>💹 Fund Explorer</h1>", unsafe_allow_html=True)
st.markdown("Modern dashboard for viewing, comparing, and commenting on funds. Persistent history included.")

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
                st.warning("Enter your name in the sidebar before adding commentary.")
            elif not new_comment.strip():
                st.warning("Write something before saving.")
            else:
                add_comment(selected_fund, new_comment.strip(), username)
                commentary_data = load_json_file(COMMENTARY_FILE)
                st.success("Comment added.")
                st.session_state["new_comment"] = ""

# ---------------- TAB: Compare Funds ----------------
with tab_compare:
    selected_funds = st.multiselect("Select funds to compare", funds)
    if selected_funds:
        if username:
            log_action(username, "Compared funds", ", ".join(selected_funds))

        st.markdown(f"<h3>📊 Comparing {len(selected_funds)} funds</h3>", unsafe_allow_html=True)
        selected_data = combined_df[combined_df["Fund Name"].isin(selected_funds)]
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
        st.info("Enter your name in the sidebar to view activity history.")
    else:
        logs = get_user_logs(username)
        if not logs:
            st.info("No activity found for your user.")
        else:
            for entry in reversed(logs):
                st.markdown(
                    f"<div class='activity-log'><span class='timestamp'>{entry['timestamp']}</span><br>"
                    f"**{entry['action']}** — {entry['details']}</div>",
                    unsafe_allow_html=True
                )
            st.download_button(
                label="Download my activity (JSON)",
                data=json.dumps(logs, indent=2),
                file_name=f"{username.replace(' ','_')}_activity.json",
                mime="application/json"
            )

st.markdown("---")
st.caption("Edit SHEET_MAPPING at the top to match each file → sheet. Fund name comes from file name (filea.xlsx → A).")


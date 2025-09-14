import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from glob import glob

# ---------------- CONFIGURATION ----------------
st.set_page_config(page_title="Fund Explorer", page_icon="💹", layout="wide")

FUND_DATA_FOLDER = "./fund_data"
COMMENTARY_FILE = "fund_commentary.json"
LOG_FILE = "user_activity.json"

# 🔧 SHEET MAPPING: map file name → sheet name (or list of sheets)
SHEET_MAPPING = {
    "funds_uk.xlsx": "UK_Funds",
    "funds_us.xlsx": "US_Funds",
    "funds_global.xlsx": "Global_Funds"
}

# --------------- STYLING ---------------
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; padding: 1.5rem; }
    .fund-card { background: white; padding: 1rem; margin-bottom: 1rem;
                 border-radius: 1rem; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }
    .comment-box { border: 1px solid #ddd; border-radius: 8px; background: #fff; padding: 0.5rem; }
    .timestamp { color: #6c757d; font-size: 0.85rem; }
    .activity-log { font-size: 0.9rem; margin-bottom: 0.3rem; }
    </style>
""", unsafe_allow_html=True)

# --------------- HELPER FUNCTIONS ---------------
def load_excel_files_from_folder(folder, sheet_mapping):
    """Load only specified sheets from Excel files based on mapping."""
    files = glob(os.path.join(folder, "*.xls*"))
    dataframes = {}
    for file in files:
        fname = os.path.basename(file)
        if fname not in sheet_mapping:
            st.warning(f"⚠️ Skipping {fname} (no sheet specified in SHEET_MAPPING)")
            continue
        sheets = sheet_mapping[fname]
        if isinstance(sheets, str):  # single sheet
            sheets = [sheets]
        for sheet in sheets:
            try:
                df = pd.read_excel(file, sheet_name=sheet)
                dataframes[f"{fname} ({sheet})"] = df
            except Exception as e:
                st.error(f"❌ Could not read {fname} - {sheet}: {e}")
    return dataframes

def load_json_file(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def save_json_file(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def add_comment(fund_name, comment, user):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if fund_name not in commentary_data:
        commentary_data[fund_name] = []
    commentary_data[fund_name].append({"timestamp": timestamp, "comment": comment, "user": user})
    save_json_file(COMMENTARY_FILE, commentary_data)
    log_action(user, "Added commentary", fund_name)

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

# --------------- LOAD DATA ---------------
if not os.path.exists(FUND_DATA_FOLDER):
    st.error(f"❌ Fund data folder not found: {FUND_DATA_FOLDER}")
    st.stop()

dataframes = load_excel_files_from_folder(FUND_DATA_FOLDER, SHEET_MAPPING)
if not dataframes:
    st.error("❌ No data loaded. Check your SHEET_MAPPING and Excel files.")
    st.stop()

commentary_data = load_json_file(COMMENTARY_FILE)

# Sidebar filters + user login
st.sidebar.header("👤 User")
username = st.sidebar.text_input("Enter your name", placeholder="e.g. John Doe").strip()

st.sidebar.header("📂 Data Filters")
selected_files = st.sidebar.multiselect(
    "Choose data source(s)",
    options=list(dataframes.keys()),
    default=list(dataframes.keys())
)

filtered_dfs = [df for fname, df in dataframes.items() if fname in selected_files]
if not filtered_dfs:
    st.warning("⚠️ No files selected. Please pick at least one.")
    st.stop()

combined_df = pd.concat(filtered_dfs, ignore_index=True)

if "Fund Name" not in combined_df.columns:
    st.error("❌ 'Fund Name' column not found in your Excel files.")
    st.stop()

funds = sorted(combined_df["Fund Name"].unique())
search_term = st.sidebar.text_input("🔎 Search fund name").strip().lower()
if search_term:
    funds = [f for f in funds if search_term in f.lower()]
if not funds:
    st.warning("⚠️ No funds match your search term.")
    st.stop()

# Show user history if logged in
if username:
    st.sidebar.subheader("📜 Your Recent Activity")
    logs = get_user_logs(username)
    if logs:
        for entry in reversed(logs[-5:]):  # Show last 5 actions
            st.sidebar.markdown(
                f"<div class='activity-log'>"
                f"<span class='timestamp'>{entry['timestamp']}</span><br>"
                f"**{entry['action']}** – {entry['details']}"
                f"</div>", unsafe_allow_html=True
            )
    else:
        st.sidebar.write("No activity yet.")

# --------------- MAIN UI ---------------
st.markdown("<h1>💹 Fund Explorer</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 Fund Details", "📊 Compare Funds"])

# ---------------- TAB 1: Fund Details ----------------
with tab1:
    selected_fund = st.selectbox("Select a fund", funds)
    if username:
        log_action(username, "Viewed fund", selected_fund)

    fund_data = combined_df[combined_df["Fund Name"] == selected_fund]
    st.markdown(f"<div class='fund-card'><h3>📄 {selected_fund}</h3></div>", unsafe_allow_html=True)
    st.dataframe(fund_data, use_container_width=True)

    st.markdown("### 📝 Commentary")
    previous_comments = commentary_data.get(selected_fund, [])
    if previous_comments:
        with st.expander("View previous commentary", expanded=True):
            for entry in reversed(previous_comments):
                user_info = f" by {entry['user']}" if 'user' in entry else ""
                st.markdown(
                    f"<div class='comment-box'><span class='timestamp'>{entry['timestamp']}{user_info}</span><br>{entry['comment']}</div>",
                    unsafe_allow_html=True
                )
    else:
        st.info("No commentary yet for this fund.")

    new_comment = st.text_area("Add new commentary:", placeholder="Write your note here...")
    if st.button("💾 Append Commentary"):
        if not username:
            st.warning("Please enter your name in the sidebar before adding commentary.")
        elif new_comment.strip():
            add_comment(selected_fund, new_comment.strip(), username)
            st.success("✅ Commentary appended successfully! Refresh to see updates.")
        else:
            st.warning("Please write something before saving.")

# ---------------- TAB 2: Compare Funds ----------------
with tab2:
    selected_funds = st.multiselect("Select funds to compare", funds)
    if selected_funds:
        if username:
            log_action(username, "Compared funds", ", ".join(selected_funds))

        st.markdown(f"<h3>📊 Comparing {len(selected_funds)} Fund(s)</h3>", unsafe_allow_html=True)
        selected_data = combined_df[combined_df["Fund Name"].isin(selected_funds)]
        st.dataframe(selected_data, use_container_width=True)

        st.markdown("### 📝 Commentary for Selected Funds")
        for fund in selected_funds:
            st.markdown(f"<div class='fund-card'><strong>{fund}</strong></div>", unsafe_allow_html=True)
            comments = commentary_data.get(fund, [])
            if comments:
                for entry in reversed(comments):
                    st.markdown(
                        f"<div class='comment-box'><span class='timestamp'>{entry['timestamp']}</span><br>{entry['comment']}</div>",
                        unsafe_allow_html=True
                    )
            else:
                st.markdown("_No commentary yet._")

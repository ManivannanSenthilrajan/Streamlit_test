import streamlit as st
import pandas as pd
import json
import os
from glob import glob
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Fund Explorer", page_icon="💹", layout="wide")

FUND_DATA_FOLDER = "./fund_data"
COMMENTARY_FILE = "fund_commentary.json"
LOG_FILE = "user_activity.json"

SHEET_MAPPING = {
    "filea.xlsx": "Sheet1",
    "fileb.xlsx": ["Sheet1", "Sheet2"],
    "filec.xlsx": "Sheet1"
}

# ---------------- CSS & THEME ----------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Frutiger', 'Verdana', 'Arial', sans-serif;
    background-color: #F8F9FA;
    color: #333;
}

/* Header */
.app-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 0;
    margin-bottom: 16px;
}
.app-title {
    font-size: 1.6rem;
    font-weight: 600;
    margin: 0;
    color: #1F2937;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    display: flex;
    gap: 6px;
    margin-bottom: 14px;
    border-bottom: 1px solid #ddd;
}
.stTabs [data-baseweb="tab"] {
    background-color: #E5E5E5 !important;
    color: #333 !important;
    font-weight: 600;
    border-radius: 4px 4px 0 0;
    padding: 10px 16px !important;
}
.stTabs button[aria-selected="true"] {
    background-color: #A44B3F !important;
    color: white !important;
}

/* Table styling */
table.dataframe {
    border-collapse: collapse;
}
table.dataframe th {
    position: sticky;
    top: 0;
    background: #f2f2f2;
    font-weight: 600;
    border-bottom: 2px solid #ccc;
}
table.dataframe td, table.dataframe th {
    border: none;
    padding: 6px 8px;
}
table.dataframe tbody tr:nth-child(even) td {
    background-color: #FAFAFA;
}

/* Comment cards */
.comment-card {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 8px;
    white-space: pre-line;
    max-height: 500px;
    overflow-y: auto;
}

/* Softer multi-select and selectbox */
div.stMultiSelect [role="listbox"], div.stMultiSelect [role="combobox"],
div.stSelectbox [role="combobox"] {
    border: 1px solid #ccc !important;
    box-shadow: none !important;
}
div.stSelectbox:focus-within, div.stMultiSelect:focus-within {
    outline: 2px solid #A44B3F;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------
def load_json_file(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(default, list) and not isinstance(data, list):
                    return []
                if isinstance(default, dict) and not isinstance(data, dict):
                    return {}
                return data
        except Exception:
            return default
    return default

def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def log_action(user, action, details=""):
    logs = load_json_file(LOG_FILE, [])
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "action": action,
        "details": details
    }
    logs.append(entry)
    save_json_file(LOG_FILE, logs)

def add_comment(fund, text, user):
    comments = load_json_file(COMMENTARY_FILE, {})
    if fund not in comments:
        comments[fund] = []
    comments[fund].append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "comment": text
    })
    save_json_file(COMMENTARY_FILE, comments)
    log_action(user, "Added commentary", f"{fund}: {text}")

def load_excel_files(folder, mapping):
    result = {}
    for file in glob(os.path.join(folder, "*.xls*")):
        fname = os.path.basename(file)
        if fname not in mapping:
            continue
        sheets = mapping[fname]
        if isinstance(sheets, str):
            sheets = [sheets]
        fund_name = os.path.splitext(fname)[0].replace("file", "").upper()
        for sheet in sheets:
            try:
                df = pd.read_excel(file, sheet_name=sheet)
                if df.empty:
                    continue
                df["Fund Name"] = fund_name
                result[f"{fund_name} ({sheet})"] = df
            except Exception:
                continue
    return result

def format_comments_grouped(comments):
    if not comments:
        return "<i>No commentary yet.</i>"
    grouped = {}
    for c in comments:
        user = c['user']
        if user not in grouped:
            grouped[user] = []
        grouped[user].append(c)
    lines = []
    for user, user_comments in grouped.items():
        lines.append(f"<b>{user}</b>")
        for c in user_comments:
            lines.append(f"<i>{c['timestamp']}: {c['comment']}</i>")
        lines.append("<br>")
    return "\n".join(lines)

# ---------------- LOAD DATA ----------------
dataframes = load_excel_files(FUND_DATA_FOLDER, SHEET_MAPPING)
commentary_data = load_json_file(COMMENTARY_FILE, {})

# Sidebar
with st.sidebar:
    st.header("User")
    username = st.text_input("Enter your name", value="")

combined_df = pd.concat(dataframes.values(), ignore_index=True) if dataframes else pd.DataFrame()
funds = sorted(combined_df["Fund Name"].unique()) if not combined_df.empty else []

# Header
st.markdown("""
<div class="app-header">
    <h1 class="app-title">Fund Explorer Dashboard</h1>
</div>
""", unsafe_allow_html=True)

tab_fund, tab_compare, tab_history = st.tabs(["Fund Details", "Compare Funds", "History"])

# ---------------- FUND DETAILS ----------------
with tab_fund:
    if funds:
        selected_fund = st.selectbox("Select Fund", funds, key="fund_select")
        if selected_fund:
            if "last_fund" not in st.session_state or st.session_state.last_fund != selected_fund:
                log_action(username, "Viewed fund details", selected_fund)
                st.session_state.last_fund = selected_fund

            df = combined_df[combined_df["Fund Name"] == selected_fund]
            comments = commentary_data.get(selected_fund, [])

            col1, col2 = st.columns([3, 1])
            with col1:
                st.dataframe(df, use_container_width=True, height=500)
            with col2:
                st.markdown("### Commentary")
                formatted_comments = format_comments_grouped(comments)
                st.markdown(f"<div class='comment-card'>{formatted_comments}</div>", unsafe_allow_html=True)

            with st.form(f"comment_form_{selected_fund}", clear_on_submit=True):
                new_comment = st.text_area("Add Commentary")
                submit = st.form_submit_button("Submit")
                if submit and new_comment.strip():
                    add_comment(selected_fund, new_comment.strip(), username)
                    st.success("Comment added!")
                    st.experimental_rerun()
    else:
        st.info("No funds loaded.")

# ---------------- COMPARE FUNDS ----------------
with tab_compare:
    selected_funds = st.multiselect("Select funds to compare", funds, key="compare_funds")
    if selected_funds:
        if "last_compare_funds" not in st.session_state or st.session_state.last_compare_funds != selected_funds:
            log_action(username, "Selected funds to compare", f"{selected_funds}")
            st.session_state.last_compare_funds = selected_funds

        df_selected = combined_df[combined_df["Fund Name"].isin(selected_funds)]
        all_attributes = list(df_selected.columns)
        all_attributes.remove("Fund Name")

        attributes_to_compare = st.multiselect(
            "Select attributes to compare",
            options=all_attributes,
            default=all_attributes[:5],
            key="compare_attributes"
        )
        if attributes_to_compare:
            if "last_compare_attrs" not in st.session_state or st.session_state.last_compare_attrs != attributes_to_compare:
                log_action(username, "Selected attributes for comparison", f"{attributes_to_compare}")
                st.session_state.last_compare_attrs = attributes_to_compare

            comparison_df = df_selected[["Fund Name"] + attributes_to_compare].set_index("Fund Name")
            st.dataframe(comparison_df, use_container_width=True)
            log_action(username, "Compare funds", f"Funds: {selected_funds}, Attributes: {attributes_to_compare}")

            if st.download_button("Download Comparison CSV", comparison_df.to_csv(index=True).encode(), "comparison.csv"):
                log_action(username, "Downloaded comparison CSV", f"{selected_funds} | {attributes_to_compare}")

            # Show commentary side by side
            n = len(selected_funds)
            cols = st.columns(n)
            for i, f in enumerate(selected_funds):
                comments = commentary_data.get(f, [])
                formatted_comments = format_comments_grouped(comments)
                with cols[i]:
                    st.markdown(f"<b>{f}</b><div class='comment-card'>{formatted_comments}</div>", unsafe_allow_html=True)
        else:
            st.warning("Please select at least one attribute to compare.")
    else:
        st.info("Select at least one fund.")

# ---------------- HISTORY ----------------
with tab_history:
    logs = load_json_file(LOG_FILE, [])
    if logs:
        df_logs = pd.DataFrame(logs)
        st.dataframe(df_logs, use_container_width=True)

        if st.download_button("Download CSV", df_logs.to_csv(index=False).encode(), "history.csv"):
            log_action(username, "Downloaded history CSV", f"{len(df_logs)} records")

        if st.download_button("Download JSON", json.dumps(logs, indent=2).encode(), "history.json"):
            log_action(username, "Downloaded history JSON", f"{len(df_logs)} records")
    else:
        st.info("No activity recorded yet.")

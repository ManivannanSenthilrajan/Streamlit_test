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
st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-family: 'Frutiger', 'Verdana', 'Arial', sans-serif;
        background-color: #F8F9FA;
        color: #333;
    }
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
    .comment-card {
        background: #fff;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 8px 10px;
        margin-bottom: 8px;
    }
    .comment-meta {
        font-size: 0.8rem;
        color: #666;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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

# ---------------- LOAD DATA ----------------
dataframes = load_excel_files(FUND_DATA_FOLDER, SHEET_MAPPING)
commentary_data = load_json_file(COMMENTARY_FILE, {})
logs_data = load_json_file(LOG_FILE, [])

# Sidebar
with st.sidebar:
    st.header("User")
    username = st.text_input("Enter your name", value="")

combined_df = pd.concat(dataframes.values(), ignore_index=True) if dataframes else pd.DataFrame()

funds = sorted(combined_df["Fund Name"].unique()) if not combined_df.empty else []

# Header
st.markdown(
    """
    <div class="app-header">
        <h1 class="app-title">Fund Explorer Dashboard</h1>
    </div>
    """, unsafe_allow_html=True
)

tab_fund, tab_compare, tab_history = st.tabs(["Fund Details", "Compare Funds", "History"])

# --- FUND TAB ---
with tab_fund:
    if funds:
        selected_fund = st.selectbox("Select Fund", funds)
        if selected_fund:
            log_action(username, "Viewed fund", selected_fund)
            comments = commentary_data.get(selected_fund, [])
            st.markdown("### Commentary")
            for c in reversed(comments):
                st.markdown(
                    f"<div class='comment-card'><div class='comment-meta'>{c['timestamp']} | {c['user']}</div><div>{c['comment']}</div></div>",
                    unsafe_allow_html=True
                )
            df = combined_df[combined_df["Fund Name"] == selected_fund]
            st.dataframe(df, use_container_width=True)
            with st.form(f"comment_form_{selected_fund}", clear_on_submit=True):
                new_comment = st.text_area("Add Commentary")
                submit = st.form_submit_button("Submit")
                if submit and new_comment.strip():
                    add_comment(selected_fund, new_comment.strip(), username)
                    st.success("Comment added!")
                    st.rerun()
    else:
        st.info("No funds loaded.")

# --- COMPARE TAB ---
with tab_compare:
    selected_funds = st.multiselect("Select funds to compare", funds)
    
    if selected_funds:
        # Filter combined_df for selected funds
        df_selected = combined_df[combined_df["Fund Name"].isin(selected_funds)]
        
        # Attributes selection
        all_attributes = list(df_selected.columns)
        all_attributes.remove("Fund Name")  # Exclude Fund Name
        attributes_to_compare = st.multiselect(
            "Select attributes to compare",
            options=all_attributes,
            default=all_attributes[:5]
        )
        
        if attributes_to_compare:
            # Create a pivoted table for side-by-side comparison
            comparison_df = df_selected[["Fund Name"] + attributes_to_compare]
            
            # Optional: set Fund Name as index for cleaner look
            comparison_df = comparison_df.set_index("Fund Name")
            st.dataframe(comparison_df, use_container_width=True)
        else:
            st.warning("Please select at least one attribute to compare.")
    else:
        st.info("Select at least one fund.")

# --- HISTORY TAB ---
with tab_history:
    logs = load_json_file(LOG_FILE, [])
    if logs:
        df_logs = pd.DataFrame(logs)
        st.dataframe(df_logs, use_container_width=True)
        st.download_button("Download CSV", df_logs.to_csv(index=False).encode(), "history.csv")
        st.download_button("Download JSON", json.dumps(logs, indent=2).encode(), "history.json")
    else:
        st.info("No activity recorded yet.")

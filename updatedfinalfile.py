import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Fund Explorer Dashboard", layout="wide")

# Paths for data
FUND_DATA_FOLDER = "fund_data"
COMMENTARY_FILE = "fund_commentary.json"
ACTIVITY_LOG_FILE = "user_activity.json"

# Sheet mapping (update according to your real files)
sheet_mapping = {
    "filea.xlsx": "Sheet1",
    "fileb.xlsx": "Holdings",
    "filec.xlsx": "FundData"
}

# ---------------- UTILITIES ----------------
def load_fund_data():
    fund_data = {}
    for file, sheet in sheet_mapping.items():
        file_path = os.path.join(FUND_DATA_FOLDER, file)
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path, sheet_name=sheet)
                fund_name = os.path.splitext(file)[0].capitalize()
                fund_data[fund_name] = df
            except Exception as e:
                st.error(f"Error reading {file}: {e}")
    return fund_data

def load_json(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def log_activity(username, action, details):
    log = load_json(ACTIVITY_LOG_FILE)
    log.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "username": username,
        "action": action,
        "details": details
    })
    save_json(ACTIVITY_LOG_FILE, log)

# ---------------- LOAD DATA ----------------
fund_data = load_fund_data()
commentary = load_json(COMMENTARY_FILE)

# ---------------- CUSTOM CSS ----------------
st.markdown("""
    <style>
    /* Global Font */
    html, body, [class*="css"] {
        font-family: 'Frutiger', Verdana, 'Courier New', sans-serif;
        font-weight: 300;
    }

    /* Header */
    .main-title {
        text-align: left;
        font-size: 2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #333;
    }

    /* Tabs */
    div[data-baseweb="tab-list"] {
        display: flex;
        justify-content: flex-start;
        border-bottom: 2px solid #ccc;
        background-color: #f5f5f5;
    }
    div[data-baseweb="tab"] {
        background-color: #d9d9d9;
        color: #333;
        padding: 0.5rem 1.5rem;
        border-radius: 0px;
        font-weight: 500;
    }
    div[data-baseweb="tab"][aria-selected="true"] {
        background-color: #8B0000; /* reddish-brown */
        color: white;
        font-weight: 600;
    }

    /* Table styling */
    table {
        border-collapse: collapse;
        width: 100%;
    }
    th, td {
        text-align: left;
        padding: 8px;
    }
    th {
        background-color: #f2f2f2;
    }
    .scroll-container {
        overflow-x: auto;
        white-space: nowrap;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- APP LAYOUT ----------------
st.markdown("<div class='main-title'>Fund Explorer Dashboard</div>", unsafe_allow_html=True)

tabs = st.tabs(["Fund Details", "Compare Funds", "Activity History"])

# ---------------- FUND DETAILS TAB ----------------
with tabs[0]:
    st.subheader("Fund Details")
    selected_fund = st.selectbox("Select a Fund", list(fund_data.keys()))
    if selected_fund:
        # Show existing commentary
        st.markdown("### Commentary")
        fund_comments = [c for c in commentary if c["fund"] == selected_fund]
        if fund_comments:
            for c in fund_comments:
                st.markdown(f"- **{c['username']}** ({c['timestamp']}): {c['comment']}")
        else:
            st.markdown("*No commentary yet.*")

        # Show data
        st.dataframe(fund_data[selected_fund], use_container_width=True)

        # Add new commentary below table
        st.markdown("### Add New Commentary")
        new_comment = st.text_area("Write your comment", key=f"comment_input_{selected_fund}")
        if st.button("Submit Comment"):
            if new_comment.strip():
                username = "User"  # Replace with real user if you add authentication
                commentary.append({
                    "fund": selected_fund,
                    "username": username,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "comment": new_comment.strip()
                })
                save_json(COMMENTARY_FILE, commentary)
                log_activity(username, "Added commentary", {"fund": selected_fund, "comment": new_comment.strip()})
                st.success("Comment added!")
                st.rerun()
            else:
                st.warning("Comment cannot be empty.")

# ---------------- COMPARE FUNDS TAB ----------------
with tabs[1]:
    st.subheader("Compare Funds")
    selected_funds = st.multiselect("Select funds to compare", list(fund_data.keys()))
    if selected_funds:
        combined = pd.concat([fund_data[f].assign(Fund=f) for f in selected_funds], axis=0, ignore_index=True)
        st.markdown("### Comparison Table")
        st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
        st.dataframe(combined, use_container_width=True, height=500)
        st.markdown('</div>', unsafe_allow_html=True)
        log_activity("User", "Compared funds", {"funds": selected_funds})

# ---------------- ACTIVITY HISTORY TAB ----------------
with tabs[2]:
    st.subheader("Activity History")
    history = load_json(ACTIVITY_LOG_FILE)
    if history:
        df = pd.DataFrame(history)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download JSON", data=json.dumps(history, indent=4), file_name="activity_log.json")
        st.download_button("Download CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="activity_log.csv")
    else:
        st.info("No activity recorded yet.")

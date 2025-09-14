# streamlit_app.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from glob import glob

# --------------- CONFIGURATION ---------------
st.set_page_config(page_title="Fund Explorer", page_icon="💹", layout="wide")

FUND_DATA_FOLDER = "./fund_data"  # Folder where Excel files live
COMMENTARY_FILE = "fund_commentary.json"

# ---------- CUSTOM STYLES ----------
st.markdown("""
    <style>
    /* General page styling */
    .main {
        background-color: #f8f9fa;
        padding: 1.5rem;
    }
    h1, h2, h3 {
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
    }
    /* Card styling */
    .fund-card {
        background: white;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    .comment-box {
        border: 1px solid #ddd;
        border-radius: 8px;
        background: #fff;
        padding: 0.5rem;
    }
    .timestamp {
        color: #6c757d;
        font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

# --------------- HELPER FUNCTIONS ---------------
def load_excel_files_from_folder(folder):
    files = glob(os.path.join(folder, "*.xls*"))
    dataframes = {}
    for file in files:
        df = pd.read_excel(file)
        dataframes[os.path.basename(file)] = df
    return dataframes

def load_commentary():
    if os.path.exists(COMMENTARY_FILE):
        with open(COMMENTARY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_commentary(commentary):
    with open(COMMENTARY_FILE, "w") as f:
        json.dump(commentary, f, indent=2)

def add_comment(fund_name, comment):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if fund_name not in commentary_data:
        commentary_data[fund_name] = []
    commentary_data[fund_name].append({"timestamp": timestamp, "comment": comment})
    save_commentary(commentary_data)

# --------------- LOAD DATA ---------------
if not os.path.exists(FUND_DATA_FOLDER):
    st.error(f"❌ Fund data folder not found: {FUND_DATA_FOLDER}")
    st.stop()

dataframes = load_excel_files_from_folder(FUND_DATA_FOLDER)
if not dataframes:
    st.error(f"❌ No Excel files found in {FUND_DATA_FOLDER}")
    st.stop()

commentary_data = load_commentary()

# Sidebar filters
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

# --------------- MAIN UI ---------------
st.markdown("<h1>💹 Fund Explorer</h1>", unsafe_allow_html=True)
st.markdown("Explore, compare, and comment on funds with a clean dashboard experience.")

tab1, tab2 = st.tabs(["🔍 Fund Details", "📊 Compare Funds"])

# ---------------- TAB 1: Fund Details ----------------
with tab1:
    selected_fund = st.selectbox("Select a fund", funds)
    fund_data = combined_df[combined_df["Fund Name"] == selected_fund]

    st.markdown(f"<div class='fund-card'><h3>📄 {selected_fund}</h3></div>", unsafe_allow_html=True)
    st.dataframe(fund_data, use_container_width=True)

    # Commentary Section
    st.markdown("### 📝 Commentary")
    previous_comments = commentary_data.get(selected_fund, [])
    if previous_comments:
        with st.expander("View previous commentary", expanded=True):
            for entry in reversed(previous_comments):
                st.markdown(
                    f"<div class='comment-box'><span class='timestamp'>{entry['timestamp']}</span><br>{entry['comment']}</div>",
                    unsafe_allow_html=True
                )
    else:
        st.info("No commentary yet for this fund.")

    new_comment = st.text_area("Add new commentary:", placeholder="Write your note here...")
    if st.button("💾 Append Commentary"):
        if new_comment.strip():
            add_comment(selected_fund, new_comment.strip())
            st.success("✅ Commentary appended successfully! Refresh to see updates.")
        else:
            st.warning("Please write something before saving.")

# ---------------- TAB 2: Compare Funds ----------------
with tab2:
    selected_funds = st.multiselect("Select funds to compare", funds)
    if selected_funds:
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

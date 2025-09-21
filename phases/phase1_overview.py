import streamlit as st
from utils.gitlab_api import get_issues, safe_join
from utils.ui_components import render_dynamic_summary_cards
import pandas as pd
import io

def render():
    st.header("📊 Overview")

    token = st.text_input("GitLab Personal Access Token", type="password", key="overview_token")
    project_ids = st.text_input("Project IDs (comma-separated)", "", key="overview_projects")
    refresh = st.button("Fetch Issues", key="overview_fetch")

    if "issues_df" not in st.session_state:
        st.session_state["issues_df"] = pd.DataFrame()

    if refresh:
        projects = [p.strip() for p in project_ids.split(",") if p.strip()]
        with st.spinner("Fetching issues..."):
            st.session_state["issues_df"] = get_issues(projects, token, ssl_verify=False)

    df = st.session_state["issues_df"]

    if df.empty:
        st.info("Enter token + project IDs and click Fetch Issues.")
        return

    # Ensure all label columns exist
    for col in ["team", "status", "milestone", "sprint", "project", "workstream"]:
        if col not in df.columns:
            df[col] = ""

    # Flatten complex objects
    for col in df.columns:
        df[col] = df[col].apply(safe_join)

    # Quick summary cards with counts
    st.subheader("Quick Summary")
    render_dynamic_summary_cards(df)

    # Show filtered dataframe
    st.subheader("All Issues")
    filtered_df = df.copy()
    for label in ["team", "status", "milestone", "sprint", "project", "workstream"]:
        filter_val = st.session_state.get(f"filter_{label}")
        if filter_val:
            filtered_df = filtered_df[filtered_df[label] == filter_val]
    st.dataframe(filtered_df)

    # Excel download
    excel_buffer = io.BytesIO()
    filtered_df.to_excel(excel_buffer, index=False, engine="openpyxl")
    excel_buffer.seek(0)
    st.download_button(
        "Download Issues as Excel",
        data=excel_buffer,
        file_name="issues.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

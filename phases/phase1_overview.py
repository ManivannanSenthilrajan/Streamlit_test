import streamlit as st
import pandas as pd
from utils.gitlab_api import fetch_issues
from utils.ui_components import render_dynamic_summary_cards

def render():
    st.title("📊 Overview")

    token = st.text_input("GitLab Personal Access Token", type="password")
    project_ids = st.text_input("Project IDs (comma-separated)", "")
    refresh = st.button("Fetch Issues")

    if not refresh or not token or not project_ids:
        st.info("Enter token + project IDs and click Fetch Issues.")
        return

    with st.spinner("Fetching issues from GitLab..."):
        projects = [p.strip() for p in project_ids.split(",") if p.strip()]
        df = fetch_issues(projects, token)

    if df.empty:
        st.warning("No issues found.")
        return

    st.subheader("Summary")
    render_dynamic_summary_cards(df)

    st.subheader("All Issues")
    st.dataframe(df, use_container_width=True)

    st.download_button(
        "Download Filtered Issues as Excel",
        data=df.to_excel(index=False),
        file_name="gitlab_issues.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

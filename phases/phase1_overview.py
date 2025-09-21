import streamlit as st
from utils.gitlab_api import get_issues, safe_join
from utils.ui_components import render_dynamic_summary_cards
import pandas as pd
import io

def render():
    st.title("📊 Overview")

    token = st.text_input("GitLab Personal Access Token", type="password")
    project_ids = st.text_input("Project IDs (comma-separated)", "")
    refresh = st.button("Fetch Issues")

    if not refresh or not token or not project_ids:
        st.info("Enter token + project IDs and click Fetch Issues.")
        return

    with st.spinner("Fetching issues..."):
        projects = [p.strip() for p in project_ids.split(",") if p.strip()]
        df = get_issues(projects, token, ssl_verify=False)

    if not isinstance(df, pd.DataFrame) or df.empty:
        st.warning("No issues found.")
        return

    # Ensure all expected label columns exist
    for col in ["status", "team", "milestone", "sprint", "project", "workstream"]:
        if col not in df.columns:
            df[col] = ""

    # Flatten any complex objects into strings
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(safe_join)

    render_dynamic_summary_cards(df)

    st.subheader("All Issues")
    st.dataframe(df)

    # Excel download using BytesIO + openpyxl
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)

    st.download_button(
        "Download Issues as Excel",
        data=excel_buffer,
        file_name="issues.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

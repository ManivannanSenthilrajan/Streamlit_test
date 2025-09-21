import streamlit as st
from phases import phase1_overview, phase2_kanban, phase3_hygiene, phase4_commentary, phase5_edit
from utils import gitlab_api

st.set_page_config(page_title="GitLab Project Dashboard", layout="wide")

# Sidebar: Token + Projects
with st.sidebar:
    st.header("🔑 Authentication")
    token = st.text_input("GitLab Personal Access Token", type="password")
    project_input = st.text_input("Comma-separated Project IDs")
    refresh = st.button("🔄 Refresh Issues")

if token and project_input and refresh:
    st.session_state["token"] = token
    st.session_state["projects"] = [p.strip() for p in project_input.split(",") if p.strip()]
    with st.spinner("Fetching issues from GitLab..."):
        issues = gitlab_api.get_issues(st.session_state["projects"], token)
        df = gitlab_api.build_dataframe(issues)
        st.session_state["issues_df"] = df

# Navigation Tabs
tab = st.sidebar.radio("Navigation", ["Overview", "Kanban", "Hygiene", "Commentary", "Edit"])

if tab == "Overview":
    phase1_overview.render()
elif tab == "Kanban":
    phase2_kanban.render()
elif tab == "Hygiene":
    phase3_hygiene.render()
elif tab == "Commentary":
    phase4_commentary.render()
elif tab == "Edit":
    phase5_edit.render()

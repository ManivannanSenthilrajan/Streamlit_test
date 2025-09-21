import streamlit as st
from utils.gitlab_api import get_issues, safe_join
from utils.ui_components import STATUS_COLORS
import pandas as pd

def render():
    st.header("🗂 Kanban Board")

    token = st.text_input("GitLab Personal Access Token", type="password", key="kanban_token")
    project_ids = st.text_input("Project IDs (comma-separated)", "", key="kanban_projects")
    refresh = st.button("Fetch Issues", key="kanban_fetch")

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

    # Grouping option
    grouping_option = st.selectbox("Group swimlanes by:", ["status", "team"], key="kanban_group")
    df[grouping_option] = df[grouping_option].apply(safe_join)
    swimlanes = sorted(df[grouping_option].fillna("No Value").unique())

    selected_issue = st.session_state.get("selected_issue")
    board_col, detail_col = st.columns([4,1])

    # Kanban swimlanes
    with board_col:
        st.markdown('<div class="kanban-container">', unsafe_allow_html=True)
        for lane in swimlanes:
            st.markdown(f'<div class="kanban-column"><h4>{lane}</h4>', unsafe_allow_html=True)
            lane_df = df[df[grouping_option].fillna("No Value") == lane]

            for _, row in lane_df.iterrows():
                color = STATUS_COLORS.get(str(row.get("status", "")).lower(), "#ddd")
                issue_key = f"btn_{row['id']}_{grouping_option}_{lane}"
                if st.button(row["title"], key=issue_key):
                    st.session_state["selected_issue"] = row.to_dict()
                    selected_issue = row.to_dict()
                st.markdown(
                    f"""
                    <div class="issue-card">
                        <div class="stripe" style="background:{color};"></div>
                        <div class="issue-title">{row['title']}</div>
                        <div class="issue-meta">
                            Team: {row.get("team", "—")} | Status: {row.get("status", "—")}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Detail panel
    with detail_col:
        st.markdown('<div class="sticky-panel">', unsafe_allow_html=True)
        if selected_issue:
            st.subheader(f"#{selected_issue['id']} - {selected_issue['title']}")
            st.markdown(f"**Team:** {selected_issue.get('team', '—')}")
            st.markdown(f"**Status:** {selected_issue.get('status', '—')}")
            st.markdown(f"**Milestone:** {selected_issue.get('milestone', '—')}")
            st.markdown(f"**Description:**\n{selected_issue.get('description', 'No description')}")
        else:
            st.info("Select an issue to see details here.")
        st.markdown('</div>', unsafe_allow_html=True)

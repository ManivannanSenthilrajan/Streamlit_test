import streamlit as st
from utils.gitlab_api import update_issue

def render():
    if "issues_df" not in st.session_state:
        st.info("Load data first in Overview tab.")
        return

    df = st.session_state["issues_df"]
    st.subheader("✏️ Edit Issues")

    selected = st.selectbox("Select Issue", df["title"].tolist())
    if not selected:
        return

    issue = df.loc[df["title"] == selected].iloc[0]

    new_title = st.text_input("Title", issue["title"])
    new_description = st.text_area("Description", issue["description"])
    new_team = st.text_input("Team", issue["team"])
    new_status = st.text_input("Status", issue["status"])
    new_sprint = st.text_input("Sprint", issue["sprint"])

    if st.button("Update Issue"):
        payload = {
            "title": new_title,
            "description": new_description,
            "labels": [f"team::{new_team}", f"status::{new_status}", f"sprint::{new_sprint}"],
        }
        resp = update_issue(issue["project_id"], issue["id"], st.session_state["token"], payload)
        if resp.status_code == 200:
            st.success("Issue updated successfully!")
        else:
            st.error(f"Failed to update issue: {resp.text}")

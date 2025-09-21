import streamlit as st
from utils.gitlab_api import update_issue

def render():
    if "issues_df" not in st.session_state:
        st.info("Load data first in Overview tab.")
        return

    df = st.session_state["issues_df"]
    st.subheader("🧹 Hygiene Check")

    missing_teams = df[df["team"] == ""]
    missing_status = df[df["status"] == ""]
    missing_sprint = df[df["sprint"] == ""]

    st.write("Click a card to view issues:")

    col1, col2, col3 = st.columns(3)
    if col1.button(f"Missing Teams ({len(missing_teams)})"):
        st.session_state["hygiene_view"] = missing_teams
    if col2.button(f"Missing Status ({len(missing_status)})"):
        st.session_state["hygiene_view"] = missing_status
    if col3.button(f"Missing Sprint ({len(missing_sprint)})"):
        st.session_state["hygiene_view"] = missing_sprint

    if "hygiene_view" in st.session_state:
        st.dataframe(st.session_state["hygiene_view"])
        st.markdown("Select an issue to edit:")
        selected = st.selectbox("Issue", st.session_state["hygiene_view"]["title"].tolist())
        if selected:
            issue = st.session_state["hygiene_view"].loc[
                st.session_state["hygiene_view"]["title"] == selected
            ].iloc[0]
            new_team = st.text_input("Team", issue["team"])
            new_status = st.text_input("Status", issue["status"])
            new_sprint = st.text_input("Sprint", issue["sprint"])
            if st.button("Update Issue"):
                payload = {"labels": [f"team::{new_team}", f"status::{new_status}", f"sprint::{new_sprint}"]}
                resp = update_issue(issue["project_id"], issue["id"], st.session_state["token"], payload)
                if resp.status_code == 200:
                    st.success("Issue updated!")
                else:
                    st.error(f"Failed to update issue: {resp.text}")

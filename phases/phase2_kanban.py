import streamlit as st
import pandas as pd

def render():
    if "issues_df" not in st.session_state:
        st.info("Load data first in Overview tab.")
        return

    df = st.session_state["issues_df"]
    st.subheader("🗂️ Kanban Board")

    selected_sprint = st.selectbox("Filter by Sprint", ["All"] + sorted(df["sprint"].unique()))
    selected_status = st.multiselect("Filter by Status", sorted(df["status"].unique()))

    filtered = df.copy()
    if selected_sprint != "All":
        filtered = filtered[filtered["sprint"] == selected_sprint]
    if selected_status:
        filtered = filtered[filtered["status"].isin(selected_status)]

    statuses = sorted(filtered["status"].unique())
    cols = st.columns(len(statuses))

    for i, status in enumerate(statuses):
        with cols[i]:
            st.markdown(f"### {status}")
            for _, row in filtered[filtered["status"] == status].iterrows():
                st.markdown(
                    f"""
                    <div class="kanban-card" onclick="window.open('{row['web_url']}', '_blank')">
                        <strong>{row['title']}</strong><br>
                        <small>Team: {row['team'] or "—"} | Sprint: {row['sprint'] or "—"}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

import streamlit as st

def summary_cards(df):
    """Render summary cards for quick stats."""
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Teams", df["team"].nunique())
    col2.metric("Sprints", df["sprint"].nunique())
    col3.metric("Milestones", df["milestone"].nunique())
    col4.metric("Statuses", df["status"].nunique())

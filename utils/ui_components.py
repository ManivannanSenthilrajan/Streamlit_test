import streamlit as st

STATUS_COLORS = {
    "done": "#4caf50",
    "in progress": "#ff9800",
    "todo": "#2196f3",
    "blocked": "#f44336",
}

def render_dynamic_summary_cards(df):
    """
    Render clickable summary cards for all label columns dynamically.
    """
    labels_to_show = ["team", "status", "milestone", "sprint", "project", "workstream"]
    for label in labels_to_show:
        if label not in df.columns:
            continue
        values = df[label].fillna("No Value").unique()
        for val in values:
            val_str = ", ".join(val) if isinstance(val, list) else str(val)
            st.button(f"{label}: {val_str}", key=f"btn_{label}_{val_str}")

import streamlit as st

# Status colors for Kanban cards
STATUS_COLORS = {
    "done": "#28a745",
    "in progress": "#ffc107",
    "todo": "#17a2b8",
    "blocked": "#dc3545",
    "": "#ddd"
}

def load_css():
    """Load global CSS from styles folder."""
    with open("styles/global.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def safe_join(val):
    """Flatten list/dict values to string."""
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    elif isinstance(val, dict):
        return ", ".join(f"{k}:{v}" for k, v in val.items())
    elif val is None:
        return ""
    else:
        return str(val)

def render_dynamic_summary_cards(df):
    """
    Render clickable summary cards for all label columns dynamically with counts.
    """
    labels_to_show = ["team", "status", "milestone", "sprint", "project", "workstream"]
    for label in labels_to_show:
        if label not in df.columns:
            continue
        values = df[label].fillna("No Value").unique()
        cols = st.columns(len(values))
        for i, val in enumerate(values):
            val_str = safe_join(val)
            count = df[df[label].fillna("No Value") == val].shape[0]
            if cols[i].button(f"{val_str} ({count})", key=f"card_{label}_{val_str}"):
                st.session_state[f"filter_{label}"] = val_str

import streamlit as st

# Status colors for Kanban cards
STATUS_COLORS = {
    "done": "#4caf50",
    "in progress": "#ff9800",
    "todo": "#2196f3",
    "blocked": "#f44336",
}

def load_css(css_file="global.css"):
    """
    Load a local CSS file into the Streamlit app.
    """
    try:
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Could not load CSS file: {e}")


def render_dynamic_summary_cards(df):
    """
    Render clickable summary cards for all label columns dynamically.
    Ensures keys are unique and safe (strings only) to prevent unhashable errors.
    """
    # Dynamically pick label columns available in df
    labels_to_show = ["team", "status", "milestone", "sprint", "project", "workstream"]
    for label in labels_to_show:
        if label not in df.columns:
            continue

        # Flatten any list values into strings
        values = df[label].fillna("No Value").unique()
        for val in values:
            val_str = ", ".join(val) if isinstance(val, list) else str(val)
            st.button(f"{label}: {val_str}", key=f"btn_{label}_{val_str}")

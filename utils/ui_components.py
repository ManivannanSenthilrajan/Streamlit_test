import streamlit as st
import pandas as pd
from pathlib import Path

STATUS_COLORS = {
    "done": "#a7f3d0",
    "in progress": "#fde68a",
    "todo": "#fca5a5",
}

def load_css(path="styles/global.css"):
    css_path = Path(path)
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"CSS file not found at {path}")

def render_dynamic_summary_cards(df: pd.DataFrame):
    """Dynamically render cards for any columns with unique values."""
    label_cols = [c for c in df.columns if c not in ["id", "title", "description", "web_url"]]
    cols = st.columns(min(len(label_cols), 4))
    for i, col_name in enumerate(label_cols):
        with cols[i % 4]:
            count = df[col_name].nunique()
            st.markdown(f"<div class='summary-card'><h3>{col_name.title()}</h3><p>{count}</p></div>", unsafe_allow_html=True)

import streamlit as st
from phases import phase1_overview, phase2_kanban
from utils.ui_components import load_css

st.set_page_config(page_title="GitLab Issue Manager", layout="wide")

# Load CSS from styles folder
load_css()

# Tabbed UI
tabs = st.tabs(["Overview", "Kanban"])
with tabs[0]:
    phase1_overview.render()
with tabs[1]:
    phase2_kanban.render()

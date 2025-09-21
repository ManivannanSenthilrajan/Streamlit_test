import streamlit as st
from phases import phase1_overview, phase2_kanban
from utils.ui_components import load_css

# Page config
st.set_page_config(page_title="GitLab Issue Manager", layout="wide")

# Load CSS
load_css()

# Tabs
tabs = st.tabs(["Overview", "Kanban"])  # add more tabs as needed
with tabs[0]:
    phase1_overview.render()
with tabs[1]:
    phase2_kanban.render()

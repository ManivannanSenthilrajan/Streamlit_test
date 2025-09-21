import streamlit as st
from utils.ui_components import load_css
from phases import phase1_overview, phase2_kanban

st.set_page_config(page_title="GitLab Project Dashboard", layout="wide")

# Load global CSS once
load_css("styles/global.css")

st.sidebar.title("Navigation")
tabs = ["Overview", "Kanban Board"]
selected_tab = st.sidebar.radio("Select Tab", tabs)

if selected_tab == "Overview":
    phase1_overview.render()
elif selected_tab == "Kanban Board":
    phase2_kanban.render()

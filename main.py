import streamlit as st
from phases import phase1_overview, phase2_kanban, phase3_hygiene, phase4_commentary, phase5_edit
from utils import gitlab_api

st.set_page_config(page_title="GitLab Project Dashboard", layout="wide")

# Inject global CSS
st.markdown("""
<style>
/* Global Styling */
body { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4 { font-weight: 600; }
.sidebar .sidebar-content { background-color: #f8f9fa; }

/* Metric Cards */
.css-1xarl3l, .css-1d391kg { background: #ffffff; border-radius: 1rem; 
    box-shadow: 0 2px 8px rgba(0,0,0,0.08); padding: 1rem; }

/* DataFrame Table Styling */
[data-testid="stDataFrame"] table { border-radius: 0.75rem; overflow: hidden; }
[data-testid="stDataFrame"] thead tr th { background-color: #f1f3f5; font-weight: 600; }

/* Kanban Cards */
.kanban-card {
    background: #ffffff;
    border-radius: 0.75rem;
    padding: 0.8rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 1px 5px rgba(0,0,0,0.08);
    transition: all 0.2s ease-in-out;
    cursor: pointer;
}
.kanban-card:hover { transform: translateY(-2px); box-shadow: 0 3px 10px rgba(0,0,0,0.15); }

/* Download Button Styling */
.stDownloadButton button {
    background: linear-gradient(135deg, #0d6efd, #6c63ff);
    color: white;
    font-weight: 600;
    border-radius: 0.75rem;
    padding: 0.5rem 1.5rem;
}
.stDownloadButton button:hover { background: linear-gradient(135deg, #0b5ed7, #574bff); }

/* Section Headers */
.block-container h2, .block-container h3 {
    border-left: 4px solid #0d6efd;
    padding-left: 8px;
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# Sidebar: Token + Projects
with st.sidebar:
    st.header("🔑 Authentication")
    token = st.text_input("GitLab Personal Access Token", type="password")
    project_input = st.text_input("Comma-separated Project IDs")
    refresh = st.button("🔄 Refresh Issues")

if token and project_input and refresh:
    st.session_state["token"] = token
    st.session_state["projects"] = [p.strip() for p in project_input.split(",") if p.strip()]
    with st.spinner("Fetching issues from GitLab..."):
        issues = gitlab_api.get_issues(st.session_state["projects"], token)
        df = gitlab_api.build_dataframe(issues)
        st.session_state["issues_df"] = df

tab = st.sidebar.radio("Navigation", ["Overview", "Kanban", "Hygiene", "Commentary", "Edit"])

if tab == "Overview":
    phase1_overview.render()
elif tab == "Kanban":
    phase2_kanban.render()
elif tab == "Hygiene":
    phase3_hygiene.render()
elif tab == "Commentary":
    phase4_commentary.render()
elif tab == "Edit":
    phase5_edit.render()

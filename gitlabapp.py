import os
import requests
import pandas as pd
import streamlit as st
from io import BytesIO
from docx import Document

# ----------------------------
# CONFIG
# ----------------------------
GITLAB_URL = "https://gitlab.com/api/v4"
PROJECT_ID = os.getenv("GITLAB_PROJECT_ID", "123456")  # replace with your project ID
PRIVATE_TOKEN = os.getenv("GITLAB_TOKEN", "your-token")

HEADERS = {"PRIVATE-TOKEN": PRIVATE_TOKEN}

# ----------------------------
# HELPERS
# ----------------------------
def fetch_issues():
    """Fetch all issues from GitLab project"""
    url = f"{GITLAB_URL}/projects/{PROJECT_ID}/issues"
    params = {"per_page": 100, "state": "all"}
    r = requests.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()

def update_issue(issue_iid, updates: dict):
    """Update GitLab issue (real API call)"""
    url = f"{GITLAB_URL}/projects/{PROJECT_ID}/issues/{issue_iid}"
    r = requests.put(url, headers=HEADERS, json=updates)
    if r.status_code == 200:
        return True, r.json()
    else:
        return False, r.text

def download_commentary_as_docx(issues, filename="commentary.docx"):
    """Download commentary as a Word file"""
    doc = Document()
    doc.add_heading("Issue Commentary", level=1)
    for issue in issues:
        doc.add_paragraph(f"[{issue['iid']}] {issue['title']}")
        doc.add_paragraph(issue.get("description", "No description"))
        doc.add_paragraph("-" * 40)
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf, filename

def parse_labels(issue):
    """Extract Sprint and Team labels"""
    sprints = [lbl for lbl in issue["labels"] if lbl.lower().startswith("sprint")]
    teams = [lbl for lbl in issue["labels"] if lbl.lower().startswith("team")]
    return sprints, teams

# ----------------------------
# STREAMLIT APP
# ----------------------------
st.set_page_config(layout="wide")
st.title("GitLab Kanban & Issue Manager")

# Load issues
issues = fetch_issues()
df = pd.DataFrame([{
    "iid": i["iid"],
    "title": i["title"],
    "state": i["state"],
    "labels": i["labels"],
    "sprints": ", ".join(parse_labels(i)[0]),
    "teams": ", ".join(parse_labels(i)[1]),
    "web_url": i["web_url"]
} for i in issues])

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Kanban Board", "By Sprint", "Hygiene", "Commentary"])

# ----------------------------
# KANBAN BOARD
# ----------------------------
with tab1:
    st.subheader("Kanban Board (Teams × Status)")
    teams = sorted({t for teamlist in df["teams"].str.split(", ") for t in teamlist if t})
    statuses = ["opened", "in progress", "closed"]
    container = st.container()
    with container:
        cols = st.columns(len(teams))
        for col, team in zip(cols, teams):
            with col:
                st.markdown(f"### {team}")
                for status in statuses:
                    st.markdown(f"**{status.capitalize()}**")
                    subset = df[(df["teams"].str.contains(team)) & (df["state"] == status)]
                    for _, row in subset.iterrows():
                        st.write(f"[#{row['iid']}] {row['title']}")

# ----------------------------
# BY SPRINT
# ----------------------------
with tab2:
    st.subheader("Issues by Sprint")
    all_sprints = sorted({s for sprintlist in df["sprints"].str.split(", ") for s in sprintlist if s})
    for sprint in all_sprints:
        st.markdown(f"### {sprint}")
        sprint_df = df[df["sprints"].str.contains(sprint)]
        st.table(sprint_df[["iid", "title", "teams", "state"]])

# ----------------------------
# HYGIENE TAB
# ----------------------------
with tab3:
    st.subheader("Hygiene Checks")
    missing_team = df[df["teams"] == ""]
    missing_sprint = df[df["sprints"] == ""]
    if not missing_team.empty:
        st.error("Issues missing team:")
        st.table(missing_team[["iid", "title"]])
    if not missing_sprint.empty:
        st.error("Issues missing sprint:")
        st.table(missing_sprint[["iid", "title"]])

    st.write("🔧 Fix an issue directly:")
    issue_id = st.selectbox("Select Issue", df["iid"])
    field = st.selectbox("Field", ["title", "sprint", "team", "state"])
    if field == "sprint":
        new_val = st.selectbox("New Sprint", all_sprints)
        payload = {"labels": df.loc[df["iid"] == issue_id, "labels"].values[0] + [new_val]}
    elif field == "team":
        new_val = st.selectbox("New Team", teams)
        payload = {"labels": df.loc[df["iid"] == issue_id, "labels"].values[0] + [new_val]}
    elif field == "state":
        new_val = st.selectbox("New State", ["opened", "closed"])
        payload = {"state_event": "close" if new_val == "closed" else "reopen"}
    else:
        new_val = st.text_input("New Title")
        payload = {"title": new_val}

    if st.button("Update Issue"):
        ok, resp = update_issue(issue_id, payload)
        if ok:
            st.success(f"Issue #{issue_id} updated")
        else:
            st.error(f"Update failed: {resp}")

# ----------------------------
# COMMENTARY
# ----------------------------
with tab4:
    st.subheader("Commentary Download")
    buf, filename = download_commentary_as_docx(issues)
    st.download_button(
        label="Download Commentary (Word)",
        data=buf,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

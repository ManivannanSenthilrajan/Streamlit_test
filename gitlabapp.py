import streamlit as st
import pandas as pd
import requests
from collections import defaultdict
from docx import Document
from io import BytesIO

st.set_page_config(page_title="GitLab Issue Dashboard", layout="wide")

# ---------------- Sidebar Settings ----------------
st.sidebar.header("GitLab Connection")
base_url = st.sidebar.text_input("GitLab Base URL", "https://gitlab.com")
project_id = st.sidebar.text_input("Project ID", "")
private_token = st.sidebar.text_input("Private Token", type="password")

headers = {"PRIVATE-TOKEN": private_token}

# ---------------- Helper Functions ----------------
def fetch_issues():
    if not project_id or not private_token:
        return []
    url = f"{base_url}/api/v4/projects/{project_id}/issues?per_page=100"
    try:
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Failed to fetch issues: {e}")
        return []

def parse_labels(issue):
    parsed = defaultdict(list)
    for raw in issue.get("labels", []):
        if "::" in raw:
            key, val = raw.split("::", 1)
            key = key.strip().split("-",1)[-1].capitalize()
            val = val.strip()
            parsed[key].append(val)
    return {k: ", ".join(v) for k, v in parsed.items()}

def build_dataframe(issues):
    rows = []
    for issue in issues:
        labels = parse_labels(issue)
        rows.append({
            "ID": issue.get("iid", ""),
            "Title": issue.get("title", ""),
            "Description": issue.get("description", ""),
            "WebURL": issue.get("web_url", ""),
            "Milestone": issue.get("milestone", {}).get("title", ""),
            **labels
        })
    return pd.DataFrame(rows)

def update_issue(issue_id, title=None, description=None, labels=None):
    url = f"{base_url}/api/v4/projects/{project_id}/issues/{issue_id}"
    payload = {}
    if title: payload["title"] = title
    if description: payload["description"] = description
    if labels is not None: payload["labels"] = labels
    try:
        resp = requests.put(url, headers=headers, json=payload, verify=False)
        resp.raise_for_status()
        st.success(f"Issue {issue_id} updated")
    except Exception as e:
        st.error(f"Failed to update {issue_id}: {e}")

def download_commentary(scope, dates, achievements, next_steps, challenges, fmt="docx"):
    if fmt == "docx":
        doc = Document()
        doc.add_heading("Project Commentary", 0)
        doc.add_heading("Scope", level=1); doc.add_paragraph(scope)
        doc.add_heading("Key Dates", level=1); doc.add_paragraph(dates)
        doc.add_heading("Achievements", level=1); doc.add_paragraph(achievements)
        doc.add_heading("Next Steps", level=1); doc.add_paragraph(next_steps)
        doc.add_heading("Challenges", level=1); doc.add_paragraph(challenges)
        buf = BytesIO(); doc.save(buf); buf.seek(0)
        return buf, "docx"
    else:
        text = (
            f"Scope:\n{scope}\n\n"
            f"Key Dates:\n{dates}\n\n"
            f"Achievements:\n{achievements}\n\n"
            f"Next Steps:\n{next_steps}\n\n"
            f"Challenges:\n{challenges}"
        )
        return BytesIO(text.encode()), "txt"

# ---------------- Main App ----------------
st.title("📊 GitLab Issue Dashboard")
issues = fetch_issues()
if not issues:
    st.warning("No issues loaded yet. Enter settings in the sidebar.")
    st.stop()

df = build_dataframe(issues)

# ---------------- Sidebar Filters ----------------
with st.sidebar:
    st.header("🔍 Filters")
    filter_team = st.multiselect("Team", sorted(df["Team"].dropna().unique()) if "Team" in df else [])
    filter_status = st.multiselect("Status", sorted(df["Status"].dropna().unique()) if "Status" in df else [])
    filter_sprint = st.multiselect("Sprint", sorted(df["Sprint"].dropna().unique()) if "Sprint" in df else [])
    filter_project = st.multiselect("Project", sorted(df["Project"].dropna().unique()) if "Project" in df else [])
    filter_milestone = st.multiselect("Milestone", sorted(df["Milestone"].dropna().unique()) if "Milestone" in df else [])

    if filter_team: df = df[df["Team"].isin(filter_team)]
    if filter_status: df = df[df["Status"].isin(filter_status)]
    if filter_sprint: df = df[df["Sprint"].isin(filter_sprint)]
    if filter_project: df = df[df["Project"].isin(filter_project)]
    if filter_milestone: df = df[df["Milestone"].isin(filter_milestone)]

# ---------------- Tabs ----------------
tab_overview, tab_kanban, tab_sprint, tab_hygiene, tab_edit, tab_commentary = st.tabs(
    ["Overview","Kanban","By Sprint","Hygiene","Edit Issues","Commentary"]
)

# ---------------- Overview ----------------
with tab_overview:
    st.subheader("📌 Quick Metrics")
    cols = st.columns(4)
    metrics = {
        "Total Issues": len(df),
        "Teams": df["Team"].nunique() if "Team" in df else 0,
        "Sprints": df["Sprint"].nunique() if "Sprint" in df else 0,
        "Projects": df["Project"].nunique() if "Project" in df else 0
    }
    for i,(label,val) in enumerate(metrics.items()):
        with cols[i % 4]:
            st.metric(label,val)

    st.subheader("📋 Full Issue List")
    st.dataframe(df[["Team","Title","Description","Status","Project","WebURL"]])

# ---------------- Kanban ----------------
with tab_kanban:
    st.subheader("🗂 Kanban Board")
    if "Team" not in df or "Status" not in df:
        st.warning("No Team/Status data found.")
    else:
        teams = sorted(df["Team"].dropna().unique())
        statuses = sorted(df["Status"].dropna().unique())
        st.markdown("<div style='display:flex; overflow-x:auto;'>", unsafe_allow_html=True)
        for team in teams:
            st.markdown("<div style='min-width:300px;margin-right:10px;'>", unsafe_allow_html=True)
            st.markdown(f"### 👥 {team}")
            for status in statuses:
                st.markdown(f"**{status}**")
                subset = df[(df["Team"]==team) & (df["Status"]==status)]
                for _,row in subset.iterrows():
                    color="#a0e7a0" if status.lower()=="done" else "#f0f2f6"
                    st.markdown(f"<div style='padding:10px;margin:5px;border-radius:8px;background:{color};'>"
                                f"<b>{row['Title']}</b><br>"
                                f"<small>{row['Description'][:50]}...</small><br>"
                                f"<a href='{row['WebURL']}' target='_blank'>🔗 Open</a></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------- By Sprint ----------------
with tab_sprint:
    st.subheader("📅 Issues by Sprint")
    if "Sprint" not in df:
        st.warning("No Sprint data found.")
    else:
        all_sprints = sorted(set(sum([s.split(", ") for s in df["Sprint"].dropna()], [])))
        for sprint in all_sprints:
            st.markdown(f"### 🏁 {sprint}")
            subset = df[df["Sprint"].fillna("").str.contains(sprint)]
            st.dataframe(subset.sort_values("Team"))

# ---------------- Hygiene ----------------
with tab_hygiene:
    st.subheader("🧹 Hygiene Check")
    missing_fields = ["Team","Status","Sprint","Project","Milestone","Title"]
    for field in missing_fields:
        if field in df:
            missing = df[df[field].isna() | (df[field]=="")]
            if not missing.empty:
                st.markdown(f"**{field} Missing ({len(missing)})**")
                for _, row in missing.iterrows():
                    with st.expander(f"Issue {row['ID']}: {row['Title']}"):
                        new_val = st.text_input(f"Set {field}", key=f"fix_{field}_{row['ID']}")
                        if st.button(f"Fix {field} for {row['ID']}", key=f"btn_fix_{field}_{row['ID']}"):
                            labels = row.get("Labels","").split(", ") if "Labels" in row else []
                            labels.append(f"{field}::{new_val}")
                            update_issue(row["ID"], labels=",".join(labels))

# ---------------- Edit Issues ----------------
with tab_edit:
    st.subheader("✏️ Edit Issues")
    issue_id = st.selectbox("Choose Issue", df["ID"])
    issue_row = df[df["ID"]==issue_id].iloc[0]

    new_title = st.text_input("Title", issue_row["Title"])
    new_desc = st.text_area("Description", issue_row["Description"])
    new_team = st.selectbox("Team", [""]+sorted(df["Team"].dropna().unique()))
    new_status = st.selectbox("Status", [""]+sorted(df["Status"].dropna().unique()))
    new_sprint = st.selectbox("Sprint", [""]+sorted(df["Sprint"].dropna().unique()))
    new_project = st.selectbox("Project", [""]+sorted(df["Project"].dropna().unique()))
    new_milestone = st.selectbox("Milestone", [""]+sorted(df["Milestone"].dropna().unique()))

    if st.button("Update Issue"):
        new_labels=[]
        if new_team: new_labels.append(f"Team::{new_team}")
        if new_status: new_labels.append(f"Status::{new_status}")
        if new_sprint: new_labels.append(f"Sprint::{new_sprint}")
        if new_project: new_labels.append(f"Project::{new_project}")
        if new_milestone: new_labels.append(f"Milestone::{new_milestone}")
        update_issue(issue_id, title=new_title, description=new_desc, labels=",".join(new_labels))

# ---------------- Commentary ----------------
with tab_commentary:
    st.subheader("📝 Project Commentary")
    scope = st.text_area("Scope")
    dates = st.text_area("Key Dates")
    achievements = st.text_area("Achievements")
    next_steps = st.text_area("Next Steps")
    challenges = st.text_area("Challenges")
    fmt = st.radio("Download as", ["docx","txt"], horizontal=True)

    if st.button("Download Commentary"):
        buf, ext = download_commentary(scope, dates, achievements, next_steps, challenges, fmt)
        st.download_button("Download File", buf, file_name=f"commentary.{ext}")

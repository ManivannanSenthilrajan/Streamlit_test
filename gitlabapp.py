import streamlit as st
import requests
import pandas as pd
import json
import os
import re

st.set_page_config(page_title="GitLab Issue Dashboard", layout="wide")

# ------------------------
# Helpers
# ------------------------
def safe_get_json(response):
    try:
        if response and response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def safe_milestone(issue):
    milestone = issue.get("milestone")
    if milestone and isinstance(milestone, dict):
        return milestone.get("title", "")
    return ""

def parse_labels(labels):
    parsed = {
        "Team": "",
        "Status": "",
        "Sprint": "",
        "Project": "",
        "Workstream": "",
        "Milestone": ""
    }
    for raw_label in labels:
        label = re.sub(r"^\d+\-?\s*", "", raw_label.strip())
        if "::" not in label:
            continue
        key, value = label.split("::", 1)
        key = key.strip().title()
        value = value.strip()
        if key.startswith("Team"):
            parsed["Team"] = value
        elif key.startswith("Status"):
            parsed["Status"] = value
        elif key.startswith("Sprint"):
            parsed["Sprint"] = value
        elif key.startswith("Project"):
            parsed["Project"] = value
        elif key.startswith("Workstream"):
            parsed["Workstream"] = value
        elif key.startswith("Milestone"):
            parsed["Milestone"] = value
    return parsed

def fetch_issues(base_url, project_id, token):
    headers = {"PRIVATE-TOKEN": token}
    url = f"{base_url}/api/v4/projects/{project_id}/issues?per_page=100"
    resp = requests.get(url, headers=headers, verify=False)
    issues = safe_get_json(resp)
    parsed = []
    for issue in issues:
        labels = issue.get("labels", [])
        parsed_labels = parse_labels(labels)
        parsed.append({
            "iid": issue.get("iid"),
            "title": issue.get("title", "Untitled"),
            "description": issue.get("description", ""),
            "team": parsed_labels["Team"],
            "status": parsed_labels["Status"],
            "sprint": parsed_labels["Sprint"],
            "project": parsed_labels["Project"],
            "workstream": parsed_labels["Workstream"],
            "milestone": parsed_labels["Milestone"] or safe_milestone(issue),
            "labels": labels,
            "web_url": issue.get("web_url", "")
        })
    return pd.DataFrame(parsed)

def update_issue(base_url, project_id, token, iid, payload):
    headers = {"PRIVATE-TOKEN": token}
    url = f"{base_url}/api/v4/projects/{project_id}/issues/{iid}"
    resp = requests.put(url, headers=headers, json=payload, verify=False)
    return resp.status_code == 200

STATUS_COLORS = {
    "Done": "#2ecc71",
    "In Progress": "#f1c40f",
    "To Do": "#e74c3c",
    "Blocked": "#e67e22",
    "": "#bdc3c7"
}

# ------------------------
# Sidebar
# ------------------------
st.sidebar.header("🔑 GitLab Connection")
base_url = st.sidebar.text_input("Base URL", value="https://gitlab.com")
project_id = st.sidebar.text_input("Project ID")
token = st.sidebar.text_input("Access Token", type="password")

if not (base_url and project_id and token):
    st.warning("Enter Base URL, Project ID, and Access Token to continue.")
    st.stop()

df = fetch_issues(base_url, project_id, token)
if df.empty:
    st.warning("No issues found. Check project ID or token.")
    st.stop()

# Filters
st.sidebar.header("⚙️ Filters")
all_sprints = sorted(df["sprint"].dropna().unique().tolist())
all_teams = sorted(df["team"].dropna().unique().tolist())
all_projects = sorted(df["project"].dropna().unique().tolist())
all_milestones = sorted(df["milestone"].dropna().unique().tolist())
all_statuses = sorted(df["status"].dropna().unique().tolist())

filter_sprint = st.sidebar.multiselect("Sprint", all_sprints)
filter_team = st.sidebar.multiselect("Team", all_teams)
filter_project = st.sidebar.multiselect("Project", all_projects)
filter_milestone = st.sidebar.multiselect("Milestone", all_milestones)
filter_status = st.sidebar.multiselect("Status", all_statuses)

filtered_df = df.copy()
if filter_sprint:
    filtered_df = filtered_df[filtered_df["sprint"].isin(filter_sprint)]
if filter_team:
    filtered_df = filtered_df[filtered_df["team"].isin(filter_team)]
if filter_project:
    filtered_df = filtered_df[filtered_df["project"].isin(filter_project)]
if filter_milestone:
    filtered_df = filtered_df[filtered_df["milestone"].isin(filter_milestone)]
if filter_status:
    filtered_df = filtered_df[filtered_df["status"].isin(filter_status)]

# ------------------------
# Tabs
# ------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Overview", "🗂️ Kanban", "🧹 Hygiene", "📝 Commentary", "✏️ Edit"]
)

# ------------------------
# Tab 1: Overview
# ------------------------
with tab1:
    st.subheader("Overview Dashboard")
    cols = st.columns(4)
    for i, field in enumerate(["status", "team", "sprint", "project"]):
        counts = filtered_df[field].replace("", "None").value_counts()
        with cols[i]:
            st.metric(label=field.title(), value=len(counts))
            for k, v in counts.items():
                st.write(f"{k}: {v}")
    st.markdown("### Full Issue Table")
    st.dataframe(filtered_df[["team","title","description","status","project","web_url"]])
    st.download_button("⬇️ Download Overview Data", filtered_df.to_csv(index=False), "overview.csv")

# ------------------------
# Tab 2: Kanban
# ------------------------
with tab2:
    st.subheader("Kanban Board")
    group_by = st.radio("Swimlane by", ["Status", "Team"])
    kanban_df = filtered_df.copy()
    kanban_df[group_by.lower()] = kanban_df[group_by.lower()].replace("", "None")
    kanban_df = kanban_df.sort_values("team") if group_by=="Status" else kanban_df.sort_values("status")
    swimlanes = kanban_df[group_by.lower()].unique()
    cols = st.columns(len(swimlanes) or 1)
    for i, lane in enumerate(swimlanes):
        with cols[i]:
            st.markdown(f"**{lane}**")
            for _, row in kanban_df[kanban_df[group_by.lower()]==lane].iterrows():
                color = STATUS_COLORS.get(row["status"], "#bdc3c7")
                if st.button(f"#{row['iid']} - {row['title']}", key=f"card_{row['iid']}"):
                    col1, col2 = st.columns([3,2])
                    with col1:
                        st.markdown(f"<div style='background-color:{color};padding:10px;border-radius:5px'>**{row['title']}**</div>", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"**Team:** {row['team']}  \n**Status:** {row['status']}  \n**Sprint:** {row['sprint']}  \n**Milestone:** {row['milestone']}")
                        st.markdown(f"[Open in GitLab]({row['web_url']})")
                        st.markdown(f"Description:\n{row['description']}")

# ------------------------
# Tab 3: Hygiene
# ------------------------
with tab3:
    st.subheader("Hygiene Checks")
    fields = ["team","status","sprint","project","title"]
    cols = st.columns(len(fields))
    for i, f in enumerate(fields):
        with cols[i]:
            missing_count = len(filtered_df[filtered_df[f]==""])
            if st.button(f"{f.title()} Missing: {missing_count}", key=f"btn_{f}"):
                missing = filtered_df[filtered_df[f]==""] 
                for _, row in missing.iterrows():
                    with st.expander(f"Issue #{row['iid']} - {row['title']}"):
                        new_val = st.text_input(f"Update {f}", key=f"fix_{f}_{row['iid']}")
                        if st.button("Apply Fix", key=f"btn_fix_{f}_{row['iid']}"):
                            payload = {}
                            if f in ["title","description"]:
                                payload[f] = new_val
                            else:
                                labels = row["labels"]
                                labels = [lbl for lbl in labels if not re.match(rf"\d*-?\s*{f}.*::", lbl, re.I)]
                                labels.append(f"{f.title()}::{new_val}")
                                payload["labels"] = labels
                            success = update_issue(base_url, project_id, token, row["iid"], payload)
                            if success:
                                st.success("Updated!")
                            else:
                                st.error("Failed to update")

# ------------------------
# Tab 4: Commentary
# ------------------------
with tab4:
    st.subheader("Sprint Commentary")
    sprints = df["sprint"].dropna().unique()
    sprint_sel = st.selectbox("Select Sprint", sprints)
    scope = st.text_area("Scope")
    key_dates = st.text_area("Key Dates")
    achievements = st.text_area("Achievements")
    next_steps = st.text_area("Next Steps")
    challenges = st.text_area("Challenges")

    commentary_file = "commentary.json"
    if st.button("💾 Save Commentary"):
        entry = {"sprint": sprint_sel,"scope":scope,"key_dates":key_dates,
                 "achievements":achievements,"next_steps":next_steps,"challenges":challenges}
        all_notes = []
        if os.path.exists(commentary_file):
            with open(commentary_file,"r") as f:
                all_notes = json.load(f)
        all_notes.append(entry)
        with open(commentary_file,"w") as f:
            json.dump(all_notes,f,indent=2)
        st.success("Saved!")

    if os.path.exists(commentary_file):
        with open(commentary_file,"r") as f:
            all_notes = json.load(f)
        for note in all_notes:
            st.markdown(f"### Sprint {note['sprint']}")
            st.write(note)
        st.download_button("⬇️ Download Commentary", json.dumps(all_notes, indent=2), "commentary.json")

# ------------------------
# Tab 5: Edit
# ------------------------
with tab5:
    st.subheader("Edit Issues")
    issue_id = st.selectbox("Select Issue", filtered_df["iid"].tolist())
    issue_row = filtered_df[filtered_df["iid"]==issue_id].iloc[0]

    new_title = st.text_input("Title", issue_row["title"])
    new_desc = st.text_area("Description", issue_row["description"])
    new_team = st.text_input("Team", issue_row["team"])
    new_status = st.text_input("Status", issue_row["status"])
    new_sprint = st.text_input("Sprint", issue_row["sprint"])
    new_project = st.text_input("Project", issue_row["project"])
    new_workstream = st.text_input("Workstream", issue_row["workstream"])
    new_milestone = st.text_input("Milestone", issue_row["milestone"])

    if st.button("✅ Save Changes"):
        labels = []
        if new_team: labels.append(f"Team::{new_team}")
        if new_status: labels.append(f"Status::{new_status}")
        if new_sprint: labels.append(f"Sprint::{new_sprint}")
        if new_project: labels.append(f"Project::{new_project}")
        if new_workstream: labels.append(f"Workstream::{new_workstream}")
        if new_milestone: labels.append(f"Milestone::{new_milestone}")
        payload = {
            "title": new_title,
            "description": new_desc,
            "labels": labels
        }
        success = update_issue(base_url, project_id, token, issue_id, payload)
        if success:
            st.success("Updated!")
        else:
            st.error("Failed to update")

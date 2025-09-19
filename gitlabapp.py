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

def normalize_label(raw_label):
    # Remove numeric prefix like "07-" and extra spaces
    label = re.sub(r"^\d+\-?\s*", "", raw_label.strip())
    return label

def parse_labels(labels):
    parsed = {"Team": "", "Status": "", "Sprint": "", "Project": "", "Workstream": "", "Milestone": ""}
    for raw_label in labels:
        label = normalize_label(raw_label)
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
all_sprints = sorted(df["sprint"].dropna().unique())
all_teams = sorted(df["team"].dropna().unique())
all_projects = sorted(df["project"].dropna().unique())
all_milestones = sorted(df["milestone"].dropna().unique())
all_statuses = sorted(df["status"].dropna().unique())

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
                st.markdown(f"<div>{k}: {v}</div>", unsafe_allow_html=True)
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
    swimlanes = kanban_df[group_by.lower()].unique()
    
    # Main columns: Left = board, Right = issue detail
    board_col, detail_col = st.columns([3,2])
    
    with board_col:
        for lane in swimlanes:
            st.markdown(f"### {lane}")
            lane_issues = kanban_df[kanban_df[group_by.lower()]==lane]
            for _, row in lane_issues.iterrows():
                color = STATUS_COLORS.get(row["status"], "#bdc3c7")
                if st.button(f"#{row['iid']} - {row['title']}", key=f"card_{row['iid']}"):
                    st.session_state["selected_issue"] = row["iid"]

    with detail_col:
        selected_iid = st.session_state.get("selected_issue")
        if selected_iid:
            issue = kanban_df[kanban_df["iid"]==selected_iid].iloc[0]
            st.markdown(f"<div style='background-color:{STATUS_COLORS.get(issue['status'],'#bdc3c7')};padding:10px;border-radius:5px'><h4>{issue['title']}</h4></div>", unsafe_allow_html=True)
            st.markdown(f"**Team:** {issue['team']}  \n**Status:** {issue['status']}  \n**Sprint:** {issue['sprint']}  \n**Milestone:** {issue['milestone']}  \n**Project:** {issue['project']}")
            st.markdown(f"**Description:**\n{issue['description']}")
            st.markdown(f"[Open in GitLab]({issue['web_url']})")

# ------------------------
# Hygiene, Commentary, Edit tabs remain same as before
# ------------------------
# [Keep the previous implementation from your working code for Tab 3, Tab 4, Tab 5]
# Ensure label parsing is consistent with normalize_label, numeric prefixes stripped, etc.


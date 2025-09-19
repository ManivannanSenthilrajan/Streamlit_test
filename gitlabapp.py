import streamlit as st
import pandas as pd
import requests
import json
import re
import os

st.set_page_config(page_title="GitLab Dashboard", layout="wide")

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

# ------------------------
# Sidebar Filters
# ------------------------
st.sidebar.header("⚙️ Filters")
all_sprints = sorted(df["sprint"].replace("", "None").unique())
all_teams = sorted(df["team"].replace("", "None").unique())
all_projects = sorted(df["project"].replace("", "None").unique())
all_milestones = sorted(df["milestone"].replace("", "None").unique())
all_statuses = sorted(df["status"].replace("", "None").unique())

filter_sprint = st.sidebar.multiselect("Sprint", all_sprints, key="filter_sprint")
filter_team = st.sidebar.multiselect("Team", all_teams, key="filter_team")
filter_project = st.sidebar.multiselect("Project", all_projects, key="filter_project")
filter_milestone = st.sidebar.multiselect("Milestone", all_milestones, key="filter_milestone")
filter_status = st.sidebar.multiselect("Status", all_statuses, key="filter_status")

if st.sidebar.button("Reset Filters"):
    st.session_state.update({
        "filter_sprint": [],
        "filter_team": [],
        "filter_project": [],
        "filter_milestone": [],
        "filter_status": []
    })

filtered_df = df.copy()
if filter_sprint:
    filtered_df = filtered_df[filtered_df["sprint"].replace("", "None").isin(filter_sprint)]
if filter_team:
    filtered_df = filtered_df[filtered_df["team"].replace("", "None").isin(filter_team)]
if filter_project:
    filtered_df = filtered_df[filtered_df["project"].replace("", "None").isin(filter_project)]
if filter_milestone:
    filtered_df = filtered_df[filtered_df["milestone"].replace("", "None").isin(filter_milestone)]
if filter_status:
    filtered_df = filtered_df[filtered_df["status"].replace("", "None").isin(filter_status)]

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
    metric_cols = st.columns(4)
    for idx, field in enumerate(["status", "team", "sprint", "project"]):
        col = metric_cols[idx]
        with col:
            st.markdown(f"#### {field.title()}")
            values = sorted(filtered_df[field].replace("", "None").unique())
            for val in values:
                count = len(filtered_df[filtered_df[field].replace("", "None")==val])
                color = STATUS_COLORS.get(val, "#3498db")
                if st.button(f"{val} ({count})", key=f"overview_{field}_{val}"):
                    st.session_state[f"filter_{field}"] = [val]

    temp_df = filtered_df.copy()
    for field in ["status", "team", "sprint", "project"]:
        val = st.session_state.get(f"filter_{field}")
        if val:
            temp_df = temp_df[temp_df[field].replace("", "None").isin(val)]

    st.markdown("### Issues Table")
    st.dataframe(temp_df[["team","title","description","status","project","web_url"]])
    st.download_button("⬇️ Download Overview Data", temp_df.to_csv(index=False), "overview.csv")

# ------------------------
# Tab 2: Kanban Board
# ------------------------
with tab2:
    st.subheader("Kanban Board")
    group_by = st.radio("Swimlane by", ["Status", "Team", "Sprint"], horizontal=True)
    kanban_df = filtered_df.copy()
    kanban_df[group_by.lower()] = kanban_df[group_by.lower()].replace("", "None")
    swimlanes = sorted(kanban_df[group_by.lower()].unique())

    if "selected_issue" not in st.session_state:
        st.session_state["selected_issue"] = None

    board_col, detail_col = st.columns([3,2])

    # Horizontal scroll wrapper
    with board_col:
        st.markdown('<div style="display:flex; overflow-x:auto; gap:15px;">', unsafe_allow_html=True)
        for lane in swimlanes:
            lane_issues = kanban_df[kanban_df[group_by.lower()]==lane].sort_values(["team","title"])
            st.markdown(f'<div style="flex:0 0 250px; background:#f9f9f9; padding:10px; border-radius:5px;">', unsafe_allow_html=True)
            st.markdown(f"<h4>{lane}</h4>", unsafe_allow_html=True)
            for _, row in lane_issues.iterrows():
                color = STATUS_COLORS.get(row["status"], "#bdc3c7")
                if st.button(f"#{row['iid']} - {row['title']}", key=f"card_{row['iid']}"):
                    st.session_state["selected_issue"] = row["iid"]
                st.markdown(f'<div style="background:{color}; padding:5px; margin-bottom:5px; border-radius:5px;"></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with detail_col:
        selected_iid = st.session_state.get("selected_issue")
        if selected_iid:
            issue = kanban_df[kanban_df["iid"]==selected_iid].iloc[0]
            if st.button("Close Details"):
                st.session_state["selected_issue"] = None
            else:
                st.markdown(f"<div style='background-color:{STATUS_COLORS.get(issue['status'],'#bdc3c7')};padding:10px;border-radius:5px'><h4>{issue['title']}</h4></div>", unsafe_allow_html=True)
                st.markdown(f"**Team:** {issue['team']}  \n**Status:** {issue['status']}  \n**Sprint:** {issue['sprint']}  \n**Milestone:** {issue['milestone']}  \n**Project:** {issue['project']}")
                st.markdown(f"**Description:**\n{issue['description']}")
                st.markdown(f"[Open in GitLab]({issue['web_url']})")

# ------------------------
# Tab 3: Hygiene
# ------------------------
with tab3:
    st.subheader("Hygiene Checks")
    hygiene_metrics = {
        "No Team": filtered_df[filtered_df["team"]==""],
        "No Status": filtered_df[filtered_df["status"]==""],
        "No Project": filtered_df[filtered_df["project"]==""],
        "No Sprint": filtered_df[filtered_df["sprint"]==""],
        "No Milestone": filtered_df[filtered_df["milestone"]==""],
        "No Title": filtered_df[filtered_df["title"]==""]
    }
    cols = st.columns(len(hygiene_metrics))
    for i, (k,v) in enumerate(hygiene_metrics.items()):
        with cols[i]:
            if st.button(f"{k} ({len(v)})", key=f"hygiene_{i}"):
                st.dataframe(v[["iid","title","description","team","status","project","sprint","milestone"]])

# ------------------------
# Tab 4: Commentary
# ------------------------
with tab4:
    st.subheader("Commentary")
    commentary_file = "commentary.json"
    if os.path.exists(commentary_file):
        with open(commentary_file,"r") as f:
            commentary_data = json.load(f)
    else:
        commentary_data = {}

    sprints_available = sorted(filtered_df["sprint"].replace("", "None").unique())
    selected_sprint = st.selectbox("Select Sprint", sprints_available)
    commentary = commentary_data.get(selected_sprint, {})
    commentary["Scope"] = st.text_area("Scope", commentary.get("Scope",""))
    commentary["Key Dates"] = st.text_area("Key Dates", commentary.get("Key Dates",""))
    commentary["Achievements"] = st.text_area("Achievements", commentary.get("Achievements",""))
    commentary["Next Steps"] = st.text_area("Next Steps", commentary.get("Next Steps",""))
    commentary["Challenges"] = st.text_area("Challenges / Risks", commentary.get("Challenges",""))

    if st.button("Save Commentary"):
        commentary_data[selected_sprint] = commentary
        with open(commentary_file,"w") as f:
            json.dump(commentary_data,f,indent=2)
        st.success("Saved successfully!")
    st.download_button("⬇️ Download Commentary JSON", json.dumps(commentary_data, indent=2), "commentary.json")

# ------------------------
# Tab 5: Edit
# ------------------------
with tab5:
    st.subheader("Edit Issues")
    issue_titles = [f"#{row['iid']} - {row['title']}" for _, row in filtered_df.iterrows()]
    selected_issue_title = st.selectbox("Select Issue", [""]+issue_titles)

    if selected_issue_title:
        iid = int(selected_issue_title.split(" ")[0][1:])
        issue = df[df["iid"]==iid].iloc[0]

        new_title = st.text_input("Title", issue["title"])
        new_desc = st.text_area("Description", issue["description"])
        new_team = st.text_input("Team", issue["team"])
        new_status = st.text_input("Status", issue["status"])
        new_sprint = st.text_input("Sprint", issue["sprint"])
        new_project = st.text_input("Project", issue["project"])
        new_workstream = st.text_input("Workstream", issue["workstream"])
        new_milestone = st.text_input("Milestone", issue["milestone"])

        if st.button("Apply Changes to GitLab"):
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
            success = update_issue(base_url, project_id, token, iid, payload)
            if success:
                st.success("Issue updated successfully!")
            else:
                st.error("Failed to update issue.")

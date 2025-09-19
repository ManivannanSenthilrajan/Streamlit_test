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
    """
    Robustly parse GitLab labels into normalized fields.
    Handles numeric prefixes, dashes, spaces, inconsistent capitalization.
    """
    parsed = {
        "Team": "",
        "Status": "",
        "Sprint": "",
        "Project": "",
        "Workstream": "",
        "Milestone": ""
    }

    for raw_label in labels:
        # Remove leading numbers, optional dash, and spaces
        label = re.sub(r"^\d+\-?\s*", "", raw_label.strip())

        if "::" not in label:
            continue

        key, value = label.split("::", 1)
        key = key.strip().title()      # normalize key
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
            "labels": labels
        })
    return pd.DataFrame(parsed)

def update_issue(base_url, project_id, token, iid, payload):
    headers = {"PRIVATE-TOKEN": token}
    url = f"{base_url}/api/v4/projects/{project_id}/issues/{iid}"
    resp = requests.put(url, headers=headers, json=payload, verify=False)
    return resp.status_code == 200

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

# Fetch issues
df = fetch_issues(base_url, project_id, token)
if df.empty:
    st.warning("No issues found. Check your project ID or token.")
    st.stop()

# ------------------------
# Tabs
# ------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Overview", "🗂️ By Sprint", "🧹 Hygiene", "📝 Commentary", "✏️ Edit"]
)

# ------------------------
# Tab 1: Overview
# ------------------------
with tab1:
    st.subheader("Overview")
    for col_name in ["status", "team", "sprint", "project"]:
        st.markdown(f"### {col_name.title()}")
        counts = df[col_name].replace("", "None").value_counts()
        st.dataframe(counts)
    st.download_button("⬇️ Download Overview Data", df.to_csv(index=False), "overview.csv")

# ------------------------
# Tab 2: By Sprint (Kanban)
# ------------------------
with tab2:
    st.subheader("By Sprint / Kanban")
    sprint = st.selectbox("Select Sprint", ["All"] + sorted(df["sprint"].dropna().unique().tolist()))
    sprint_df = df if sprint == "All" else df[df["sprint"] == sprint]

    statuses = sprint_df["status"].replace("", "No Status").unique().tolist()
    cols = st.columns(len(statuses) or 1)
    for i, status in enumerate(statuses):
        with cols[i]:
            st.markdown(f"**{status}**")
            for _, row in sprint_df[sprint_df["status"].replace("", "No Status") == status].iterrows():
                st.info(f"#{row['iid']} - {row['title']}")

    st.download_button("⬇️ Download Sprint Data", sprint_df.to_csv(index=False), "sprint.csv")

# ------------------------
# Tab 3: Hygiene
# ------------------------
with tab3:
    st.subheader("Hygiene Checks")
    required_fields = ["team", "status", "sprint", "project", "title"]
    for field in required_fields:
        missing = df[df[field] == ""]
        if not missing.empty:
            st.markdown(f"### Missing {field.title()}")
            for _, row in missing.iterrows():
                with st.expander(f"Issue #{row['iid']} - {row['title']}"):
                    new_val = st.text_input(f"Update {field}", key=f"fix_{field}_{row['iid']}")
                    if st.button("Apply Fix", key=f"btn_{field}_{row['iid']}"):
                        payload = {}
                        if field in ["title", "description"]:
                            payload[field] = new_val
                        else:
                            # update label
                            labels = row["labels"]
                            # Remove any existing label of this field
                            labels = [lbl for lbl in labels if not re.match(rf"\d*-?\s*{field}.*::", lbl, re.I)]
                            labels.append(f"{field.title()}::{new_val}")
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
    commentary_file = "commentary.json"
    sprints = df["sprint"].dropna().unique().tolist()
    sprint_sel = st.selectbox("Select Sprint", sprints)
    notes = st.text_area("Enter Commentary")

    if st.button("💾 Save Commentary"):
        entry = {"sprint": sprint_sel, "notes": notes}
        all_notes = []
        if os.path.exists(commentary_file):
            with open(commentary_file, "r") as f:
                all_notes = json.load(f)
        all_notes.append(entry)
        with open(commentary_file, "w") as f:
            json.dump(all_notes, f, indent=2)
        st.success("Saved commentary")

    if os.path.exists(commentary_file):
        with open(commentary_file, "r") as f:
            all_notes = json.load(f)
        st.download_button("⬇️ Download Commentary", json.dumps(all_notes, indent=2), "commentary.json")

# ------------------------
# Tab 5: Edit
# ------------------------
with tab5:
    st.subheader("Edit Issues")
    issue_id = st.selectbox("Select Issue", df["iid"].tolist())
    issue_row = df[df["iid"] == issue_id].iloc[0]

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

        payload = {"title": new_title, "description": new_desc, "labels": labels}
        success = update_issue(base_url, project_id, token, issue_id, payload)
        if success:
            st.success("Updated!")
        else:
            st.error("Failed to update")

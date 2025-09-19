import streamlit as st
import requests
import pandas as pd
import json

# ========================
# Helpers
# ========================

def safe_milestone(issue: dict) -> str:
    """Extract milestone title safely."""
    try:
        milestone = issue.get("milestone")
        if milestone and isinstance(milestone, dict):
            return milestone.get("title", "")
        return ""
    except Exception:
        return ""

def parse_labels(labels):
    """Parse labels into structured dict (Team, Status, Sprint, Project, Workstream, etc)."""
    parsed = {"Team": "", "Status": "", "Sprint": "", "Project": "", "Workstream": ""}
    for label in labels:
        if "::" in label:
            key, value = label.split("::", 1)
            key = key.strip().title()  # normalize
            value = value.strip()
            # remove ordering numbers like "01 Project"
            key = "".join([c for c in key if not c.isdigit()]).strip()
            if key in parsed:
                parsed[key] = value
    return parsed

def fetch_issues(base_url, project_id, token):
    url = f"{base_url}/api/v4/projects/{project_id}/issues?per_page=100"
    headers = {"PRIVATE-TOKEN": token}
    try:
        r = requests.get(url, headers=headers, verify=False)  # user asked verify=False
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Error fetching issues: {e}")
        return []

def build_dataframe(issues):
    rows = []
    for issue in issues:
        labels = issue.get("labels", [])
        parsed = parse_labels(labels)
        rows.append({
            "IID": issue.get("iid"),
            "Title": issue.get("title", ""),
            "Description": issue.get("description", ""),
            "Team": parsed["Team"],
            "Status": parsed["Status"],
            "Sprint": parsed["Sprint"],
            "Project": parsed["Project"],
            "Workstream": parsed["Workstream"],
            "Milestone": safe_milestone(issue),
            "Labels": ", ".join(labels)
        })
    return pd.DataFrame(rows)

def update_issue(base_url, project_id, token, issue_iid, updates):
    url = f"{base_url}/api/v4/projects/{project_id}/issues/{issue_iid}"
    headers = {"PRIVATE-TOKEN": token}
    try:
        r = requests.put(url, headers=headers, data=updates, verify=False)
        if r.status_code == 200:
            st.success(f"Issue {issue_iid} updated successfully.")
        else:
            st.error(f"Failed to update issue {issue_iid}: {r.text}")
    except Exception as e:
        st.error(f"Error updating issue: {e}")

# ========================
# Streamlit UI
# ========================

st.set_page_config(page_title="GitLab Issue Dashboard", layout="wide")

st.sidebar.header("🔧 Configuration")
base_url = st.sidebar.text_input("GitLab Base URL", "https://gitlab.com")
project_id = st.sidebar.text_input("Project ID")
token = st.sidebar.text_input("Access Token", type="password")

if project_id and token:
    issues = fetch_issues(base_url, project_id, token)
    if issues:
        df = build_dataframe(issues)

        tab_overview, tab_kanban, tab_hygiene, tab_commentary, tab_edit = st.tabs(
            ["📊 Overview", "🗂️ By Sprint/Team/Status", "🧹 Hygiene", "📝 Commentary", "✏️ Edit"]
        )

        # -----------------
        # Overview Tab
        # -----------------
        with tab_overview:
            st.subheader("Overview")
            counts = df.groupby("Status").size().reset_index(name="Count")
            st.dataframe(counts)
            st.download_button("⬇️ Download Overview", counts.to_csv(index=False), "overview.csv")

        # -----------------
        # Kanban Tab
        # -----------------
        with tab_kanban:
            st.subheader("By Sprint → Team → Status")
            sprint = st.selectbox("Select Sprint", ["All"] + sorted(df["Sprint"].dropna().unique().tolist()))
            subset = df if sprint == "All" else df[df["Sprint"] == sprint]

            if not subset.empty:
                for team in subset["Team"].unique():
                    st.markdown(f"### Team {team or 'Unassigned'}")
                    team_data = subset[subset["Team"] == team]
                    for status in team_data["Status"].unique():
                        st.markdown(f"**{status or 'No Status'}**")
                        for _, row in team_data[team_data["Status"] == status].iterrows():
                            st.write(f"🔹 {row['IID']} - {row['Title']}")

        # -----------------
        # Hygiene Tab
        # -----------------
        with tab_hygiene:
            st.subheader("Hygiene Checks")
            hygiene_issues = []
            for _, row in df.iterrows():
                if not row["Team"]:
                    hygiene_issues.append((row["IID"], "Missing Team"))
                if not row["Status"]:
                    hygiene_issues.append((row["IID"], "Missing Status"))
                if not row["Sprint"]:
                    hygiene_issues.append((row["IID"], "Missing Sprint"))
                if not row["Project"]:
                    hygiene_issues.append((row["IID"], "Missing Project"))

            if hygiene_issues:
                for iid, problem in hygiene_issues:
                    st.write(f"Issue {iid}: {problem}")
                    if st.button(f"Fix {problem} for {iid}", key=f"fix_{iid}_{problem}"):
                        new_value = st.text_input(f"Enter value for {problem}", key=f"val_{iid}_{problem}")
                        if new_value:
                            label_key = problem.split()[-1]
                            update_issue(base_url, project_id, token, iid, {"labels": f"{label_key}::{new_value}"})
            else:
                st.success("No hygiene issues found 🎉")

        # -----------------
        # Commentary Tab
        # -----------------
        with tab_commentary:
            st.subheader("Sprint Commentary")
            sprint = st.selectbox("Select Sprint", sorted(df["Sprint"].dropna().unique().tolist()))
            commentary = st.text_area("Enter commentary")
            if st.button("💾 Save Commentary"):
                try:
                    data = {"sprint": sprint, "commentary": commentary}
                    with open("commentary.json", "a") as f:
                        f.write(json.dumps(data) + "\n")
                    st.success("Saved locally to commentary.json")
                except Exception as e:
                    st.error(f"Error saving commentary: {e}")

        # -----------------
        # Edit Tab
        # -----------------
        with tab_edit:
            st.subheader("Edit Issues")
            iid = st.selectbox("Select Issue", df["IID"].tolist())
            issue_row = df[df["IID"] == iid].iloc[0]

            new_title = st.text_input("Title", issue_row["Title"])
            new_desc = st.text_area("Description", issue_row["Description"])
            new_team = st.text_input("Team", issue_row["Team"])
            new_status = st.text_input("Status", issue_row["Status"])
            new_sprint = st.text_input("Sprint", issue_row["Sprint"])
            new_project = st.text_input("Project", issue_row["Project"])

            if st.button("Update Issue"):
                labels = []
                if new_team: labels.append(f"Team::{new_team}")
                if new_status: labels.append(f"Status::{new_status}")
                if new_sprint: labels.append(f"Sprint::{new_sprint}")
                if new_project: labels.append(f"Project::{new_project}")
                updates = {"title": new_title, "description": new_desc, "labels": labels}
                update_issue(base_url, project_id, token, iid, updates)

import streamlit as st
import requests
import pandas as pd
import json
import os
from io import BytesIO
import urllib3

# ------------------------
# Page Config
# ------------------------
st.set_page_config(page_title="GitLab Issues Dashboard", layout="wide")

# ------------------------
# CSS Styling
# ------------------------
st.markdown(
    """
    <style>
    body, div, p, span, input, textarea, select, button {
        font-family: "Frutiger45Light", "Segoe UI", "Helvetica Neue", Arial, sans-serif !important;
    }
    .card {
        padding: 10px;
        margin: 5px;
        border-radius: 8px;
        color: white;
        font-size: 13px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 8px;
    }
    .status-todo { background-color: #808080; }
    .status-inprogress { background-color: #f4b400; }
    .status-blocked { background-color: #db4437; }
    .status-done { background-color: #0f9d58; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------
# Helpers
# ------------------------
def fetch_issues(base_url, project_id, token, verify_ssl=True):
    url = f"{base_url}/api/v4/projects/{project_id}/issues?per_page=100"
    headers = {"PRIVATE-TOKEN": token}
    issues = []
    page = 1
    while True:
        resp = requests.get(f"{url}&page={page}", headers=headers, verify=verify_ssl)
        if resp.status_code != 200:
            st.error(f"Error fetching issues: {resp.text}")
            break
        data = resp.json()
        if not data:
            break
        issues.extend(data)
        page += 1
    return issues

def normalize_labels(labels):
    result = {}
    for lbl in labels:
        if "::" in lbl:
            parts = lbl.split("::", 1)
            key = parts[0].strip().lower()
            val = parts[1].strip()
            result[key] = val
    return result

def issues_to_df(issues):
    rows = []
    for i in issues:
        labels_dict = normalize_labels(i.get("labels", []))
        row = {
            "id": i["id"],
            "iid": i["iid"],
            "title": i["title"],
            "state": i["state"],
            "assignee": i["assignee"]["name"] if i.get("assignee") else None,
            "created_at": i["created_at"],
            "due_date": i.get("due_date"),
            "milestone": i["milestone"]["title"] if i.get("milestone") else None,
            "sprint": labels_dict.get("sprint"),
            "team": labels_dict.get("team"),
            "status": labels_dict.get("status"),
            "project": labels_dict.get("project"),
            "workstream": labels_dict.get("workstream"),
            "labels": ", ".join(i.get("labels", [])),
            "web_url": i["web_url"],
        }
        rows.append(row)
    return pd.DataFrame(rows)

def download_excel(df, filename="data.xlsx"):
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button("⬇️ Download Excel", data=buffer, file_name=filename,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def load_commentary():
    if os.path.exists("commentary.json"):
        with open("commentary.json", "r") as f:
            return json.load(f)
    return {}

def save_commentary(data):
    with open("commentary.json", "w") as f:
        json.dump(data, f, indent=2)

def update_issue(base_url, project_id, token, iid, body, verify_ssl=True):
    url = f"{base_url}/api/v4/projects/{project_id}/issues/{iid}"
    headers = {"PRIVATE-TOKEN": token}
    resp = requests.put(url, headers=headers, json=body, verify=verify_ssl)
    return resp

def status_class(status):
    if not status:
        return "status-todo"
    s = status.lower()
    if "progress" in s:
        return "status-inprogress"
    if "block" in s:
        return "status-blocked"
    if "done" in s or "closed" in s:
        return "status-done"
    return "status-todo"

# ------------------------
# Sidebar Inputs
# ------------------------
st.sidebar.header("🔑 GitLab Connection")
base_url = st.sidebar.text_input("GitLab Base URL", value="https://gitlab.com")
project_id = st.sidebar.text_input("Project ID")
access_token = st.sidebar.text_input("Access Token", type="password")
verify_ssl = st.sidebar.checkbox("Verify SSL Certificates", value=True)

# ------------------------
# Fetch & Filter Issues
# ------------------------
issues, df = [], pd.DataFrame()

if project_id and access_token:
    try:
        issues = fetch_issues(base_url, project_id, access_token, verify_ssl)
    except requests.exceptions.SSLError as e:
        st.error(f"SSL Error: {e}. You may need to disable SSL verification for self-signed certs.")
    if issues:
        df = issues_to_df(issues)
        # Sidebar Filters
        st.sidebar.header("📊 Filters")
        sprint_filter = st.sidebar.multiselect("Sprint", sorted(df["sprint"].dropna().unique()))
        team_filter = st.sidebar.multiselect("Team", sorted(df["team"].dropna().unique()))
        status_filter = st.sidebar.multiselect("Status", sorted(df["status"].dropna().unique()))

        filtered_df = df.copy()
        if sprint_filter:
            filtered_df = filtered_df[filtered_df["sprint"].isin(sprint_filter)]
        if team_filter:
            filtered_df = filtered_df[filtered_df["team"].isin(team_filter)]
        if status_filter:
            filtered_df = filtered_df[filtered_df["status"].isin(status_filter)]
    else:
        st.warning("No issues found or unable to fetch.")
        filtered_df = pd.DataFrame()
else:
    filtered_df = pd.DataFrame()
    st.info("Enter Project ID and Access Token in the sidebar to fetch issues.")

# ------------------------
# Tabs
# ------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "By Sprint–Team–Status", "Hygiene", "Commentary"])

# --- Overview ---
with tab1:
    st.subheader("📊 Overview")
    if not filtered_df.empty:
        counts = filtered_df.groupby("status").size().reset_index(name="count")
        st.dataframe(counts)
        download_excel(filtered_df, "overview.xlsx")

# --- Kanban Tab ---
with tab2:
    st.subheader("🗂️ Sprint → Team → Status (Kanban)")
    if not filtered_df.empty:
        sprints = filtered_df["sprint"].dropna().unique()
        for sprint in sprints:
            st.markdown(f"### Sprint: {sprint}")
            sprint_df = filtered_df[filtered_df["sprint"] == sprint]
            teams = sprint_df["team"].dropna().unique()
            for team in teams:
                st.markdown(f"**Team: {team}**")
                team_df = sprint_df[sprint_df["team"] == team]
                statuses = team_df["status"].dropna().unique()
                cols = st.columns(len(statuses))
                for idx, status in enumerate(statuses):
                    with cols[idx]:
                        st.markdown(f"**{status}**")
                        for _, row in team_df[team_df["status"] == status].iterrows():
                            css_class = status_class(row["status"])
                            st.markdown(
                                f"<div class='card {css_class}'><b>{row['title']}</b><br/>#{row['iid']}</div>",
                                unsafe_allow_html=True,
                            )
        download_excel(filtered_df, "by_sprint.xlsx")

# --- Hygiene Tab ---
with tab3:
    st.subheader("🧹 Hygiene Checks (Fixable)")
    if not filtered_df.empty:
        hygiene_checks = {
            "No Team": filtered_df[filtered_df["team"].isna()],
            "No Status": filtered_df[filtered_df["status"].isna()],
            "No Project": filtered_df[filtered_df["project"].isna()],
            "No Sprint": filtered_df[filtered_df["sprint"].isna()],
            "No Title": filtered_df[filtered_df["title"].isna()],
            "No Milestone": filtered_df[filtered_df["milestone"].isna()],
        }
        for check, subset in hygiene_checks.items():
            if not subset.empty:
                st.markdown(f"### {check} ({len(subset)})")
                for _, row in subset.iterrows():
                    with st.expander(f"#{row['iid']} {row['title']}", expanded=False):
                        current_labels = row["labels"].split(", ") if row["labels"] else []
                        new_labels = current_labels.copy()
                        body = {}

                        # Status
                        if "Status" in check:
                            status_val = st.selectbox("Set Status", ["To Do", "In Progress", "Blocked", "Done"],
                                                      key=f"status_{row['iid']}")
                            new_labels = [l for l in new_labels if not l.lower().startswith("status::")]
                            new_labels.append(f"Status::{status_val}")

                        # Team
                        if "Team" in check:
                            team_val = st.text_input("Set Team", key=f"team_{row['iid']}")
                            if team_val:
                                new_labels = [l for l in new_labels if not l.lower().startswith("team::")]
                                new_labels.append(f"Team::{team_val}")

                        # Project
                        if "Project" in check:
                            proj_val = st.text_input("Set Project", key=f"proj_{row['iid']}")
                            if proj_val:
                                new_labels = [l for l in new_labels if not l.lower().startswith("project::")]
                                new_labels.append(f"Project::{proj_val}")

                        # Sprint
                        if "Sprint" in check:
                            sprint_val = st.text_input("Set Sprint", key=f"sprint_{row['iid']}")
                            if sprint_val:
                                new_labels = [l for l in new_labels if not l.lower().startswith("sprint::")]
                                new_labels.append(f"Sprint::{sprint_val}")

                        # Title
                        if "Title" in check:
                            new_title = st.text_input("Set Title", value=row["title"], key=f"title_{row['iid']}")
                            if new_title and new_title != row["title"]:
                                body["title"] = new_title

                        if st.button("Apply Fix", key=f"fix_{row['iid']}"):
                            body["labels"] = new_labels
                            resp = update_issue(base_url, project_id, access_token, row["iid"], body, verify_ssl)
                            if resp.status_code == 200:
                                st.success(f"Issue #{row['iid']} updated successfully! ✅")
                                st.experimental_rerun()
                            else:
                                st.error(f"Failed: {resp.text}")
        download_excel(filtered_df, "hygiene.xlsx")

# --- Commentary Tab ---
with tab4:
    st.subheader("📝 Sprint Commentary")
    commentary_data = load_commentary()
    sprint_options = sorted(df["sprint"].dropna().unique()) if not df.empty else []
    selected_sprint = st.selectbox("Select Sprint", sprint_options)

    if selected_sprint:
        default_text = commentary_data.get(selected_sprint, "")
        text = st.text_area("Enter commentary", value=default_text, height=250)
        if st.button("💾 Save Commentary", key=f"save_commentary_{selected_sprint}"):
            commentary_data[selected_sprint] = text
            save_commentary(commentary_data)
            st.success("Commentary saved!")

        st.download_button(
            "⬇️ Download Commentary JSON",
            data=json.dumps(commentary_data, indent=2),
            file_name="commentary.json",
            mime="application/json",
        )

import streamlit as st
import pandas as pd
import requests
import json
import re
from io import BytesIO
from docx import Document
import os
from requests.exceptions import RequestException   # ✅ fixed import


# -------------------------
# Utility Functions
# -------------------------

def normalize_label(label: str):
    """
    Normalize a GitLab label into Key, Value.
    Handles inconsistent spacing, case, and numeric prefixes like 01-Status::.
    """
    if "::" not in label:
        return None, None

    key, val = label.split("::", 1)
    key = re.sub(r"^\d+[- ]*", "", key.strip())  # remove numeric prefixes
    val = val.strip()

    key = key.capitalize()  # e.g., Status, Team, Sprint
    return key, val


def fetch_issues(base_url, project_id, access_token):
    """
    Fetch all issues from a GitLab project using the API.
    """
    url = f"{base_url}/api/v4/projects/{project_id}/issues?per_page=100"
    headers = {"PRIVATE-TOKEN": access_token}

    all_issues = []
    page = 1

    while True:
        try:
            resp = requests.get(f"{url}&page={page}", headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except RequestException as e:
            st.error(f"Error fetching issues: {e}")
            break

        if not data:
            break

        all_issues.extend(data)
        page += 1

    return all_issues


def process_issues(issues):
    """
    Convert raw GitLab issues into a DataFrame with normalized fields.
    Handles multi-value fields (e.g., multiple Sprints).
    """
    rows = []
    for issue in issues:
        row = {
            "iid": issue.get("iid"),
            "title": issue.get("title"),
            "description": issue.get("description"),
            "web_url": issue.get("web_url"),
            "milestone": issue.get("milestone", {}).get("title") if issue.get("milestone") else None,
            "status": None,
            "team": None,
            "sprint": [],
            "project": None,
            "workstream": None
        }

        for label in issue.get("labels", []):
            key, val = normalize_label(label)
            if not key:
                continue
            if key == "Status":
                row["status"] = val
            elif key == "Team":
                row["team"] = val
            elif key == "Sprint":
                row["sprint"].append(val)   # ✅ allow multiple sprints
            elif key == "Project":
                row["project"] = val
            elif key == "Workstream":
                row["workstream"] = val
            elif key == "Milestone" and not row["milestone"]:
                row["milestone"] = val

        rows.append(row)

    df = pd.DataFrame(rows)

    # Expand sprint list into separate rows
    df = df.explode("sprint").reset_index(drop=True)
    return df


def export_docx(commentary):
    """
    Export commentary dictionary to a Word document.
    """
    doc = Document()
    doc.add_heading("Sprint Commentary", level=1)

    for section, text in commentary.items():
        doc.add_heading(section, level=2)
        doc.add_paragraph(text)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# -------------------------
# Streamlit App
# -------------------------

st.set_page_config(layout="wide", page_title="GitLab Issue Dashboard")

st.sidebar.header("🔑 GitLab Settings")
base_url = st.sidebar.text_input("Base URL", value="https://gitlab.com")
project_id = st.sidebar.text_input("Project ID")
access_token = st.sidebar.text_input("Access Token", type="password")

if base_url and project_id and access_token:
    issues = fetch_issues(base_url, project_id, access_token)
    if issues:
        df = process_issues(issues)

        # Sidebar filters
        st.sidebar.header("📊 Filters")
        selected_sprint = st.sidebar.multiselect("Filter by Sprint", sorted(df["sprint"].dropna().unique()))
        selected_team = st.sidebar.multiselect("Filter by Team", sorted(df["team"].dropna().unique()))
        selected_status = st.sidebar.multiselect("Filter by Status", sorted(df["status"].dropna().unique()))
        selected_project = st.sidebar.multiselect("Filter by Project", sorted(df["project"].dropna().unique()))
        selected_milestone = st.sidebar.multiselect("Filter by Milestone", sorted(df["milestone"].dropna().unique()))

        # Apply filters
        fdf = df.copy()
        if selected_sprint:
            fdf = fdf[fdf["sprint"].isin(selected_sprint)]
        if selected_team:
            fdf = fdf[fdf["team"].isin(selected_team)]
        if selected_status:
            fdf = fdf[fdf["status"].isin(selected_status)]
        if selected_project:
            fdf = fdf[fdf["project"].isin(selected_project)]
        if selected_milestone:
            fdf = fdf[fdf["milestone"].isin(selected_milestone)]

        # Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["Overview", "Kanban (By Sprint/Team/Status)", "Hygiene", "Commentary", "Edit Issues"]
        )

        # -------------------------
        # Tab 1: Overview
        # -------------------------
        with tab1:
            st.subheader("📊 Overview Dashboard")

            metrics = {
                "Total Issues": len(fdf),
                "By Status": fdf["status"].value_counts().to_dict(),
                "By Team": fdf["team"].value_counts().to_dict(),
                "By Sprint": fdf["sprint"].value_counts().to_dict(),
            }

            # Render clickable metrics
            cols = st.columns(len(metrics["By Status"]))
            for i, (status, count) in enumerate(sorted(metrics["By Status"].items())):
                if cols[i].button(f"{status}: {count}", key=f"status_{status}"):
                    st.session_state["status_filter"] = status

            st.dataframe(fdf[["iid", "title", "description", "status", "team", "sprint", "project", "web_url"]])

        # -------------------------
        # Tab 2: Kanban
        # -------------------------
        with tab2:
            st.subheader("🗂 Kanban Board")

            swimlanes = fdf.groupby("status")

            left, right = st.columns([3, 2])
            with left:
                for status, group in swimlanes:
                    st.markdown(f"### {status}")
                    for _, row in group.sort_values("team").iterrows():
                        if st.button(f"{row['title']} ({row['team']})", key=f"card_{row['iid']}"):
                            st.session_state["selected_issue"] = row.to_dict()

            with right:
                if "selected_issue" in st.session_state:
                    issue = st.session_state["selected_issue"]
                    st.markdown("### 📝 Issue Details")
                    st.write(f"**Title:** {issue['title']}")
                    st.write(f"**Description:** {issue['description']}")
                    st.write(f"**Team:** {issue['team']}")
                    st.write(f"**Status:** {issue['status']}")
                    st.write(f"**Sprint:** {issue['sprint']}")
                    st.write(f"[🔗 View in GitLab]({issue['web_url']})")

        # -------------------------
        # Tab 3: Hygiene
        # -------------------------
        with tab3:
            st.subheader("🧹 Hygiene Checks")

            missing_team = fdf[fdf["team"].isna()]
            missing_status = fdf[fdf["status"].isna()]
            missing_sprint = fdf[fdf["sprint"].isna()]

            cols = st.columns(3)
            if cols[0].button(f"No Team: {len(missing_team)}"):
                st.dataframe(missing_team)
            if cols[1].button(f"No Status: {len(missing_status)}"):
                st.dataframe(missing_status)
            if cols[2].button(f"No Sprint: {len(missing_sprint)}"):
                st.dataframe(missing_sprint)

        # -------------------------
        # Tab 4: Commentary
        # -------------------------
        with tab4:
            st.subheader("🗒 Sprint Commentary")

            sections = ["Scope", "Key Dates", "Achievements", "Next Steps", "Challenges"]
            commentary = {}
            for sec in sections:
                commentary[sec] = st.text_area(sec, "")

            if st.button("💾 Save Commentary"):
                buffer = export_docx(commentary)
                st.download_button(
                    "Download Commentary (Word)",
                    data=buffer,
                    file_name="commentary.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

        # -------------------------
        # Tab 5: Edit Issues
        # -------------------------
        with tab5:
            st.subheader("✏️ Edit Issues")

            issue_id = st.selectbox("Select Issue", fdf["iid"].unique())
            issue_row = fdf[fdf["iid"] == issue_id].iloc[0]

            new_title = st.text_input("Title", issue_row["title"])
            new_desc = st.text_area("Description", issue_row["description"])
            new_status = st.selectbox("Status", sorted(df["status"].dropna().unique()), index=0)
            new_team = st.selectbox("Team", sorted(df["team"].dropna().unique()), index=0)

            if st.button("Update Issue"):
                st.success("Issue updated in GitLab (simulated).")

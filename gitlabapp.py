import streamlit as st
import requests
import pandas as pd
import json
import re
from io import BytesIO

# ----------------------------
# Helper Functions
# ----------------------------
def fetch_issues(base_url, project_id, token):
    url = f"{base_url}/api/v4/projects/{project_id}/issues?per_page=100"
    headers = {"PRIVATE-TOKEN": token}
    try:
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Failed to fetch issues: {e}")
        return []

def normalize_label(label):
    clean = re.sub(r"^\d+\s*", "", label).strip()
    if "::" in clean:
        key, val = clean.split("::", 1)
    elif ":" in clean:
        key, val = clean.split(":", 1)
    else:
        return None, clean.strip()
    return key.strip().title(), val.strip()

def parse_labels(issue):
    parsed = {}
    for raw in issue.get("labels", []):
        key, val = normalize_label(raw)
        if key:
            parsed.setdefault(key, []).append(val)
    return parsed

def to_dataframe(issues):
    rows = []
    for issue in issues:
        labels = parse_labels(issue)
        rows.append({
            "ID": issue.get("iid"),
            "Title": issue.get("title", "Untitled"),
            "Description": issue.get("description", ""),
            "Milestone": issue.get("milestone", {}).get("title", "None"),
            "Team": ", ".join(labels.get("Team", [])) or None,
            "Status": ", ".join(labels.get("Status", [])) or None,
            "Sprint": ", ".join(labels.get("Sprint", [])) or None,
            "Project": ", ".join(labels.get("Project", [])) or None,
            "Workstream": ", ".join(labels.get("Workstream", [])) or None,
            "Other Labels": ", ".join(
                v for k, vlist in labels.items()
                for v in vlist if k not in ["Team","Status","Sprint","Project","Workstream"]
            )
        })
    return pd.DataFrame(rows)

def download_excel(df, filename="issues.xlsx"):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    return buffer

def update_issue(base_url, project_id, token, issue_id, payload):
    url = f"{base_url}/api/v4/projects/{project_id}/issues/{issue_id}"
    headers = {"PRIVATE-TOKEN": token}
    try:
        resp = requests.put(url, headers=headers, data=payload, verify=False)
        if resp.status_code == 200:
            st.success(f"Issue {issue_id} updated successfully")
        else:
            st.error(f"Failed to update issue {issue_id}: {resp.text}")
    except Exception as e:
        st.error(f"Error updating issue: {e}")

def status_color(status):
    if not status:
        return "#d3d3d3"  # light gray
    status = status.lower()
    if "done" in status or "closed" in status:
        return "#90ee90"  # light green
    elif "progress" in status or "doing" in status:
        return "#ffa500"  # orange
    elif "block" in status:
        return "#ff6961"  # red
    else:
        return "#87ceeb"  # light blue default

def colored_badge(text, color):
    return f"<span style='background-color:{color}; color:black; padding:4px 8px; border-radius:8px;'>{text}</span>"

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="GitLab Issue Manager", layout="wide")

st.sidebar.header("🔑 GitLab Connection")
base_url = st.sidebar.text_input("Base URL (e.g. https://gitlab.com)", "https://gitlab.com")
project_id = st.sidebar.text_input("Project ID")
token = st.sidebar.text_input("Access Token", type="password")

if project_id and token:
    issues = fetch_issues(base_url, project_id, token)
    if issues:
        df = to_dataframe(issues)

        # Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["📊 Overview", "🗂️ Kanban", "🧹 Hygiene", "📝 Commentary", "✏️ Edit"]
        )

        # ----------------------------
        # Overview Tab
        # ----------------------------
        with tab1:
            st.subheader("Overview Summary")
            if not df.empty:
                col1, col2, col3, col4 = st.columns(4)
                for col, field in zip([col1, col2, col3, col4], ["Status", "Team", "Sprint", "Project"]):
                    with col:
                        unique_vals = df[field].dropna().unique()
                        count = len(unique_vals)
                        st.metric(field, count)
                        if field == "Status":
                            for val in unique_vals:
                                c = status_color(val)
                                st.markdown(colored_badge(val, c), unsafe_allow_html=True)

                st.dataframe(df)
                excel_data = download_excel(df)
                st.download_button("⬇️ Download Excel", data=excel_data, file_name="issues.xlsx")
            else:
                st.info("No issues available")

        # ----------------------------
        # Kanban Tab
        # ----------------------------
        with tab2:
            st.subheader("Kanban View (by Sprint → Team → Status)")
            sprint_filter = st.selectbox("Filter by Sprint", ["All"] + sorted(df["Sprint"].dropna().unique().tolist()))
            filtered = df if sprint_filter == "All" else df[df["Sprint"] == sprint_filter]

            if not filtered.empty:
                for team in sorted(filtered["Team"].dropna().unique()):
                    st.markdown(f"### 👥 Team: {team}")
                    team_df = filtered[filtered["Team"] == team]
                    statuses = team_df["Status"].dropna().unique()
                    cols = st.columns(len(statuses))
                    for c, status in zip(cols, statuses):
                        with c:
                            color = status_color(status)
                            st.markdown(f"<h4 style='background-color:{color}; padding:6px; border-radius:6px;'>{status}</h4>", unsafe_allow_html=True)
                            for _, row in team_df[team_df["Status"] == status].iterrows():
                                st.markdown(
                                    f"- [{row['Title']}]({base_url}/{project_id}/-/issues/{row['ID']})"
                                )
            else:
                st.info("No issues for selected sprint")

        # ----------------------------
        # Hygiene Tab
        # ----------------------------
        with tab3:
            st.subheader("Hygiene Check")
            hygiene_fields = ["Team", "Status", "Sprint", "Project", "Title", "Milestone"]
            for field in hygiene_fields:
                missing = df[df[field].isna() | (df[field] == "")]
                if not missing.empty:
                    st.markdown(f"**⚠️ Missing {field}: {len(missing)} issues**")
                    for _, row in missing.iterrows():
                        with st.expander(f"Issue {row['ID']}: {row['Title']}"):
                            new_val = st.text_input(f"Set {field}", key=f"fix_{field}_{row['ID']}")
                            if st.button(f"Update {field}", key=f"btn_{field}_{row['ID']}"):
                                payload = {field.lower(): new_val} if field in ["title","description"] else {"labels": f"{field}::{new_val}"}
                                update_issue(base_url, project_id, token, row["ID"], payload)
                else:
                    st.success(f"All issues have {field}")

        # ----------------------------
        # Commentary Tab
        # ----------------------------
        with tab4:
            st.subheader("Sprint Commentary")
            sprint_options = ["General"] + sorted(df["Sprint"].dropna().unique().tolist())
            sprint_choice = st.selectbox("Select Sprint", sprint_options)
            commentary = st.text_area("Write commentary here...")
            if st.button("💾 Save Commentary"):
                entry = {"sprint": sprint_choice, "commentary": commentary}
                try:
                    with open("commentary.json", "a") as f:
                        f.write(json.dumps(entry) + "\n")
                    st.success("Commentary saved")
                except Exception as e:
                    st.error(f"Failed to save commentary: {e}")
            try:
                with open("commentary.json", "r") as f:
                    lines = f.readlines()
                    if lines:
                        st.json([json.loads(l) for l in lines])
            except FileNotFoundError:
                st.info("No commentary saved yet.")

        # ----------------------------
        # Edit Tab
        # ----------------------------
        with tab5:
            st.subheader("Edit Issues")
            issue_id = st.selectbox("Select Issue", df["ID"].tolist())
            issue = df[df["ID"] == issue_id].iloc[0]
            new_title = st.text_input("Title", issue["Title"])
            new_desc = st.text_area("Description", issue["Description"])
            new_team = st.text_input("Team", issue["Team"] or "")
            new_status = st.text_input("Status", issue["Status"] or "")
            new_sprint = st.text_input("Sprint", issue["Sprint"] or "")
            new_project = st.text_input("Project", issue["Project"] or "")
            new_workstream = st.text_input("Workstream", issue["Workstream"] or "")
            new_milestone = st.text_input("Milestone", issue["Milestone"] or "")

            if st.button("Update Issue"):
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
                    "labels": ",".join(labels)
                }
                update_issue(base_url, project_id, token, issue_id, payload)

else:
    st.info("Enter GitLab connection details to start.")

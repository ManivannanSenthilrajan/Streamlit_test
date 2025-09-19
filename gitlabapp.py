import streamlit as st
import pandas as pd
import requests
import json
import os
from io import BytesIO

# ------------------------
# Page Config
# ------------------------
st.set_page_config(page_title="GitLab Issues Dashboard", layout="wide")

# ------------------------
# CSS Styling
# ------------------------
st.markdown("""
<style>
body, div, p, span, input, textarea, select, button {
    font-family: "Frutiger45Light", "Segoe UI", Arial, sans-serif !important;
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
.kanban-board { display: flex; overflow-x: auto; padding-bottom: 20px; }
.kanban-col {
    flex: 0 0 250px;
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 10px;
    margin-right: 10px;
    background-color: #f9f9f9;
}
.kanban-col h4 { text-align: center; }
</style>
""", unsafe_allow_html=True)

# ------------------------
# Helper Functions
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
    """
    Convert GitLab labels to a dict {key: value}, normalizing spaces and cases.
    Handles labels like:
        'Team::A', 'Team :: B', 'Status :: Done', 'Sprint::Q1::Phase1'
    """
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
            "title": i.get("title", ""),
            "state": i.get("state", ""),
            "team": labels_dict.get("team"),
            "status": labels_dict.get("status"),
            "sprint": labels_dict.get("sprint"),
            "project": labels_dict.get("project"),
            "workstream": labels_dict.get("workstream"),
            "milestone": i["milestone"]["title"] if i.get("milestone") else None,
            "labels": i.get("labels", []),
            "web_url": i.get("web_url"),
        }
        rows.append(row)
    df = pd.DataFrame(rows)
    for col in ["team","status","sprint","project","workstream","milestone"]:
        if col not in df.columns:
            df[col] = None
        df[col] = df[col].replace({None: None, "": None})
    return df

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
    if not status or status.lower() in ["none", "nan"]:
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
    else:
        st.warning("No issues found or unable to fetch.")
else:
    st.info("Enter Project ID and Access Token in the sidebar to fetch issues.")

# ------------------------
# Sidebar Filters
# ------------------------
if not df.empty:
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
    filtered_df = pd.DataFrame()

# ------------------------
# Tabs
# ------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "By Sprint–Team–Status", "Hygiene", "Commentary"])

# --- Overview Tab ---
with tab1:
    st.subheader("📊 Overview")
    if not filtered_df.empty:
        counts = filtered_df.groupby("status").size().reset_index(name="count")
        st.dataframe(counts)
        download_excel(filtered_df, "overview.xlsx")
    else:
        st.info("No issues to display in Overview.")

# --- Kanban Tab ---
with tab2:
    st.subheader("🗂️ Sprint → Team → Status (Kanban)")
    if not filtered_df.empty:
        sprints = filtered_df["sprint"].fillna("No Sprint").unique()
        for sprint in sprints:
            st.markdown(f"### Sprint: {sprint}")
            sprint_df = filtered_df[filtered_df["sprint"].fillna("No Sprint") == sprint]
            teams = sprint_df["team"].fillna("No Team").unique()
            for team in teams:
                st.markdown(f"**Team: {team}**")
                team_df = sprint_df[sprint_df["team"].fillna("No Team") == team]
                statuses = team_df["status"].fillna("No Status").unique()
                st.markdown('<div class="kanban-board">', unsafe_allow_html=True)
                for status in statuses:
                    col_df = team_df[team_df["status"].fillna("No Status") == status]
                    st.markdown(f'<div class="kanban-col"><h4>{status}</h4>', unsafe_allow_html=True)
                    for _, row in col_df.iterrows():
                        css_class = status_class(row["status"])
                        st.markdown(
                            f"<div class='card {css_class}'><b>{row['title']}</b><br/>#{row['iid']}</div>",
                            unsafe_allow_html=True
                        )
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        download_excel(filtered_df, "by_sprint.xlsx")
    else:
        st.info("No issues to display in Kanban.")

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
                for idx, row in subset.iterrows():
                    with st.expander(f"Issue #{row['iid']}: {row['title']}", expanded=False):
                        key_base = f"{check}_{row['iid']}_{idx}"
                        current_labels = row["labels"]
                        new_labels = current_labels.copy()
                        body = {}
                        if "Status" in check:
                            status_val = st.selectbox("Set Status",
                                                      ["To Do","In Progress","Blocked","Done"],
                                                      key=f"status_{key_base}")
                            apply_fix = st.button("Apply Fix", key=f"apply_{key_base}")
                            if apply_fix:
                                new_labels = [l for l in new_labels if not l.lower().startswith("status::")]
                                new_labels.append(f"Status::{status_val}")
                                body["labels"] = new_labels
                                resp = update_issue(base_url, project_id, access_token, row["iid"], body, verify_ssl)
                                if resp.status_code == 200:
                                    st.success(f"Issue #{row['iid']} updated successfully!")
                                    st.experimental_rerun()
                                else:
                                    st.error(f"Failed: {resp.text}")
        download_excel(filtered_df, "hygiene.xlsx")
    else:
        st.info("No issues to display in Hygiene.")

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

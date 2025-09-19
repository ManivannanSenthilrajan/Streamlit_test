import streamlit as st
import pandas as pd
import requests
import json
import os
import re
from io import BytesIO

# ---------------- Page Config ----------------
st.set_page_config(page_title="GitLab Dashboard", layout="wide")

# ---------------- CSS Styling ----------------
st.markdown("""
<style>
body, div, p, span, input, textarea, select, button {
    font-family: "Frutiger45Light", "Segoe UI", Arial, sans-serif !important;
}
.card {
    padding: 10px; margin:5px; border-radius:8px; color:white; font-size:13px;
    box-shadow: 0px 2px 5px rgba(0,0,0,0.1); margin-bottom:8px;
}
.status-todo { background-color:#808080; }
.status-inprogress { background-color:#f4b400; }
.status-blocked { background-color:#db4437; }
.status-done { background-color:#0f9d58; }
.kanban-board { display:flex; overflow-x:auto; padding-bottom:20px; }
.kanban-col { flex:0 0 250px; border:1px solid #ddd; border-radius:5px; padding:10px; margin-right:10px; background-color:#f9f9f9; }
.kanban-col h4 { text-align:center; }
</style>
""", unsafe_allow_html=True)

# ---------------- Helper Functions ----------------
KEY_MAP = {
    "team":"team",
    "status":"status",
    "sprint":"sprint",
    "project":"project",
    "milestone":"milestone",
    "workstream":"workstream"
}

def normalize_key(key):
    key = re.sub(r'^\d+\s*','', key).strip().lower().replace(" ","")
    return key

def parse_labels_merge(labels):
    result = {}
    for lbl in labels:
        if "::" in lbl:
            k,v = lbl.split("::",1)
            key_norm = normalize_key(k)
            std_key = None
            for kmap in KEY_MAP:
                if key_norm.startswith(kmap):
                    std_key = KEY_MAP[kmap]
                    break
            if std_key:
                if std_key in result:
                    result[std_key] += ", "+v.strip()
                else:
                    result[std_key] = v.strip()
    return result

def fetch_issues(base_url, project_id, token, verify_ssl=True):
    url = f"{base_url}/api/v4/projects/{project_id}/issues?per_page=100"
    headers = {"PRIVATE-TOKEN": token}
    issues=[]
    page=1
    while True:
        resp = requests.get(f"{url}&page={page}", headers=headers, verify=verify_ssl)
        if resp.status_code != 200:
            st.error(f"Error fetching issues: {resp.text}")
            break
        data = resp.json()
        if not data: break
        issues.extend(data)
        page += 1
    return issues

def issues_to_df(issues):
    rows=[]
    all_keys=set()
    for i in issues:
        labels_dict=parse_labels_merge(i.get("labels",[]))
        all_keys.update(labels_dict.keys())
        row={
            "iid":i["iid"],
            "title":i.get("title",""),
            "description":i.get("description",""),
            "labels":i.get("labels",[]),
            "web_url":i.get("web_url")
        }
        row.update(labels_dict)
        rows.append(row)
    df=pd.DataFrame(rows)
    for k in all_keys:
        if k not in df.columns:
            df[k] = ""
    return df

def status_class(status):
    if not status: return "status-todo"
    s=status.lower()
    if "progress" in s: return "status-inprogress"
    if "block" in s: return "status-blocked"
    if "done" in s or "closed" in s: return "status-done"
    return "status-todo"

def download_excel(df, filename="data.xlsx"):
    buffer=BytesIO()
    df.to_excel(buffer,index=False)
    buffer.seek(0)
    st.download_button("⬇️ Download Excel", data=buffer, file_name=filename,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def load_commentary():
    if os.path.exists("commentary.json"):
        with open("commentary.json","r") as f: return json.load(f)
    return {}

def save_commentary(data):
    with open("commentary.json","w") as f: json.dump(data,f,indent=2)

def update_issue(base_url, project_id, token, iid, body, verify_ssl=True):
    url = f"{base_url}/api/v4/projects/{project_id}/issues/{iid}"
    headers={"PRIVATE-TOKEN":token}
    resp=requests.put(url, headers=headers, json=body, verify=verify_ssl)
    return resp

# ---------------- Sidebar ----------------
st.sidebar.header("🔑 GitLab Connection")
base_url = st.sidebar.text_input("GitLab Base URL", value="https://gitlab.com")
project_id = st.sidebar.text_input("Project ID")
access_token = st.sidebar.text_input("Access Token", type="password")
verify_ssl = st.sidebar.checkbox("Verify SSL Certificates", value=True)

# ---------------- Fetch Issues ----------------
df=pd.DataFrame()
if project_id and access_token:
    issues=fetch_issues(base_url, project_id, access_token, verify_ssl)
    if issues:
        df=issues_to_df(issues)
    else:
        st.warning("No issues found or unable to fetch.")
else:
    st.info("Enter Project ID and Access Token to fetch issues.")

# ---------------- Filters ----------------
if not df.empty:
    st.sidebar.header("📊 Filters")
    filter_cols = [c for c in df.columns if c not in ["iid","title","description","labels","web_url"]]
    filters={}
    for col in filter_cols:
        vals=sorted(df[col].dropna().unique())
        filters[col]=st.sidebar.multiselect(col.capitalize(), vals)
    filtered_df=df.copy()
    for col,vals in filters.items():
        if vals:
            filtered_df=filtered_df[filtered_df[col].isin(vals)]
else:
    filtered_df=pd.DataFrame()

# ---------------- Tabs ----------------
tab1,tab2,tab3,tab4,tab5 = st.tabs(["Overview","Kanban","Hygiene","Commentary","Edit Issue"])

# -------- Overview --------
with tab1:
    st.subheader("📊 Overview")
    if not filtered_df.empty:
        count_cols=[c for c in filtered_df.columns if c not in ["iid","title","description","labels","web_url"]]
        for col in count_cols:
            st.markdown(f"### {col.capitalize()} Counts")
            st.dataframe(filtered_df.groupby(col).size().reset_index(name="count"))
        download_excel(filtered_df,"overview.xlsx")
    else:
        st.info("No issues to display.")

# -------- Kanban --------
with tab2:
    st.subheader("🗂️ Kanban (Sprint → Team → Status)")
    if not filtered_df.empty:
        if "sprint" not in filtered_df.columns:
            st.info("No sprint data found.")
        else:
            sprints = filtered_df["sprint"].replace("", "No Sprint").unique()
            for sprint in sprints:
                st.markdown(f"### Sprint: {sprint}")
                sprint_df = filtered_df[filtered_df["sprint"].replace("", "No Sprint")==sprint]
                teams = sprint_df["team"].replace("", "No Team").unique()
                st.markdown('<div class="kanban-board">', unsafe_allow_html=True)
                for team in teams:
                    st.markdown(f'<div class="kanban-col"><h4>Team: {team}</h4>', unsafe_allow_html=True)
                    team_df=sprint_df[sprint_df["team"].replace("", "No Team")==team]
                    statuses=team_df["status"].replace("", "No Status").unique()
                    for status in statuses:
                        col_df=team_df[team_df["status"].replace("", "No Status")==status]
                        st.markdown(f'<h5>{status}</h5>', unsafe_allow_html=True)
                        for idx,row in col_df.iterrows():
                            css_class=status_class(row.get("status"))
                            st.markdown(f"<div class='card {css_class}'><b>{row['title']}</b><br/>#{row['iid']}</div>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No issues to display.")

# -------- Hygiene --------
with tab3:
    st.subheader("🧹 Hygiene Checks")
    if not filtered_df.empty:
        required_keys = ["team","status","sprint","project","milestone","workstream","title"]
        missing_df=pd.DataFrame()
        for key in required_keys:
            if key in filtered_df.columns:
                temp=filtered_df[filtered_df[key]==""][["iid","title",key]]
                temp["field"]=key
                temp.rename(columns={key:"current_value"}, inplace=True)
                missing_df=pd.concat([missing_df,temp], ignore_index=True)
        if not missing_df.empty:
            for idx,row in missing_df.iterrows():
                col1,col2,col3,col4=st.columns([1,3,2,2])
                with col1: st.write(f"#{row['iid']}")
                with col2: st.write(row["title"])
                with col3:
                    new_val=st.text_input(f"{row['field']}", value=row["current_value"], key=f"hyg_{row['iid']}_{row['field']}")
                with col4:
                    if st.button("💾 Apply", key=f"btn_{row['iid']}_{row['field']}"):
                        issue_row=filtered_df[filtered_df["iid"]==row["iid"]].iloc[0]
                        new_labels=[l for l in issue_row["labels"] if normalize_key(l.split("::")[0])!=row["field"]]
                        if new_val: new_labels.append(f"{row['field'].capitalize()}::{new_val}")
                        body={"labels":new_labels}
                        resp=update_issue(base_url, project_id, access_token, row["iid"], body, verify_ssl)
                        if resp.status_code==200:
                            st.success(f"Issue #{row['iid']} updated!")
                            st.experimental_rerun()
                        else:
                            st.error(f"Failed: {resp.text}")
        else:
            st.info("No hygiene issues found.")
    else:
        st.info("No issues to display.")

# -------- Commentary --------
with tab4:
    st.subheader("💬 Commentary")
    commentary=load_commentary()
    sprints=df["sprint"].replace("", None).dropna().unique() if not df.empty and "sprint" in df.columns else []
    selected_sprint=st.selectbox("Select Sprint", sprints)
    if selected_sprint:
        cmt=commentary.get(selected_sprint,{})
        scope=st.text_area("Sprint Scope", value=cmt.get("scope",""))
        capacity=st.text_input("Capacity", value=cmt.get("capacity",""))
        key_dates=st.text_area("Key Dates", value=cmt.get("key_dates",""))
        review=st.text_area("Sprint Review", value=cmt.get("review",""))
        carry_over=st.text_area("Carry Over Issues", value=cmt.get("carry_over",""))
        next_steps=st.text_area("Next Steps", value=cmt.get("next_steps",""))
        achievements=st.text_area("Achievements", value=cmt.get("achievements",""))
        risks=st.text_area("Risks/Challenges", value=cmt.get("risks",""))
        if st.button("💾 Save Commentary"):
            commentary[selected_sprint]={
                "scope":scope,"capacity":capacity,"key_dates":key_dates,"review":review,
                "carry_over":carry_over,"next_steps":next_steps,"achievements":achievements,"risks":risks
            }
            save_commentary(commentary)
            st.success("Saved successfully!")
        st.download_button("⬇️ Download Commentary JSON", data=json.dumps(commentary, indent=2),
                           file_name="commentary.json", mime="application/json")
    else:
        st.info("No sprint selected.")

# -------- Edit Issue --------
with tab5:
    st.subheader("✏️ Edit Issue")
    if not filtered_df.empty:
        issue_map={f"#{row['iid']} - {row['title']}": row["iid"] for idx,row in filtered_df.iterrows()}
        selected_issue=st.selectbox("Select Issue", list(issue_map.keys()))
        if selected_issue:
            iid=issue_map[selected_issue]
            row=filtered_df[filtered_df["iid"]==iid].iloc[0]
            new_title=st.text_input("Title", value=row["title"])
            new_desc=st.text_area("Description", value=row.get("description",""))
            label_cols=[c for c in filtered_df.columns if c not in ["iid","title","description","labels","web_url"]]
            new_labels=[]
            for col in label_cols:
                val=st.text_input(f"{col.capitalize()}", value=row.get(col,""))
                if val:
                    new_labels.append(f"{col.capitalize()}::{val}")
            if st.button("💾 Apply Changes", key=f"edit_{iid}"):
                body={"title":new_title,"description":new_desc,"labels":new_labels}
                resp=update_issue(base_url, project_id, access_token, iid, body, verify_ssl)
                if resp.status_code==200:
                    st.success(f"Issue #{iid} updated!")
                    st.experimental_rerun()
                else:
                    st.error(f"Failed: {resp.text}")
    else:
        st.info("No issues to edit.")

import requests
import pandas as pd
import io
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from utils.label_parser import parse_labels

urllib3.disable_warnings(InsecureRequestWarning)

BASE_URL = "https://gitlab.com/api/v4"

def get_issues(project_ids, token):
    """Fetch issues from multiple GitLab projects with SSL verify disabled."""
    all_issues = []
    headers = {"PRIVATE-TOKEN": token}
    for project_id in project_ids:
        page = 1
        while True:
            url = f"{BASE_URL}/projects/{project_id}/issues"
            params = {"per_page": 100, "page": page}
            resp = requests.get(url, headers=headers, params=params, verify=False)
            if resp.status_code != 200:
                all_issues.append({"error": f"Failed to fetch issues for {project_id}: {resp.text}"})
                break
            issues = resp.json()
            if not issues:
                break
            all_issues.extend(issues)
            page += 1
    return all_issues


def build_dataframe(issues):
    """Convert raw GitLab issues to DataFrame with parsed labels."""
    rows = []
    for issue in issues:
        if "error" in issue:
            continue
        labels_parsed = parse_labels(issue.get("labels", []))
        rows.append({
            "id": issue["iid"],
            "project_id": issue["project_id"],
            "title": issue["title"],
            "description": issue["description"],
            "web_url": issue["web_url"],
            "team": labels_parsed["team"],
            "sprint": labels_parsed["sprint"],
            "status": labels_parsed["status"],
            "milestone": labels_parsed["milestone_label"],
            "project": labels_parsed["project_label"],
            "workstream": labels_parsed["workstream"]
        })
    return pd.DataFrame(rows)


def update_issue(project_id, issue_id, token, payload):
    """Update a GitLab issue using PUT API."""
    headers = {"PRIVATE-TOKEN": token, "Content-Type": "application/json"}
    url = f"{BASE_URL}/projects/{project_id}/issues/{issue_id}"
    resp = requests.put(url, headers=headers, json=payload, verify=False)
    return resp


def download_excel(df):
    """Generate Excel bytes for download."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Issues")
    return output.getvalue()

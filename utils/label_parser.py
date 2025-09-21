import re

def parse_labels(issue_labels):
    """Parse GitLab labels into key-value fields."""
    parsed = {
        "team": "",
        "sprint": "",
        "status": "",
        "milestone_label": "",
        "project_label": "",
        "workstream": ""
    }
    for label in issue_labels:
        match = re.match(r"(.+?)::(.*)", label, flags=re.IGNORECASE)
        if match:
            key, value = match.groups()
            key = key.strip().lower()
            value = value.strip()
            if "team" in key:
                parsed["team"] = value
            elif "sprint" in key:
                parsed["sprint"] = value
            elif "status" in key:
                parsed["status"] = value
            elif "milestone" in key:
                parsed["milestone_label"] = value
            elif "project" in key:
                parsed["project_label"] = value
            elif "workstream" in key:
                parsed["workstream"] = value
    return parsed

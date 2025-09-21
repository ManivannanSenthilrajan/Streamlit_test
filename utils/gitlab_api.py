import requests
import pandas as pd

def safe_join(x):
    """
    Safely convert list/dict/other to string for Streamlit buttons or display.
    """
    if isinstance(x, list):
        return ", ".join([str(e) for e in x])
    elif isinstance(x, dict):
        return ", ".join([f"{k}:{v}" for k, v in x.items()])
    elif pd.isna(x):
        return ""
    else:
        return str(x)


def get_issues(project_ids, token, ssl_verify=False):
    """
    Fetch issues from multiple GitLab projects and return a clean DataFrame.
    """
    all_issues = []
    headers = {"PRIVATE-TOKEN": token}

    for project_id in project_ids:
        page = 1
        while True:
            url = f"https://gitlab.com/api/v4/projects/{project_id}/issues"
            params = {"per_page": 100, "page": page}
            resp = requests.get(url, headers=headers, params=params, verify=ssl_verify)
            resp.raise_for_status()
            issues = resp.json()
            if not issues:
                break
            all_issues.extend(issues)
            page += 1

    if not all_issues:
        return pd.DataFrame()  # always return a DataFrame

    df = pd.json_normalize(all_issues)

    df = df.rename(columns={
        "id": "id",
        "title": "title",
        "description": "description",
        "web_url": "web_url",
        "labels": "labels"
    })

    df = parse_labels(df)
    df = df.drop_duplicates(subset=["id"])
    return df


def parse_labels(df):
    """
    Parse GitLab issue labels into separate columns.
    Handles multi-value labels, case-insensitive, fills missing values.
    """
    if "labels" not in df.columns:
        return df

    all_keys = set()
    for label_list in df["labels"]:
        if not label_list:
            continue
        for label in label_list:
            if "::" in label:
                key = label.split("::")[0].strip().lower()
                all_keys.add(key)

    for key in all_keys:
        df[key] = ""

    for idx, label_list in enumerate(df["labels"]):
        if not label_list:
            continue
        label_dict = {}
        for label in label_list:
            if "::" in label:
                parts = label.split("::")
                key = parts[0].strip().lower()
                value = safe_join(parts[1]) if len(parts) > 1 else ""
                if key in label_dict:
                    label_dict[key] += f", {value}"
                else:
                    label_dict[key] = value
        for key in all_keys:
            df.at[idx, key] = safe_join(label_dict.get(key, ""))

    for col in all_keys:
        df[col] = df[col].apply(safe_join)

    df.rename(columns=lambda x: x.replace(" ", "_").lower(), inplace=True)
    return df

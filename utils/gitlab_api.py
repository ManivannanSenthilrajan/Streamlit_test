import requests
import pandas as pd

def get_issues(project_ids, token, ssl_verify=False):
    """
    Fetch issues from multiple GitLab projects and return a clean DataFrame.

    Args:
        project_ids (list of str): GitLab project IDs
        token (str): Personal Access Token
        ssl_verify (bool): Whether to verify SSL certificates

    Returns:
        pd.DataFrame: Issues with parsed labels, deduplicated
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

    # Convert list of issues to DataFrame
    df = pd.json_normalize(all_issues)

    # Keep only required columns
    df = df.rename(columns={
        "id": "id",
        "title": "title",
        "description": "description",
        "web_url": "web_url",
        "labels": "labels"
    })

    # Parse labels dynamically
    df = parse_labels(df)

    # Deduplicate issues by ID (avoid multiple appearances in Kanban)
    df = df.drop_duplicates(subset=["id"])

    return df


def parse_labels(df):
    """
    Parse GitLab issue labels into separate columns.
    Handles key::value pattern, multiple values per key, case-insensitive.
    Fills missing values with None.

    Returns:
        pd.DataFrame: DataFrame with dynamic label columns
    """
    if "labels" not in df.columns:
        return df

    # Collect all unique keys
    all_keys = set()
    for label_list in df["labels"]:
        if not label_list:
            continue
        for label in label_list:
            if "::" in label:
                key = label.split("::")[0].strip().lower()
                all_keys.add(key)

    # Initialize empty columns
    for key in all_keys:
        df[key] = None

    # Fill values
    for idx, label_list in enumerate(df["labels"]):
        if not label_list:
            continue
        for label in label_list:
            if "::" in label:
                parts = label.split("::")
                key = parts[0].strip().lower()
                value = parts[1].strip() if len(parts) > 1 else None
                # If multiple values for same key, join with comma
                if df.at[idx, key]:
                    df.at[idx, key] += f", {value}"
                else:
                    df.at[idx, key] = value

    # Optional: clean column names (replace spaces with underscores)
    df.rename(columns=lambda x: x.replace(" ", "_").lower(), inplace=True)
    return df

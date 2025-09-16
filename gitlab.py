import requests
import csv

# === CONFIGURATION ===
GITLAB_URL = "https://gitlab.com"  # Change if self-hosted
PROJECT_ID = "<your_project_id>"   # Find in Project → Settings → General
PRIVATE_TOKEN = "<your_personal_access_token>"
OUTPUT_FILE = "issues_with_labels.csv"

headers = {"PRIVATE-TOKEN": PRIVATE_TOKEN}
all_issues = []
page = 1

print("Fetching issues...")

# === FETCH ALL ISSUES (PAGINATED) ===
while True:
    url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/issues"
    params = {"per_page": 100, "page": page, "state": "all"}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Error fetching issues: {response.status_code} - {response.text}")
        break

    issues = response.json()
    if not issues:
        break

    all_issues.extend(issues)
    page += 1

print(f"Fetched {len(all_issues)} issues.")

# === COLLECT ALL UNIQUE LABELS ===
all_labels = set()
for issue in all_issues:
    all_labels.update(issue.get("labels", []))

sorted_labels = sorted(all_labels)
print(f"Found {len(sorted_labels)} unique labels.")

# === WRITE TO CSV ===
with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    # Base columns + one column per label
    header = ["IID", "Title", "State", "Author", "Assignee", "Created At", "Due Date"] + sorted_labels
    writer.writerow(header)

    for issue in all_issues:
        row = [
            issue["iid"],
            issue["title"],
            issue["state"],
            issue["author"]["username"],
            issue["assignee"]["username"] if issue.get("assignee") else "",
            issue["created_at"],
            issue.get("due_date", "")
        ]

        issue_labels = set(issue.get("labels", []))
        # For each possible label, put 1 if present, else 0
        for label in sorted_labels:
            row.append(1 if label in issue_labels else 0)

        writer.writerow(row)

print(f"Issues saved to {OUTPUT_FILE}")

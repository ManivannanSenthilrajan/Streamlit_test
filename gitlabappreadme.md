📊 GitLab Issue Dashboard (Streamlit)

A Streamlit-based dashboard to fetch, visualize, and manage GitLab project issues.
Supports filtering, Kanban-style view, hygiene checks with quick fixes, and editable sprint commentary.

🚀 Features
🔑 GitLab Connection

Enter Project ID and Personal Access Token in the sidebar.

Fetches all issues from the project using GitLab API.

🧭 Tabs Overview

Overview

Shows issue counts by status.

Groups by Label::Value convention (Team, Status, Sprint, Workstream, Project).

Filterable by Sprint, Team, Status, Project, and Milestone.

Exportable to Excel.

By Sprint → Team → Status (Kanban)

Visualizes issues in Kanban-style swimlanes.

Status color-coded:

✅ Done → Green

🟡 In Progress → Yellow

🔴 Blocked → Red

⚪ To Do → Gray

Filterable using sidebar filters.

Exportable to Excel.

Hygiene

Highlights issues missing critical fields:

No Team, No Status, No Project, No Sprint, No Title, No Milestone.

Quick Fix: Edit missing fields inline, updates GitLab directly.

Table refreshes automatically after fixes.

Exportable to Excel.

Commentary

Editable sprint commentary (Sprint Scope, Capacity, Key Dates, Sprint Review, Carry Over Issues, Next Steps, Achievements, Risks).

Saved locally in commentary.json (multi-user append supported).

Downloadable JSON for reporting.

🎨 UI & Styling

Font stack: "Frutiger45Light", "Segoe UI", "Helvetica Neue", Arial, sans-serif.

Status label color coding in Kanban cards.

Clean card-based layout for readability.

📦 Requirements
pip install streamlit pandas requests openpyxl

▶️ Run the App
streamlit run app.py

⚙️ How It Works

Fetch Issues: Uses GitLab API to fetch all issues.

Normalize Labels: Converts Key::Value labels into structured columns.

Sidebar Filters: Filter issues by Team, Status, Sprint, Project, Milestone.

Overview Tab: Shows counts and summaries, downloadable as Excel.

Kanban Tab: Visual board by Sprint → Team → Status, color-coded.

Hygiene Tab: Detects missing fields, allows inline fixes directly updating GitLab.

Commentary Tab: Editable sprint notes, persisted in commentary.json, downloadable.

📂 File Structure
gitlab-issue-dashboard/
 ┣ app.py               # Main Streamlit app
 ┣ commentary.json      # Sprint commentary (auto-created)
 ┣ README.md            # Documentation

🔑 Notes

Label convention: Key::Value (e.g., Team::Backend, Status::In Progress, Sprint::Q3-2025).

Extra spaces in labels are normalized automatically.

GitLab personal access token requires read_api and write_api scopes.

📌 Use Cases

Scrum Masters or Project Managers can:

Monitor sprint progress in real-time.

Identify and fix hygiene issues quickly.

Add collaborative sprint commentary.

Export data for reporting.

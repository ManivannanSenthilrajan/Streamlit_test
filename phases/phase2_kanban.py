import streamlit as st
import pandas as pd

# Define color mapping for statuses
STATUS_COLORS = {
    "done": "#d4edda",       # light green
    "closed": "#d4edda",     # treat as done
    "in progress": "#cce5ff",# light blue
    "todo": "#fff3cd",       # yellow
    "blocked": "#f8d7da"     # light red
}

def render():
    if "issues_df" not in st.session_state:
        st.info("Load data first in Overview tab.")
        return

    df = st.session_state["issues_df"]

    # 🔄 Ensure multi-value labels (like sprint) are split into rows
    for col in df.columns:
        if df[col].dtype == object and df[col].str.contains(",").any():
            df = df.assign(**{col: df[col].str.split(",")}).explode(col)
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    st.subheader("🗂️ Kanban Board")

    # Detect label columns dynamically
    label_columns = [col for col in df.columns if col not in ["id", "title", "description", "web_url"]]

    # Add swimlane grouping selection
    group_field = st.selectbox("📊 Group swimlanes by", ["status"] + label_columns)
    if group_field not in df.columns:
        st.warning(f"'{group_field}' column not found in data.")
        return

    # Sidebar filters
    with st.sidebar:
        st.markdown("### 🔍 Filters")
        filters = {}
        for col in label_columns:
            unique_values = sorted(df[col].dropna().unique())
            filters[col] = st.multiselect(f"{col.capitalize()}", unique_values)

    filtered = df.copy()
    for col, selected_values in filters.items():
        if selected_values:
            filtered = filtered[filtered[col].isin(selected_values)]

    swimlanes = sorted(filtered[group_field].dropna().unique())
    if not swimlanes:
        st.warning("No issues match the selected filters.")
        return

    selected_issue = st.session_state.get("selected_issue")

    # CSS for sticky panel
    st.markdown("""
        <style>
        .sticky-panel {
            position: sticky;
            top: 0;
            background-color: #f8f9fa;
            border-left: 2px solid #ddd;
            padding: 1rem;
            height: 90vh;
            overflow-y: auto;
        }
        .issue-card {
            border-radius: 10px;
            padding: 8px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: transform 0.1s ease-in-out;
        }
        .issue-card:hover {
            transform: scale(1.02);
        }
        </style>
    """, unsafe_allow_html=True)

    # Layout: left board + right sticky detail panel
    board_col, detail_col = st.columns([3, 1])

    with board_col:
        cols = st.columns(len(swimlanes))
        for i, swimlane in enumerate(swimlanes):
            with cols[i]:
                st.markdown(f"### {swimlane or 'No Value'}")
                for _, row in filtered[filtered[group_field] == swimlane].iterrows():
                    bg = STATUS_COLORS.get(str(row.get("status", "")).lower(), "#ffffff")
                    unique_key = f"btn_{row['id']}_{swimlane}_{row.get('project','')}"

                    if st.button(row['title'], key=unique_key, help="Click to view details"):
                        st.session_state["selected_issue"] = row.to_dict()
                        selected_issue = st.session_state["selected_issue"]

                    st.markdown(
                        f"""
                        <div class="issue-card" style="background-color: {bg};">
                            <strong>{row['title']}</strong><br>
                            <small>{", ".join(f"{c}: {row[c]}" for c in label_columns if row[c])}</small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    with detail_col:
        st.markdown('<div class="sticky-panel">', unsafe_allow_html=True)
        if selected_issue:
            st.markdown("### 📝 Issue Details")
            st.markdown(f"**Title:** {selected_issue['title']}")
            st.markdown(f"**Description:** {selected_issue.get('description','(No description)')}")
            for col in label_columns:
                st.markdown(f"**{col.capitalize()}:** {selected_issue.get(col, '—')}")
            st.link_button("🔗 Open in GitLab", selected_issue['web_url'])
            if st.button("❌ Close Panel"):
                st.session_state["selected_issue"] = None
                selected_issue = None
                st.experimental_rerun()
        else:
            st.markdown("_Select an issue from the board to see details here._")
        st.markdown('</div>', unsafe_allow_html=True)

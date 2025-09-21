import streamlit as st
import pandas as pd

# Define color mapping for statuses
STATUS_COLORS = {
    "done": "#d4edda",
    "closed": "#d4edda",
    "in progress": "#cce5ff",
    "todo": "#fff3cd",
    "blocked": "#f8d7da"
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

    # Maintain selection state for right-side detail view
    selected_issue = st.session_state.get("selected_issue")

    # Layout: left Kanban board + right detail panel
    board_col, detail_col = st.columns([3, 1])
    with board_col:
        cols = st.columns(len(swimlanes))
        for i, swimlane in enumerate(swimlanes):
            with cols[i]:
                st.markdown(f"### {swimlane or 'No Value'}")
                for _, row in filtered[filtered[group_field] == swimlane].iterrows():
                    bg = STATUS_COLORS.get(str(row.get("status", "")).lower(), "#ffffff")
                    if st.button(row['title'], key=f"btn_{row['id']}", help="Click to view details"):
                        st.session_state["selected_issue"] = row.to_dict()
                        selected_issue = st.session_state["selected_issue"]

                    st.markdown(
                        f"""
                        <div style="background-color: {bg}; padding: 8px; border-radius: 10px; margin-bottom: 5px;">
                            <strong>{row['title']}</strong><br>
                            <small>{", ".join(f"{c}: {row[c]}" for c in label_columns if row[c])}</small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    with detail_col:
        if selected_issue:
            st.markdown("### 📝 Issue Details")
            st.markdown(f"**Title:** {selected_issue['title']}")
            st.markdown(f"**Description:** {selected_issue.get('description','(No description)')}")
            for col in label_columns:
                st.markdown(f"**{col.capitalize()}:** {selected_issue.get(col, '—')}")
            st.link_button("🔗 Open in GitLab", selected_issue['web_url'])

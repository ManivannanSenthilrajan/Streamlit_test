# phases/phase2_kanban.py
import streamlit as st
import pandas as pd

# Color mapping for statuses (extend if you want more)
STATUS_COLORS = {
    "done": "#d4edda",
    "closed": "#d4edda",
    "in progress": "#cce5ff",
    "inprogress": "#cce5ff",
    "todo": "#fff3cd",
    "blocked": "#f8d7da"
}


def render():
    """
    Kanban board:
    - dynamic grouping (status, team, project, etc.)
    - dynamic filters for any parsed label column
    - sticky right panel that shows issue details
    - unique button keys (avoids duplicate-key errors)
    """
    if "issues_df" not in st.session_state:
        st.info("Load data first in the Overview tab (enter token & project IDs, then Refresh).")
        return

    # Work on a copy
    df = st.session_state["issues_df"].copy()

    # --- Handle multi-value cells (common for 'sprint' etc.)
    # Convert comma-separated strings to lists, then explode only those columns.
    # This keeps the association of other fields intact and ensures each exploded row has a unique index.
    multi_cols = []
    for col in df.columns:
        if df[col].dtype == object:
            # convert NaN to empty string to avoid errors; check for comma presence
            if df[col].fillna("").str.contains(",").any():
                multi_cols.append(col)
                df[col] = df[col].fillna("").astype(str).str.split(",")

    for col in multi_cols:
        df = df.explode(col)

    # Trim string columns
    df = df.apply(lambda s: s.str.strip() if s.dtype == "object" else s)

    # Reset index to ensure a unique integer index for each row -> used to create unique button keys
    df = df.reset_index(drop=True)

    st.subheader("🗂️ Kanban Board")

    # Label columns: everything except core fields
    label_columns = [c for c in df.columns if c not in ("id", "title", "description", "web_url")]

    # Build group options (status first if available)
    group_options = []
    if "status" in label_columns:
        group_options.append("status")
    # then add other label columns (avoid duplicates)
    for c in label_columns:
        if c not in group_options:
            group_options.append(c)

    # Group by selection
    group_field = st.selectbox("📊 Group swimlanes by", options=group_options, index=0)

    # Show/hide details panel toggle
    show_panel = st.checkbox("Show details panel", value=True, key="kanban_show_panel")

    # Sidebar: dynamic filters (one multi-select per label column)
    with st.sidebar:
        st.markdown("### 🔍 Kanban Filters")
        filters = {}
        for col in label_columns:
            unique_vals = sorted([v for v in df[col].dropna().unique() if str(v) != ""])
            # use a distinct key per filter to avoid key collision with other tabs
            filters[col] = st.multiselect(f"{col.capitalize()}", unique_vals, key=f"kanban_filter_{col}")

    # Apply filters
    filtered = df.copy()
    for col, sel in filters.items():
        if sel:
            filtered = filtered[filtered[col].isin(sel)]

    # If grouped field no longer exists after filtering
    if group_field not in filtered.columns:
        st.warning(f"Grouping field '{group_field}' not available after filtering.")
        return

    # Build ordered swimlanes from the filtered dataset
    swimlanes = sorted(filtered[group_field].fillna("").unique(), key=lambda x: str(x))

    if len(swimlanes) == 0:
        st.warning("No issues match the selected filters.")
        return

    # Keep current selected issue in session_state
    selected_issue = st.session_state.get("selected_issue")

    # CSS for sticky panel + nicer card hover
    st.markdown(
        """
    <style>
    .sticky-panel {
        position: sticky;
        top: 0;
        background-color: #fbfbfb;
        border-left: 1px solid rgba(0,0,0,0.06);
        padding: 10px;
        height: 90vh;
        overflow-y: auto;
    }
    .kanban-card-html {
        border-radius: 8px;
        padding: 8px;
        margin-bottom: 8px;
        transition: transform .08s ease-in-out;
    }
    .kanban-card-html:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.06); }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Choose layout columns depending on whether panel is shown
    if show_panel:
        board_col, detail_col = st.columns([3, 1])
    else:
        board_col = st.columns([1])[0]
        detail_col = None

    # Render the Kanban columns (board)
    with board_col:
        cols = st.columns(len(swimlanes))
        for i, lane in enumerate(swimlanes):
            with cols[i]:
                st.markdown(f"### {lane or 'No Value'}")
                subdf = filtered[filtered[group_field] == lane]
                if subdf.empty:
                    st.write("_No issues_")
                    continue

                # Iterate by integer index (unique after reset_index) -> prevents duplicate button keys
                for idx in subdf.index:
                    row = subdf.loc[idx]
                    # normalize status for color mapping
                    status_val = str(row.get("status", "")).lower() if row.get("status") else ""
                    bg = STATUS_COLORS.get(status_val, "#ffffff")

                    # create a guaranteed-unique key for every button
                    unique_key = f"kanban_btn_{idx}_{row.get('id','')}_{str(lane)}_{row.get('project','')}"

                    # the visible button (clicking sets selected_issue)
                    if st.button(row["title"], key=unique_key):
                        st.session_state["selected_issue"] = row.to_dict()

                    # present a lightweight HTML card below/above the button for info (styling only)
                    meta = ", ".join(f"{c}: {row[c]}" for c in label_columns if row.get(c))
                    st.markdown(
                        f"""
                        <div class="kanban-card-html" style="background:{bg};">
                            <strong>{row['title']}</strong><br>
                            <small>{meta}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    # Render the sticky right details panel (if enabled)
    if show_panel:
        with detail_col:
            st.markdown('<div class="sticky-panel">', unsafe_allow_html=True)
            sel = st.session_state.get("selected_issue")
            if sel:
                st.markdown("### 📝 Issue Details")
                st.markdown(f"**Title:** {sel.get('title')}")
                st.markdown(f"**Description:** {sel.get('description', '(No description)')}")
                st.markdown("---")
                for c in label_columns:
                    st.markdown(f"**{c.capitalize()}:** {sel.get(c, '—')}")
                st.markdown(f"[Open in GitLab]({sel.get('web_url')})")
                # close button to clear selection and collapse panel if desired
                if st.button("❌ Close Panel", key="kanban_close_panel"):
                    st.session_state["selected_issue"] = None
                    # rerun to clear UI state immediately
                    st.experimental_rerun()
            else:
                st.markdown("_Select an issue from the board to see details here._")
            st.markdown("</div>", unsafe_allow_html=True)

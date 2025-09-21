import streamlit as st
from utils.gitlab_api import download_excel

def render():
    if "issues_df" not in st.session_state:
        st.info("Enter token and project IDs, then click **Refresh Issues** to load data.")
        return

    df = st.session_state["issues_df"]

    st.subheader("📌 Overview")

    # Dynamically detect all label-based columns (besides id, title, description, web_url)
    label_columns = [col for col in df.columns if col not in ["id", "title", "description", "web_url"]]

    # Sidebar Filters (dynamically created)
    with st.sidebar:
        st.markdown("### 🔍 Filters")
        filters = {}
        for col in label_columns:
            unique_values = sorted(df[col].dropna().unique())
            filters[col] = st.multiselect(col.capitalize(), unique_values)

    # Apply filters dynamically
    filtered_df = df.copy()
    for col, selected_values in filters.items():
        if selected_values:
            filtered_df = filtered_df[filtered_df[col].isin(selected_values)]

    # Dynamic summary cards (1 row with up to 4 cards per row)
    cols = st.columns(min(len(label_columns), 4))
    for i, col in enumerate(label_columns):
        with cols[i % 4]:
            st.metric(col.capitalize(), filtered_df[col].nunique())

    st.dataframe(filtered_df, use_container_width=True)

    excel_data = download_excel(filtered_df)
    st.download_button(
        "📥 Download Filtered Issues (Excel)",
        data=excel_data,
        file_name="issues.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

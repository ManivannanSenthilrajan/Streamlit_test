import streamlit as st
from utils.gitlab_api import download_excel
from utils.ui_components import summary_cards

def render():
    if "issues_df" not in st.session_state:
        st.info("Enter token and project IDs, then click **Refresh Issues** to load data.")
        return

    df = st.session_state["issues_df"]

    st.subheader("📌 Overview")

    with st.sidebar:
        st.markdown("### 🔍 Filters")
        selected_team = st.multiselect("Team", sorted(df["team"].unique()))
        selected_sprint = st.multiselect("Sprint", sorted(df["sprint"].unique()))
        selected_status = st.multiselect("Status", sorted(df["status"].unique()))

    filtered_df = df.copy()
    if selected_team:
        filtered_df = filtered_df[filtered_df["team"].isin(selected_team)]
    if selected_sprint:
        filtered_df = filtered_df[filtered_df["sprint"].isin(selected_sprint)]
    if selected_status:
        filtered_df = filtered_df[filtered_df["status"].isin(selected_status)]

    summary_cards(filtered_df)
    st.dataframe(filtered_df, use_container_width=True)

    excel_data = download_excel(filtered_df)
    st.download_button("📥 Download Filtered Issues", data=excel_data,
                       file_name="issues.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

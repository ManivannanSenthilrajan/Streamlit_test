import streamlit as st
import graphviz
import pandas as pd
import time
import random

# ----------------------------
# MOCK DATA GENERATOR
# ----------------------------
def generate_mock_master_data():
    funds = ["Fund_A", "Fund_B", "Fund_C"]
    metrics = ["Cost Leverage", "Par Value", "Watch List"]
    columns = ["Private Loan", "Public Loan", "Price Change to Other Private Investments", 
               "ADS", "Middle Market", "Large Market"]
    quarters = ["2025-Q1", "2025-Q2", "2025-Q3"]

    data = []
    for fund in funds:
        for quarter in quarters:
            for metric in metrics:
                for col in columns:
                    value = (
                        round(random.uniform(0, 100), 2)
                        if metric != "Watch List"
                        else random.choice(["Yes", "No"])
                    )
                    data.append({
                        "Fund_Name": fund,
                        "Metric_Name": metric,
                        "Column_Name": col,
                        "Quarter": quarter,
                        "Value": value
                    })
    return pd.DataFrame(data)

# ----------------------------
# STREAMLIT APP
# ----------------------------
def app():
    st.set_page_config(page_title="Fund Data ETL Simulation", page_icon="🔄", layout="wide")
    st.title("🔄 Fund Data ETL Process & Future App Simulation")

    st.markdown("""
    This demo shows the **end-to-end fund data process** from file upload, ETL, 
    to the future app visualizations.  

    **Important Notes:**
    - This is purely a **backend process demo**. Users can see fund metrics, fund comparison, 
      and add commentary in the front-end app.
    - It is the **responsibility of the domain/fund owner or point of contact** to upload the files.
    - All teams must ensure the **data is clean and accurate**; otherwise, the process will not work.
    """)

    # ----------------------------
    # STEP 1: FILE UPLOAD SIMULATION
    # ----------------------------
    st.header("📂 Step 1: Upload Files to Landing Zone")
    uploaded_files = st.file_uploader(
        "Upload one or more Excel files (simulated)", 
        type=["xlsx"], accept_multiple_files=True
    )
    if uploaded_files:
        st.success(f"{len(uploaded_files)} file(s) uploaded to Landing Zone.")
        st.write("**Files in Landing Zone:**")
        for file in uploaded_files:
            st.write(f"📄 {file.name}")

    # ----------------------------
    # STEP 2: ETL SIMULATION
    # ----------------------------
    st.header("⚙️ Step 2: Run ETL Pipeline")
    etl_ran = False
    if st.button("Run ETL Process"):
        with st.spinner("Processing files..."):
            time.sleep(2)
        st.success("✅ ETL completed successfully! Data appended to master file.")
        etl_ran = True
        master_df = generate_mock_master_data()
    else:
        master_df = pd.DataFrame()

    # ----------------------------
    # VISUAL FLOW DIAGRAM (Enhanced Dashboard Panels)
    # ----------------------------
    st.header("🔀 End-to-End Visual Flow (Including Future App)")

    flow = graphviz.Digraph(format="png")
    flow.attr(rankdir="LR", bgcolor="white", nodesep="1.0", splines="ortho")

    # Backend steps
    flow.node("Landing", "Step 1:\n📂 Landing Zone\nFiles uploaded by fund owner", shape="folder", style="filled", fillcolor="#f2f2f2")
    flow.node("ETL", "Step 2:\n⚙️ ETL Pipeline\n(Unpivot + Clean + Append)\n*Teams must ensure data is clean*", shape="box", style="filled", fillcolor="#ffe6cc")
    flow.node("Master", "Step 3:\n🗄️ Consolidated Master File", shape="cylinder", style="filled", fillcolor="#d9ead3")

    # Future app as a cluster (dashboard)
    flow.attr('node', shape='box3d', style='filled', color='black')
    with flow.subgraph(name='cluster_App') as app_cluster:
        app_cluster.attr(style='rounded,filled', fillcolor='#e8f4f8', label='Front-End App', fontsize='16')
        app_cluster.node("FundMetrics", "📊 Fund Metrics")
        app_cluster.node("FundComparison", "📈 Fund Comparison")
        app_cluster.node("UserCommentary", "📝 User Commentary")
        app_cluster.edge("FundMetrics", "FundComparison")
        app_cluster.edge("FundMetrics", "UserCommentary")
        app_cluster.edge("FundComparison", "UserCommentary")

    # Connections from backend to app
    flow.edge("Landing", "ETL")
    flow.edge("ETL", "Master")
    flow.edge("Master", "FundMetrics")  # entering the dashboard

    st.graphviz_chart(flow, use_container_width=True)

    # ----------------------------
    # STAR SCHEMA DATA MODEL
    # ----------------------------
    st.header("🔗 Star Schema Data Model")
    dot = graphviz.Digraph(format="png")
    dot.attr(rankdir='TB', bgcolor="white", nodesep="0.6")
    dot.node("Facts", "Fund_Facts\n(Fund_ID, Metric_ID, Column_ID, Date_ID, Value)",
             shape="box", style="filled", fillcolor="lightblue", color="black")
    dot.node("Fund", "Fund Dimension\n(Fund_ID, Fund_Name)", shape="box", style="filled", fillcolor="#f2f2f2")
    dot.node("Metric", "Metric Dimension\n(Metric_ID, Metric_Name)", shape="box", style="filled", fillcolor="#f2f2f2")
    dot.node("Column", "Column Dimension\n(Column_ID, Column_Name)", shape="box", style="filled", fillcolor="#f2f2f2")
    dot.node("Date", "Date Dimension\n(Date_ID, Quarter, Year)", shape="box", style="filled", fillcolor="#f2f2f2")
    dot.edges([("Facts","Fund"),("Facts","Metric"),("Facts","Column"),("Facts","Date")])
    st.graphviz_chart(dot, use_container_width=True)

    # ----------------------------
    # CONSOLIDATED DATA TABLE (at bottom)
    # ----------------------------
    if etl_ran and not master_df.empty:
        st.header("📊 Consolidated Fund Table")

        # Filters
        funds = sorted(master_df["Fund_Name"].unique())
        selected_funds = st.multiselect("Select Funds", options=funds, default=funds)
        quarters = sorted(master_df["Quarter"].unique())
        selected_quarters = st.multiselect("Select Quarters", options=quarters, default=quarters)

        filtered_df = master_df[
            (master_df["Fund_Name"].isin(selected_funds)) &
            (master_df["Quarter"].isin(selected_quarters))
        ]

        # Convert Yes/No to numeric
        filtered_df['Value'] = filtered_df['Value'].apply(
            lambda x: 1 if str(x).lower() == "yes" else (0 if str(x).lower() == "no" else x)
        )

        # Pivot: Metrics as rows, Column_Name as columns
        pivot_df = filtered_df.pivot_table(
            index=["Fund_Name","Metric_Name"],
            columns="Column_Name",
            values="Value",
            aggfunc="sum"
        ).fillna(0)

        # Add Total column
        pivot_df["Total"] = pivot_df.sum(axis=1)

        # Reset index for display
        final_df = pivot_df.reset_index()

        st.dataframe(final_df, use_container_width=True)

if __name__ == "__main__":
    app()

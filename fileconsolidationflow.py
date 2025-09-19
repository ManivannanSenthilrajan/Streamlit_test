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
    ### Disclaimer
    This is a **demo architecture flow** for **discussion/presentation purposes**.
    It illustrates how data flows from the landing zone to the final app view.
    """)

    # ----------------------------
    # BUSINESS VIEW DIAGRAM (High-level)
    # ----------------------------
    st.header("🏢 Business View: High-Level Process Flow")
    business_flow = graphviz.Digraph(format="png")
    business_flow.attr(rankdir="LR", bgcolor="white", nodesep="1.0", splines="ortho")

    # Landing zone
    business_flow.node(
        "Landing",
        "Landing Zone / Share Drive\n(Business uploads files)",
        shape="folder",
        style="filled,rounded",
        fillcolor="#c6efce",
        tooltip="Business users are provided entitlements to upload Excel files here."
    )
    # ETL process
    business_flow.node(
        "ETL",
        "ETL / Backend Processing\n(Unpivot + Clean + Append)",
        shape="box",
        style="filled,rounded",
        fillcolor="#ffeb9c",
        tooltip="The backend process runs automatically, cleaning and transforming uploaded data."
    )
    # Front-end app
    business_flow.node(
        "App",
        "Front-End App\n📊 Fund Metrics\n📈 Compare Funds\n📝 Add Commentary",
        shape="box3d",
        style="filled,rounded",
        fillcolor="#d9eaf7",
        tooltip="Users can view metrics, compare funds, and add commentary."
    )

    business_flow.edge("Landing", "ETL")
    business_flow.edge("ETL", "App")

    st.graphviz_chart(business_flow, use_container_width=True)

    # ----------------------------
    # TECHNICAL DETAILS: Star Schema & Consolidation
    # ----------------------------
    st.header("🔧 Technical View: Data Model & Process Flow")
    tech_flow = graphviz.Digraph(format="png")
    tech_flow.attr(rankdir='LR', bgcolor="white", nodesep="0.6", splines="ortho")

    # Input files
    tech_flow.node("InputFiles",
                   "29 Excel Files\n(Input)",
                   shape="folder", style="filled,rounded", fillcolor="#c6efce",
                   tooltip="Files placed in the landing zone by authorized users")
    # ETL
    tech_flow.node("ETLNode",
                   "ETL Pipeline\n(Unpivot + Clean + Append)",
                   shape="box", style="filled,rounded", fillcolor="#ffeb9c",
                   tooltip="Data is unpivoted, cleaned, and appended to master file")
    # Star Schema
    tech_flow.node("Facts", "Fact Table\n(Fund_Facts)",
                   shape="box", style="filled,rounded", fillcolor="#9fc5e8",
                   tooltip="Central fact table containing metric values per fund/column/quarter")
    tech_flow.node("FundDim", "Fund Dimension",
                   shape="box", style="filled,rounded", fillcolor="#d9ead3",
                   tooltip="Fund master data")
    tech_flow.node("MetricDim", "Metric Dimension",
                   shape="box", style="filled,rounded", fillcolor="#d9ead3",
                   tooltip="Metric master data")
    tech_flow.node("ColumnDim", "Column Dimension",
                   shape="box", style="filled,rounded", fillcolor="#d9ead3",
                   tooltip="Column/Investment type data")
    tech_flow.node("DateDim", "Date Dimension",
                   shape="box", style="filled,rounded", fillcolor="#d9ead3",
                   tooltip="Quarter/Year information")
    # Consolidated Master
    tech_flow.node("Consolidated",
                   "Consolidated Master File\n(Output)",
                   shape="cylinder", style="filled,rounded", fillcolor="#ffe6cc",
                   tooltip="Final consolidated dataset ready for front-end app")
    # Front-End App cluster
    with tech_flow.subgraph(name='cluster_App') as app_cluster:
        app_cluster.attr(style='rounded,filled', fillcolor='#d9eaf7', label='Front-End App', fontsize='16')
        app_cluster.node("FundMetrics", "📊 Fund Metrics")
        app_cluster.node("FundComparison", "📈 Fund Comparison")
        app_cluster.node("UserCommentary", "📝 User Commentary")
        app_cluster.edge("FundMetrics", "FundComparison")
        app_cluster.edge("FundMetrics", "UserCommentary")
        app_cluster.edge("FundComparison", "UserCommentary")

    # Connections
    tech_flow.edge("InputFiles", "ETLNode")
    tech_flow.edge("ETLNode", "Facts")
    tech_flow.edge("Facts", "FundDim")
    tech_flow.edge("Facts", "MetricDim")
    tech_flow.edge("Facts", "ColumnDim")
    tech_flow.edge("Facts", "DateDim")
    tech_flow.edge("Facts", "Consolidated")
    tech_flow.edge("Consolidated", "FundMetrics")

    st.graphviz_chart(tech_flow, use_container_width=True)

    # ----------------------------
    # STAR SCHEMA DATA MODEL
    # ----------------------------
    st.header("🔗 Star Schema Data Model")
    dot = graphviz.Digraph(format="png")
    dot.attr(rankdir='TB', bgcolor="white", nodesep="0.6")
    dot.node("Facts", "Fund_Facts\n(Fund_ID, Metric_ID, Column_ID, Date_ID, Value)",
             shape="box", style="filled", fillcolor="#9fc5e8", color="black",
             tooltip="Fact table contains all metric values")
    dot.node("Fund", "Fund Dimension\n(Fund_ID, Fund_Name)", shape="box", style="filled", fillcolor="#d9ead3",
             tooltip="Details of funds")
    dot.node("Metric", "Metric Dimension\n(Metric_ID, Metric_Name)", shape="box", style="filled", fillcolor="#d9ead3",
             tooltip="Details of metrics")
    dot.node("Column", "Column Dimension\n(Column_ID, Column_Name)", shape="box", style="filled", fillcolor="#d9ead3",
             tooltip="Columns for investments")
    dot.node("Date", "Date Dimension\n(Date_ID, Quarter, Year)", shape="box", style="filled", fillcolor="#d9ead3",
             tooltip="Time dimension")
    dot.edges([("Facts","Fund"),("Facts","Metric"),("Facts","Column"),("Facts","Date")])
    st.graphviz_chart(dot, use_container_width=True)

    # ----------------------------
    # STEP 1 & STEP 2: Upload & Run ETL
    # ----------------------------
    st.header("⚡ Runtime Actions: Upload Files & Run ETL")
    uploaded_files = st.file_uploader(
        "Upload one or more Excel files (simulated)",
        type=["xlsx"], accept_multiple_files=True, key="runtime_upload"
    )
    if uploaded_files:
        st.success(f"{len(uploaded_files)} file(s) uploaded to Landing Zone.")

    etl_ran = False
    if st.button("Run ETL Process (Simulated)"):
        with st.spinner("Processing files..."):
            time.sleep(2)
        st.success("✅ ETL completed successfully! Data appended to master file.")
        etl_ran = True
        master_df = generate_mock_master_data()
    else:
        master_df = pd.DataFrame()

    # ----------------------------
    # CONSOLIDATED DATA TABLE
    # ----------------------------
    if etl_ran and not master_df.empty:
        st.header("📊 Consolidated Fund Table")

        # Filters
        funds = sorted(master_df["Fund_Name"].unique())
        selected_funds = st.multiselect("Select Funds", options=funds, default=funds, key="fund_filter")
        quarters = sorted(master_df["Quarter"].unique())
        selected_quarters = st.multiselect("Select Quarters", options=quarters, default=quarters, key="quarter_filter")

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

        final_df = pivot_df.reset_index()

        st.dataframe(final_df, use_container_width=True)

if __name__ == "__main__":
    app()

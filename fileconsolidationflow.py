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
    This is a **demo architecture flow** and only for **discussion/presentation purposes**.  
    It illustrates how data flows from the landing zone to the final app view.
    """)

    # ----------------------------
    # BUSINESS VIEW DIAGRAM (High-level)
    # ----------------------------
    st.header("🏢 Business View: High-Level Process Flow")
    business_flow = graphviz.Digraph(format="png")
    business_flow.attr(rankdir="LR", bgcolor="white", nodesep="1.0", splines="ortho")

    business_flow.node("Landing", "Landing Zone / Share Drive\n(Business uploads files)", shape="folder", style="filled", fillcolor="#f2f2f2")
    business_flow.node("ETL", "ETL / Processing\n(Backend process)", shape="box", style="filled", fillcolor="#ffe6cc")
    business_flow.node("App", "Front-End App\nView Fund Metrics\nCompare Funds\nAdd Commentary", shape="box3d", style="filled", fillcolor="#f0f4f8")

    business_flow.edge("Landing", "ETL")
    business_flow.edge("ETL", "App")

    st.graphviz_chart(business_flow, use_container_width=True)

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
    # TECHNICAL DETAILS: Star Schema & Consolidation
    # ----------------------------
    st.header("🔧 Technical View: Data Model & Process Flow")
    tech_flow = graphviz.Digraph(format="png")
    tech_flow.attr(rankdir='LR', bgcolor="white", nodesep="0.6", splines="ortho")

    # Input files
    tech_flow.node("InputFiles", "29 Excel Files\n(Input)", shape="folder", style="filled", fillcolor="#f2f2f2")
    # ETL
    tech_flow.node("ETLNode", "ETL Pipeline\n(Unpivot + Clean + Append)", shape="box", style="filled", fillcolor="#ffe6cc")
    # Star Schema
    tech_flow.node("Facts", "Fact Table\n(Fund_Facts)", shape="box", style="filled", fillcolor="#cfe2f3")
    tech_flow.node("FundDim", "Fund Dimension", shape="box", style="filled", fillcolor="#d9ead3")
    tech_flow.node("MetricDim", "Metric Dimension", shape="box", style="filled", fillcolor="#d9ead3")
    tech_flow.node("ColumnDim", "Column Dimension", shape="box", style="filled", fillcolor="#d9ead3")
    tech_flow.node("DateDim", "Date Dimension", shape="box", style="filled", fillcolor="#d9ead3")
    # Consolidated Master
    tech_flow.node("Consolidated", "Consolidated Master File\n(Output)", shape="cylinder", style="filled", fillcolor="#ffe6cc")
    # Front-End App cluster
    with tech_flow.subgraph(name='cluster_App') as app_cluster:
        app_cluster.attr(style='rounded,filled', fillcolor='#f0f4f8', label='Front-End App', fontsize='16')
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

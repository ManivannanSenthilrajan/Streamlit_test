import streamlit as st
import graphviz
import pandas as pd
import time
import random

# ----------------------------
# MOCK DATA GENERATOR
# ----------------------------
def generate_mock_master_data():
    """Generate a mock master dataset with multiple funds, metrics, columns, and quarters."""
    funds = ["Fund_A", "Fund_B", "Fund_C"]
    metrics = ["Cost Leverage", "Par Value", "Watch List"]
    columns = ["Public Loan", "Price", "Private Loan"]
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
                    data.append(
                        {
                            "Fund_Name": fund,
                            "Metric_Name": metric,
                            "Column_Name": col,
                            "Quarter": quarter,
                            "Value": value,
                        }
                    )
    return pd.DataFrame(data)

# ----------------------------
# STREAMLIT APP
# ----------------------------
def app():
    st.set_page_config(page_title="Fund Data ETL Simulation", page_icon="🔄", layout="wide")
    st.title("🔄 Fund Data ETL Process & Data Model (Simulation)")

    st.markdown("""
    This interactive demo shows how fund data flows from quarterly Excel files 
    into a consolidated **reporting data model**. 
    """)

    # ----------------------------
    # STEP 1: FILE UPLOAD SIMULATION
    # ----------------------------
    st.header("📂 Step 1: Upload Files to Landing Zone")
    uploaded_files = st.file_uploader("Upload one or more Excel files (simulated)", 
                                      type=["xlsx"], accept_multiple_files=True)

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
            time.sleep(2)  # simulate ETL run
        st.success("✅ ETL completed successfully! Data appended to master file.")
        etl_ran = True
        master_df = generate_mock_master_data()
    else:
        master_df = pd.DataFrame()

    # ----------------------------
    # VISUAL FLOW DIAGRAM
    # ----------------------------
    st.header("🔀 End-to-End Visual Flow")
    flow = graphviz.Digraph(format="png")
    flow.attr(rankdir="LR", bgcolor="white", nodesep="1.0", splines="ortho")

    flow.node("Landing", "Step 1:\n📂 Landing Zone\n29 Excel Files", shape="folder", style="filled", fillcolor="#f2f2f2")
    flow.node("ETL", "Step 2:\n⚙️ ETL Pipeline\n(Unpivot + Clean + Append)", shape="box", style="filled", fillcolor="#ffe6cc")
    flow.node("Master", "Step 3:\n🗄️ Master File\n(consolidated CSV in Reporting Zone)", shape="cylinder", style="filled", fillcolor="#d9ead3")
    flow.node("Model", "Step 4:\n📊 Star Schema\nFund_Facts + Dimensions", shape="box3d", style="filled", fillcolor="#cfe2f3")

    flow.edge("Landing", "ETL")
    flow.edge("ETL", "Master")
    flow.edge("Master", "Model")

    st.graphviz_chart(flow, use_container_width=True)

    # ----------------------------
    # SHOW TABLE AFTER FLOW DIAGRAM
    # ----------------------------
    if etl_ran and not master_df.empty:
        st.header("📊 Consolidated Data View")

        # --- FILTERS ---
        funds = sorted(master_df["Fund_Name"].unique())
        selected_funds = st.multiselect("Select Funds", options=funds, default=funds)

        filtered_df = master_df[master_df["Fund_Name"].isin(selected_funds)]

        # --- PIVOT: COLUMN NAMES AS ROWS, METRICS AS COLUMNS, QUARTERS + YTD AS COLUMNS ---
        pivot_df = filtered_df.pivot_table(
            index=["Fund_Name", "Column_Name", "Quarter"],
            columns="Metric_Name",
            values="Value",
            aggfunc="first"
        ).reset_index()

        # Compute YTD for each Fund + Column_Name
        ytd_df = (
            pivot_df.groupby(["Fund_Name", "Column_Name"])
            .agg({metric: "mean" for metric in pivot_df.columns if metric not in ["Fund_Name", "Column_Name", "Quarter"]})
            .reset_index()
        )
        ytd_df["Quarter"] = "YTD"
        pivot_df = pd.concat([pivot_df, ytd_df], ignore_index=True)

        final_pivot = pivot_df.pivot_table(
            index=["Fund_Name", "Column_Name"],
            columns="Quarter",
            values=[col for col in pivot_df.columns if col not in ["Fund_Name", "Column_Name", "Quarter"]],
            aggfunc="first"
        )

        st.dataframe(final_pivot, use_container_width=True)

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
    dot.edges([("Facts", "Fund"), ("Facts", "Metric"), ("Facts", "Column"), ("Facts", "Date")])

    st.graphviz_chart(dot, use_container_width=True)

if __name__ == "__main__":
    app()

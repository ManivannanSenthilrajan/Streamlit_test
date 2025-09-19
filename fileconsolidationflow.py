import streamlit as st
import graphviz
import pandas as pd
import time
import random

# ----------------------------
# FAKE DATA GENERATOR
# ----------------------------
def generate_mock_master_data():
    funds = ["Fund_A", "Fund_B", "Fund_C"]
    metrics = ["Cost Leverage", "Par Value", "Watch List"]
    columns = ["Public Loan", "Price", "Private Loan"]
    data = []
    for fund in funds:
        for metric in metrics:
            for col in columns:
                data.append({
                    "Fund_Name": fund,
                    "Metric_Name": metric,
                    "Column_Name": col,
                    "Quarter": "2025-Q3",
                    "Value": round(random.uniform(0, 100), 2) if metric != "Watch List" else random.choice(["Yes", "No"])
                })
    return pd.DataFrame(data)

# ----------------------------
# STREAMLIT APP
# ----------------------------
def app():
    st.set_page_config(page_title="Fund Data ETL Simulation", page_icon="🔄", layout="wide")
    st.title("🔄 Fund Data ETL Process & Data Model (Simulation)")

    st.markdown("""
    This interactive demo shows **how fund data flows** from Excel files to a consolidated reporting model.
    """)

    # ----------------------------
    # STEP 1: FILE UPLOAD SIMULATION
    # ----------------------------
    st.header("📂 Step 1: Upload Files to Landing Zone")
    uploaded_files = st.file_uploader("Upload one or more Excel files (simulated)", type=["xlsx"], accept_multiple_files=True)

    if uploaded_files:
        st.success(f"{len(uploaded_files)} file(s) uploaded to Landing Zone.")
        st.write("**Files in Landing Zone:**")
        for file in uploaded_files:
            st.write(f"📄 {file.name}")

    # ----------------------------
    # STEP 2: ETL SIMULATION
    # ----------------------------
    st.header("⚙️ Step 2: Run ETL Pipeline")
    if st.button("Run ETL Process"):
        with st.spinner("Processing files..."):
            time.sleep(2)  # simulate ETL run
        st.success("✅ ETL completed successfully! Data appended to master file.")
        master_df = generate_mock_master_data()
        st.dataframe(master_df.head(10), use_container_width=True)

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

    st.info("This process repeats each quarter — just upload new files and re-run ETL.")

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

    st.subheader("📄 Example of Normalized Data")
    st.markdown("""
    **Before (Raw Excel Layout):**

    | Metric        | Public Loan | Price  | Private Loan |
    |--------------|-------------|--------|-------------|
    | Cost Leverage| 0.45        | 100.25 | 0.50        |
    | Par Value    | 5,000,000   | 100,000| 2,000,000   |
    | Watch List   | Yes         | No     | Yes         |

    **After (Fact Table):**

    | Fund_Name | Metric_Name   | Column_Name  | Quarter | Value      |
    |----------|---------------|-------------|---------|-----------|
    | Fund_A   | Cost Leverage | Public Loan | 2025-Q1 | 0.45      |
    | Fund_A   | Cost Leverage | Price       | 2025-Q1 | 100.25    |
    | Fund_A   | Cost Leverage | Private Loan| 2025-Q1 | 0.50      |
    | Fund_A   | Par Value     | Public Loan | 2025-Q1 | 5,000,000 |
    | Fund_A   | Par Value     | Price       | 2025-Q1 | 100,000   |
    | Fund_A   | Watch List    | Private Loan| 2025-Q1 | Yes       |
    """)

if __name__ == "__main__":
    app()

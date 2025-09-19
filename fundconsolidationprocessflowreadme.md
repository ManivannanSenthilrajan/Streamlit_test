# Fund Data ETL & App Simulation

## **Purpose**

This Streamlit app is a **presentation/demo simulation** of a fund data ETL pipeline and a front-end app.

> **Note:** This is **not a production app**. It demonstrates how data flows from the landing zone to the final app view, including fund metrics, comparisons, and commentary.

The app illustrates:

- How business users provide data (landing zone)
- How backend ETL processes transform and consolidate data
- How the data feeds into a front-end app for metrics and comparison
- How the final consolidated table looks

It is designed to **tell a visual story**, not perform real production ETL.

---

## **Libraries Used**

- **streamlit** → interactive app and UI  
- **graphviz** → visualizing process flows and data models  
- **pandas** → data manipulation and pivot tables  
- **time & random** → simulate ETL runtime and mock data generation  

---

## **Data Generation**

The function `generate_mock_master_data()` generates a mock dataset for demonstration:

- **Funds:** `Fund_A`, `Fund_B`, `Fund_C`  
- **Metrics:** `Cost Leverage`, `Par Value`, `Watch List`  
- **Columns / Investment Types:** `Private Loan`, `Public Loan`, `Price Change to Other Private Investments`, `ADS`, `Middle Market`, `Large Market`  
- **Quarters:** `2025-Q1` to `2025-Q3`  

**Value assignment:**

- Numeric values for `Cost Leverage` and `Par Value`  
- `"Yes/No"` for `Watch List` metric  

Output is a Pandas DataFrame with columns: `Fund_Name`, `Metric_Name`, `Column_Name`, `Quarter`, `Value`.

---

## **App Flow**

The app is structured to **tell a story** from business perspective → technical → final data table.

### **1. Business Flow Diagram**

- **Landing Zone / Share Drive:** Business users upload files. Tooltip mentions **user entitlements**.  
- **ETL / Backend Processing:** Data is unpivoted, cleaned, appended. Tooltip notes **data cleaning responsibility**.  
- **Front-End App:** Users can view **fund metrics**, **compare funds**, and **add commentary**.

**Color coding:**  
- Green = Landing Zone  
- Yellow/Orange = ETL  
- Blue = Front-end App  

This diagram helps a **business audience understand the process** when they upload files.

---

### **2. Technical Flow Diagram**

Shows **internal workings / backend**:

- **Input files:** 29 Excel files  
- **ETL node:** Unpivot, clean, append  
- **Star Schema Tables:**
  - Fact Table: `Fund_Facts`
  - Dimensions: Fund, Metric, Column, Date
- **Consolidated Master File:** Output for front-end consumption  
- **Front-End App Cluster:** Fund Metrics, Fund Comparison, User Commentary  

**Color coding:**  
- Green = Input / Landing Zone  
- Yellow/Orange = ETL  
- Blue = Fact table  
- Light green = Dimensions  
- Orange = Consolidated master  
- Light blue = Front-end app  

**Tooltips** explain each block’s purpose.

---

### **3. Star Schema Diagram**

- **Fact Table:** All metric values per Fund/Column/Quarter  
- **Dimensions:** Fund, Metric, Column, Date  
- Shows **data organization logic** behind the consolidated table.

---

### **4. Runtime Actions: Step 1 & Step 2**

- **Step 1:** File upload simulation (represents **user uploading Excel files**)  
- **Step 2:** ETL run simulation (**backend processing occurs on login**)  
- Both steps are interactive to demonstrate **real-time backend behavior**.

---

### **5. Consolidated Fund Table**

- **Pivot Table Logic:**
  - Rows → `Metric_Name`  
  - Columns → `Column_Name` / investment types  
  - Values → numeric metric values; `"Yes/No"` converted to 1/0  
  - **Total column** added per row  

- **Filters:**  
  - By Fund  
  - By Quarter  

- Shows the **final output that end-users see** in the front-end app.

---

## **Key Design Notes**

1. **Presentation-ready & color-coded:** Business → Technical → Data Model → Runtime → Table  
2. **Annotations / tooltips:** Explain responsibilities (e.g., uploading files, cleaning data)  
3. **Storytelling order:** Business view → Technical → Star schema → Runtime → Consolidated table  
4. **Disclaimer:** Demo / discussion tool only  

---

## **How to Explain the Code**

1. **Business View:** Users upload files → ETL runs → App shows metrics  
2. **Technical Flow:** Fact and dimension tables → Consolidated master file → Front-end app  
3. **Star Schema:** Relationships between facts and dimensions  
4. **Runtime:** Upload file → Run ETL → See consolidated table  
5. **Highlight colors & tooltips** for visual clarity  

---

## **Benefits of This Demo**

- Provides **business-friendly visualization** of data flow  
- Illustrates **ETL and star schema concepts** without needing technical knowledge  
- Shows how **users interact with the system** (upload, metrics, commentary)  
- Useful for **presentations, training, or process discussions**

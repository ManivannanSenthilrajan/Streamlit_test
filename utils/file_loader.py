import pandas as pd
import os
from glob import glob
import streamlit as st

def load_excel_files_from_folder(folder, sheet_mapping):
    files = glob(os.path.join(folder, "*.xls*"))
    dataframes = {}
    if not files:
        st.error(f"No excel files found in {folder}")
        return dataframes
    for file in files:
        fname = os.path.basename(file)
        fund_name = os.path.splitext(fname)[0].replace("file", "").upper()
        if fname not in sheet_mapping:
            continue
        sheets = sheet_mapping[fname]
        if isinstance(sheets, str): sheets = [sheets]
        try:
            xls = pd.ExcelFile(file)
        except Exception as e:
            st.error(f"Could not open {fname}: {e}")
            continue
        for sheet in sheets:
            if sheet not in xls.sheet_names:
                st.warning(f"Sheet '{sheet}' not found in {fname}. Available: {xls.sheet_names}")
                continue
            try:
                df = pd.read_excel(file, sheet_name=sheet)
            except Exception as e:
                st.error(f"Could not read {fname} - {sheet}: {e}")
                continue
            if df.empty: continue
            df["Fund Name"] = fund_name
            dataframes[f"{fund_name} ({sheet})"] = df
    return dataframes

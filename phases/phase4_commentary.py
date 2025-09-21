import streamlit as st
import json
import os

COMMENTARY_FILE = "commentary.json"

def render():
    if "issues_df" not in st.session_state:
        st.info("Load data first in Overview tab.")
        return

    df = st.session_state["issues_df"]
    st.subheader("🗒️ Sprint Commentary")

    sprint = st.selectbox("Select Sprint", sorted(df["sprint"].unique()))

    if os.path.exists(COMMENTARY_FILE):
        with open(COMMENTARY_FILE, "r") as f:
            commentary_data = json.load(f)
    else:
        commentary_data = {}

    sprint_data = commentary_data.get(sprint, {})

    scope = st.text_area("Scope", sprint_data.get("scope", ""))
    dates = st.text_input("Key Dates", sprint_data.get("dates", ""))
    retro = st.text_area("Retro Comments", sprint_data.get("retro", ""))
    achievements = st.text_area("Achievements", sprint_data.get("achievements", ""))
    next_steps = st.text_area("Next Steps", sprint_data.get("next_steps", ""))
    challenges = st.text_area("Challenges", sprint_data.get("challenges", ""))

    if st.button("💾 Save Commentary"):
        commentary_data[sprint] = {
            "scope": scope,
            "dates": dates,
            "retro": retro,
            "achievements": achievements,
            "next_steps": next_steps,
            "challenges": challenges,
        }
        with open(COMMENTARY_FILE, "w") as f:
            json.dump(commentary_data, f, indent=2)
        st.success("Saved commentary!")

    if st.button("📥 Download Commentary"):
        st.download_button("Download Commentary", json.dumps(commentary_data, indent=2),
                           file_name="commentary.json")

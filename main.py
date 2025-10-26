import streamlit as st
import subprocess
from pathlib import Path
import sys

st.title("LangChain Multi-Agent Launcher")

agent = st.selectbox("Select an agent to run:", ["OpenAI + DDG", "Crew AI", "LangGraph Agent"])

if st.button("Launch Agent"):
    app_paths = {
        "OpenAI + DDG": "app/agent_openai_ddg.py",
        "Crew AI": "app/crew_ai.py",
        "LangGraph Agent": "app/langgraph_agent.py"
    }
    app_path = Path(app_paths[agent]).resolve()

    # Launch as a detached process (Linux/Mac)
    subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(app_path)],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
    st.success(f"{agent} launched in background! Open your browser to view it.")

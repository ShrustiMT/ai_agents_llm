# crew_ai.py

import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client['crew_ai_db']
collection = db['user_tasks']

# --- Crew AI Functions using OpenAI v1 API ---

def call_openai_chat(prompt):
    """
    Call OpenAI API using the new v1 interface.
    """
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    return response.choices[0].message.content

def task_breakdown_agent(task_text):
    prompt = f"Break down the following tasks into actionable subtasks:\n{task_text}\nOutput in bullet points."
    return call_openai_chat(prompt)

def scheduler_agent(task_breakdown):
    prompt = f"Schedule the following tasks with time slots starting from 9:00 AM:\n{task_breakdown}"
    return call_openai_chat(prompt)

def productivity_coach_agent(task_breakdown):
    prompt = f"Suggest productivity tips and techniques for completing these tasks:\n{task_breakdown}"
    return call_openai_chat(prompt)

# --- Streamlit UI ---
st.title("👥 Crew AI - Task Management Assistant")
st.write("Enter your tasks, and Crew AI will break them down, schedule them, and provide productivity tips.")

user_input = st.text_area("Your Tasks", "I need to write a blog post, do laundry, and prepare for tomorrow’s meeting.")

if st.button("Generate Crew Plan") and user_input.strip() != "":
    with st.spinner("Generating Crew Plan..."):
        breakdown = task_breakdown_agent(user_input)
        schedule = scheduler_agent(breakdown)
        tips = productivity_coach_agent(breakdown)

        # Save to MongoDB
        record = {
            "input": user_input,
            "breakdown": breakdown,
            "schedule": schedule,
            "tips": tips,
            "timestamp": datetime.now()
        }
        collection.insert_one(record)

        # Display results
        st.subheader("📝 Task Breakdown")
        st.text(breakdown)
        
        st.subheader("⏰ Schedule")
        st.text(schedule)
        
        st.subheader("💡 Productivity Tips")
        st.text(tips)

st.subheader("📚 Previous Crew Plans")
for entry in collection.find().sort("timestamp", -1).limit(5):
    st.markdown(f"**Input:** {entry['input']}")
    st.markdown(f"**Breakdown:** {entry['breakdown']}")
    st.markdown(f"**Schedule:** {entry['schedule']}")
    st.markdown(f"**Tips:** {entry['tips']}")
    st.markdown("---")


'''podman run -d \
  --name crew_mongo \
  -p 27017:27017 \
  -v mongo_data:/data/db \
  mongo:latest'''
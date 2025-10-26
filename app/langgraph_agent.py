import streamlit as st
from pymongo import MongoClient
from argon2 import PasswordHasher
import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from bson import ObjectId

# ----------------- MongoDB Setup -----------------
client = MongoClient("mongodb://localhost:27017")
db = client["langgraph_db"]
users_collection = db["users"]
chats_collection = db["email_chats"]
ph = PasswordHasher()

# ----------------- Auth Management -----------------
def signup_user(username, password):
    if users_collection.find_one({"username": username}):
        return False, "Username already exists."
    hashed_pw = ph.hash(password)
    users_collection.insert_one({"username": username, "password": hashed_pw})
    return True, "Signup successful! Please log in."

def login_user(username, password):
    user = users_collection.find_one({"username": username})
    if not user:
        return False, "User not found."
    try:
        ph.verify(user["password"], password)
        return True, "Login successful!"
    except:
        return False, "Incorrect password."

# ----------------- Chat Handling -----------------
def create_chat(username):
    chat = {
        "username": username,
        "title": f"Chat {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "details": {},
        "draft": "",
        "created_at": datetime.datetime.utcnow(),
    }
    return chats_collection.insert_one(chat).inserted_id

def get_user_chats(username):
    return list(chats_collection.find({"username": username}).sort("created_at", -1))

def save_message(username, role, content):
    chats_collection.update_one(
        {"username": username, "title": st.session_state.get("chat_title")},
        {"$push": {"messages": {"role": role, "content": content, "timestamp": datetime.datetime.utcnow()}}},
        upsert=True
    )

# ----------------- LangGraph Nodes -----------------
def input_node():
    st.subheader("✉️ Email Details")
    intent = st.selectbox("Select email type:", ["Meeting Request", "Follow-up", "Status Update"])
    recipient = st.text_input("Recipient Name / Email")
    purpose = st.text_input("Purpose / Key Points")
    tone = st.selectbox("Tone:", ["Professional", "Friendly", "Formal"])
    if st.button("Generate Draft"):
        return {"intent": intent, "recipient": recipient, "purpose": purpose, "tone": tone}
    return None

def template_node(intent, tone):
    templates = {
        "Meeting Request": {
            "Professional": "Dear {recipient},\nI would like to schedule a meeting regarding {purpose}...",
            "Friendly": "Hi {recipient},\nCan we catch up soon to discuss {purpose}?",
            "Formal": "Dear {recipient},\nI am requesting a meeting to discuss {purpose}."
        },
        "Follow-up": {
            "Professional": "Hello {recipient},\nFollowing up on {purpose}...",
            "Friendly": "Hey {recipient}, just checking in on {purpose}...",
            "Formal": "Dear {recipient},\nI am following up regarding {purpose}."
        },
        "Status Update": {
            "Professional": "Hello {recipient},\nHere is the update regarding {purpose}...",
            "Friendly": "Hi {recipient}, wanted to share an update on {purpose}...",
            "Formal": "Dear {recipient},\nPlease find below the status update on {purpose}."
        }
    }
    return templates[intent][tone]

def content_generation_node(template, details):
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)
    filled_template = template.format(recipient=details['recipient'], purpose=details['purpose'])
    prompt = f"Polish and improve this email draft while keeping the tone {details['tone']}:\n\n{filled_template}"
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content if response else filled_template

def email_agent(username, details):
    save_message(username, "user", str(details))
    template = template_node(details["intent"], details["tone"])
    draft = content_generation_node(template, details)
    save_message(username, "agent", draft)
    return draft

# ----------------- UI Styling (Lovable) -----------------
def lovable_style():
    st.markdown("""
        <style>
        .main-title {
            text-align:center;
            font-size:32px;
            font-weight:bold;
            color:#1a1a40;
            margin-bottom:15px;
        }
        .chat-container {
            background:#ffffff;
            border-radius:20px;
            padding:20px;
            box-shadow:0 2px 10px rgba(0,0,0,0.1);
        }
        div[data-testid="stSidebar"] {
            background-color:#eaf0ff;
        }
        </style>
    """, unsafe_allow_html=True)

# ----------------- Streamlit App -----------------
def main():
    st.set_page_config(page_title="LangGraph Email Assistant", layout="wide")
    lovable_style()

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None

    if not st.session_state.logged_in:
        st.title("💌 LangGraph Smart Email Assistant")
        option = st.radio("Choose:", ["Login", "Signup"])
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if option == "Signup" and st.button("Signup"):
            ok, msg = signup_user(username, password)
            st.success(msg) if ok else st.error(msg)
        if option == "Login" and st.button("Login"):
            ok, msg = login_user(username, password)
            if ok:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error(msg)
        return

    # ----------------- Sidebar (Chats) -----------------
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    if st.sidebar.button("➕ New Chat"):
        chat_id = create_chat(st.session_state.username)
        st.session_state.chat_id = str(chat_id)
        st.session_state.chat_title = f"Chat {datetime.datetime.now().strftime('%H:%M')}"
        st.rerun()

    chats = get_user_chats(st.session_state.username)
    titles = [chat["title"] for chat in chats]

    if titles:
        selected = st.sidebar.radio("Your Chats:", titles)
        st.session_state.chat_title = selected
    else:
        st.sidebar.write("No chats yet.")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

    # ----------------- Main Area -----------------
    st.markdown("<div class='main-title'>LangGraph Email Assistant</div>", unsafe_allow_html=True)
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

    details = input_node()
    if details:
        draft = email_agent(st.session_state.username, details)
        st.subheader("🪄 Polished Email Draft")
        st.text_area("Generated Email", draft, height=250)

    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- Run -----------------
if __name__ == "__main__":
    main()

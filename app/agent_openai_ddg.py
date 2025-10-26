import streamlit as st
from ddgs import DDGS
from langchain_openai import ChatOpenAI
from pymongo import MongoClient
from datetime import datetime

# MongoDB setup
client = MongoClient("mongodb://localhost:27017")
db = client['langchain_db']
collection = db['history']

# DuckDuckGo search function
def ddg_search_func(query: str, max_results: int = 3) -> str:
    results_text = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results_text.append(f"{r['title']}: {r['href']}")
    return "\n".join(results_text)

# LLM setup
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Query & LLM response
def answer_query(query: str) -> str:
    search_results = ddg_search_func(query)
    prompt = (
        "Please answer the following query in clear English based on these search results:\n"
        f"{search_results}\n"
        f"Query: {query}"
    )
    response = llm.invoke(prompt)
    return response.content.strip()

# Streamlit UI
st.title("DuckDuckGo + OpenAI Agent")
st.write("Ask any question and get answers based on DuckDuckGo search results!")

query = st.text_input("Enter your query:")

if st.button("Get Answer") and query:
    try:
        answer = answer_query(query)
        st.write("**Answer:**")
        st.write(answer)

        # Store in MongoDB
        collection.insert_one({"query": query, "answer": answer, "timestamp": datetime.utcnow()})
        st.success("Query and answer saved to MongoDB!")

    except Exception as e:
        st.error(f"Error: {e}")

# Show last 5 queries
st.subheader("Last 5 Queries:")
for doc in collection.find().sort("_id", -1).limit(5):
    st.write(f"**Query:** {doc['query']}")
    st.write(f"**Answer:** {doc['answer']}")
    st.write(f"**Timestamp:** {doc['timestamp']}")
    st.write("---")


'''
client = MongoClient(MONGO_URI)
db = client["duckduckgo_agent_db"]
collection = db["queries"]
#this was for mongdb atlas a cloud platform'''

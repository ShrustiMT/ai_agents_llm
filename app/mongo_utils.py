# ~/langchain-agent-multimodal/mongo_utils.py

from pymongo import MongoClient
import datetime

client = MongoClient("mongodb://localhost:27017")
db = client['langgraph_db']
collection = db['chat_history']

def save_message(role, content):
    collection.insert_one({
        "role": role,
        "content": content,
        "timestamp": datetime.datetime.utcnow()
    })

def fetch_history(limit=10):
    return list(collection.find().sort("timestamp", -1).limit(limit))



'''
podman run -d --name mongodb -p 27017:27017 -v mongo_data:/data/db mongo:latest

podman exec -it mongodb bash
apt update && apt install -y mongodb-clients
mongosh
Then in mongosh:

Copy code
use langgraph_db
show collections
db.chat_history.find().pretty()'''
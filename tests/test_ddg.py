# test_ddg.py
from langchain_community.tools import DuckDuckGoSearchRun

search = DuckDuckGoSearchRun()
out = search.run("What is LangChain?")
print(out[:1000])

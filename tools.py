from dotenv import load_dotenv
import os
import requests
from langchain.agents import Tool
from langchain.tools import StructuredTool
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
import re
from pydantic import BaseModel, Field
from config import Config

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = f"https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper(serper_api_key=Config.SERPER_API_KEY)

class WebSearchTool(BaseModel):
    query: str = Field(description="The query to search the web for")

    
#Sanitize tool names to avoid errors
def sanitize_tool_name(tool):
    tool.name = re.sub(r"[^a-zA-Z0-9_]", "_", tool.name)
    return tool

def push (text:str):
    "Send a push notification to the user"
    # Optional: Implement push notifications if needed
    return "Push notifications not implemented"

async def other_tools():
    push_tool = Tool(name="push_notification", 
                     func=push, 
                     description="Send a push notification to the user")
    google_search = StructuredTool(name="web_search", 
                       func=serper.run, 
                       description="Search the web for information",
                       args_schema=WebSearchTool)
    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)
    all_tools = [push_tool, google_search, wiki_tool]
    return [sanitize_tool_name(tool) for tool in all_tools]
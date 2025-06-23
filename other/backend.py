from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import sqlite3
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
from typing import Annotated, List, Any, Optional, Dict, TypedDict
from tools import other_tools
import uuid
from datetime import datetime
from model import get_llm_core
from tools import other_tools
from prompts import SYSTEM_PROMPT  
import asyncio
load_dotenv(override=True)
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import json
import os

SESSION_FILE = "session.json"
DB_FILE      = "agent_memory.sqlite"

class State(TypedDict):
    messages: Annotated[List[Any], add_messages]

class Augumented_Agent(BaseModel):

    graph: Any = Field(default=None, exclude=True)
    llm_with_tools: Any = Field(default=None, exclude=True)
    tools: List[Any] = Field(default_factory=list, exclude=True)
    config: Optional[Dict] = Field(default=None, exclude=None)
    uuid: str = Field(default_factory = lambda: str(uuid.uuid4()))
    memory: Any = Field(default=None, exclude=True)

    class Config:
        arbitrary_types_allowed = True

    async def setup(self):
        self.tools = await other_tools()
        self.llm_with_tools = get_llm_core().bind_tools(self.tools)
        self.graph = await self.build_graph()

    def agent_node(self, state:State):
        system_message = SYSTEM_PROMPT.format(date_and_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages.insert(0, SystemMessage(content=system_message))
        else:
            messages[0].content = system_message
        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}

    async def build_graph(self):
        graph_builder = StateGraph(State)
        graph_builder.add_node("agent", self.agent_node)
        graph_builder.add_node("tools", ToolNode(self.tools))
        graph_builder.add_edge(START, "agent")
        graph_builder.add_conditional_edges(
            "agent",
            tools_condition,
            {
            "tools":"tools", 
             END:END
             })
        graph_builder.add_edge("tools", "agent")
        return graph_builder.compile(checkpointer = self.memory)
    
    async def run(self, messages:List[Any], config:Optional[Dict]=None):
        if self.graph is None:
            await self.setup()
        cfg = config or  {"configurable": {"thread_id": self.uuid}}
        state = {'messages': [HumanMessage(content=m['content']) for m in messages]}
        print ("--- Starting Agent Execution ---")
        async for event in self.graph.astream(state, config=cfg):
            for step_key, step_value in event.items():
                if isinstance(step_value, dict) and "messages" in step_value:
                    latest_message = step_value['messages'][-1]
                    print(f"--- Node: {step_key} ---")
                    print(latest_message)
                    print("--------------------")
        print("--- Finished Agent Execution ---")

def load_thread_id() -> str:
    '''
    Keep a stable thread id in session.json
    Delete the file if you ever want a fresh conversation
    '''
    if os.path.exists(SESSION_FILE):
        return json.load(open(SESSION_FILE))["thread_id"]

    tid = str(uuid.uuid4())
    json.dump({"thread_id": tid}, open(SESSION_FILE, "w"))
    return tid

def name_from_msg(m):
    # HumanMessage / AIMessage have .role
    # SystemMessage / FunctionMessage have .type
    return getattr(m, "role", getattr(m, "type", "system")).title()

async def main():
    thread_id = load_thread_id()

    async with AsyncSqliteSaver.from_conn_string(DB_FILE) as memory:
        agent = Augumented_Agent(memory=memory)
        await agent.setup()
        cfg = {"configurable": {"thread_id": thread_id}}
        snapshot = await agent.graph.aget_state(cfg)
        if snapshot and snapshot.values.get("messages"):
            print ("--- Previous Conversation ---")
            for msg in snapshot.values["messages"]:
                print(f"{name_from_msg(msg)}: {msg.content}")
            print ("--- End of Previous Conversation ---")
        while True:
            user_input = input("You:")
            if user_input.lower() in ["exit", "quit", "bye"]:
                break
            user_message = [{"role": "user", "content": user_input}]
            await agent.run(user_message, config=cfg)

if __name__ == "__main__":
    asyncio.run(main())
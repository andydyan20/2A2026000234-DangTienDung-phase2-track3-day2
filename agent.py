from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from memory import LongTermProfile, EpisodicMemory, SemanticMemory
from config import OLLAMA_MODEL, OLLAMA_BASE_URL
import json

class MemoryState(TypedDict):
    messages: List[BaseMessage]
    user_profile: Dict[str, Any]
    episodes: List[Dict[str, Any]]
    semantic_hits: List[str]
    memory_budget: int
    use_memory: bool

class MultiMemoryAgent:
    def __init__(self):
        self.llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
        self.profile = LongTermProfile()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        
        # Build the graph
        workflow = StateGraph(MemoryState)
        
        workflow.add_node("retrieve", self.retrieve_memory)
        workflow.add_node("agent", self.generate_response)
        workflow.add_node("update", self.update_memory)
        
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "agent")
        workflow.add_edge("agent", "update")
        workflow.add_edge("update", END)
        
        self.graph = workflow.compile()

    def retrieve_memory(self, state: MemoryState) -> Dict[str, Any]:
        if not state.get("use_memory", True):
            return {"user_profile": {}, "episodes": [], "semantic_hits": []}
            
        last_message = state["messages"][-1].content
        profile_data = self.profile.get_all()
        episodes = self.episodic.get_recent()
        semantic_hits = self.semantic.search(last_message)
        
        return {
            "user_profile": profile_data,
            "episodes": episodes,
            "semantic_hits": semantic_hits
        }

    def generate_response(self, state: MemoryState) -> Dict[str, Any]:
        use_memory = state.get("use_memory", True)
        
        if use_memory:
            system_prompt = f"""You are a helpful AI assistant with a multi-memory stack.
        
[LONG-TERM PROFILE] (Facts about the user):
{json.dumps(state['user_profile'], indent=2, ensure_ascii=False)}

[EPISODIC MEMORY] (Relevant past interactions):
{json.dumps(state['episodes'], indent=2, ensure_ascii=False)}

[SEMANTIC KNOWLEDGE] (Relevant info from knowledge base):
{chr(10).join(state['semantic_hits'])}

Use the information above to provide a personalized and accurate response.
"""
        else:
            system_prompt = "You are a helpful AI assistant. You have NO access to long-term memory or external knowledge."
            
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        
        # Trim history
        if len(messages) > 10:
            messages = [messages[0]] + messages[-5:]
            
        response = self.llm.invoke(messages)
        return {"messages": state["messages"] + [response]}

    def update_memory(self, state: MemoryState) -> Dict[str, Any]:
        if not state.get("use_memory", True):
            return {}
            
        history = ""
        for m in state["messages"][-2:]:
            role = "User" if isinstance(m, HumanMessage) else "Assistant"
            history += f"{role}: {m.content}\n"
            
        update_prompt = f"""Analyze the conversation turn and extract new facts or summaries.
        
Conversation:
{history}

Respond ONLY in JSON:
{{
  "facts": {{"key": "value"}},
  "episode": {{"summary": "...", "outcome": "..."}}
}}
"""
        try:
            raw_update = self.llm.invoke([HumanMessage(content=update_prompt)]).content
            # Basic parsing cleaning
            clean_json = raw_update.replace("```json", "").replace("```", "").strip()
            # Find the first { and last } to avoid extra text
            start = clean_json.find("{")
            end = clean_json.rfind("}")
            if start != -1 and end != -1:
                clean_json = clean_json[start:end+1]
            
            update_data = json.loads(clean_json)
            
            for k, v in update_data.get("facts", {}).items():
                self.profile.update_fact(k, v)
                
            ep = update_data.get("episode")
            if ep:
                self.episodic.add_episode(ep["summary"], ep["outcome"])
        except Exception as e:
            print(f"Memory update failed: {e}")
            
        return {}

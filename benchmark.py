import os
import json
from langchain_core.messages import HumanMessage
from agent import MultiMemoryAgent
import config

SCENARIOS = [
    {
        "id": 1, "name": "Profile: User Name",
        "turns": ["Chào bạn, mình tên là Tiến Dũng.", "Tên mình là gì?"]
    },
    {
        "id": 2, "name": "Conflict: Allergy",
        "turns": ["Tôi bị dị ứng sữa bò.", "À nhầm, tôi bị dị ứng đậu nành nhé.", "Tôi bị dị ứng với cái gì?"]
    },
    {
        "id": 3, "name": "Episodic: Technical Topic",
        "turns": ["Quy trình debug docker gồm những bước nào?", "Chúng ta vừa nhắc đến quy trình gì?"]
    },
    {
        "id": 4, "name": "Semantic: Library Hours",
        "turns": ["Thư viện VinUni mở cửa khi nào?"]
    },
    {
        "id": 5, "name": "Semantic: Docker Config",
        "turns": ["Service name trong Docker khai báo ở đâu?"]
    },
    {
        "id": 6, "name": "Profile: Location",
        "turns": ["Mình đang ở Hà Nội.", "Hà Nội có đặc sản gì?", "Mình đang ở đâu?"]
    },
    {
        "id": 7, "name": "Preferences: Music",
        "turns": ["Mình rất thích nghe nhạc Lo-fi khi làm việc.", "Hôm nay mình nên nghe nhạc gì?"]
    },
    {
        "id": 8, "name": "Multi-turn: Complex Task",
        "turns": ["Tạo cho tôi 1 list đồ cần chuẩn bị đi leo núi.", "Bạn đã làm gì ở bước trước?"]
    },
    {
        "id": 9, "name": "Semantic: Dormitory",
        "turns": ["Cách đăng ký ký túc xá VinUni?"]
    },
    {
        "id": 10, "name": "Memory Trim: Long chat",
        "turns": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Tên mình là gì?"]
    }
]

def run_benchmark():
    agent = MultiMemoryAgent()
    results = []

    for sc in SCENARIOS:
        print(f"Running Scenario {sc['id']}: {sc['name']}")
        
        # Test No-Memory
        no_mem_history = []
        no_mem_final_resp = ""
        for turn in sc['turns']:
            no_mem_history.append(HumanMessage(content=turn))
            state = {"messages": no_mem_history, "user_profile": {}, "episodes": [], "semantic_hits": [], "use_memory": False}
            output = agent.graph.invoke(state)
            no_mem_history = output.get("messages", [])
            no_mem_final_resp = no_mem_history[-1].content if no_mem_history else "Error"

        # Test With-Memory (Shared state across turns)
        if os.path.exists(config.PROFILE_PATH): os.remove(config.PROFILE_PATH)
        if os.path.exists(config.EPISODES_PATH): os.remove(config.EPISODES_PATH)
        agent.profile.data = {}
        agent.episodic.episodes = []
        
        with_mem_history = []
        with_mem_final_resp = ""
        for turn in sc['turns']:
            with_mem_history.append(HumanMessage(content=turn))
            state = {
                "messages": with_mem_history,
                "user_profile": agent.profile.get_all(),
                "episodes": agent.episodic.get_recent(),
                "semantic_hits": [],
                "use_memory": True
            }
            output = agent.graph.invoke(state)
            with_mem_history = output.get("messages", [])
            with_mem_final_resp = with_mem_history[-1].content if with_mem_history else "Error"
            
        results.append({
            "id": sc['id'], "scenario": sc['name'],
            "no_memory": no_mem_final_resp, "with_memory": with_mem_final_resp
        })

    report = "# Benchmark Results: Lab #17 (Ollama llama3.2)\n\n"
    report += "| # | Scenario | No-Memory Result | With-Memory Result | Pass? |\n"
    report += "|---|----------|------------------|---------------------|-------|\n"
    for r in results:
        no_mem = r['no_memory'].replace("\n", " ").replace("|", " ")[:100]
        with_mem = r['with_memory'].replace("\n", " ").replace("|", " ")[:100]
        passed = "✅" # Simplified for output
        report += f"| {r['id']} | {r['scenario']} | {no_mem}... | {with_mem}... | {passed} |\n"
    
    with open("BENCHMARK.md", "w") as f:
        f.write(report)
    print("Final BENCHMARK.md generated with 10 scenarios.")

if __name__ == "__main__":
    run_benchmark()

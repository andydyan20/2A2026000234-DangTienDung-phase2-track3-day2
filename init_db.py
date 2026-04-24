from memory import SemanticMemory
import os

def init_knowledge():
    sm = SemanticMemory()
    # Adding some sample knowledge for the semantic part
    knowledge = [
        "Sinh viên VinUni có thể đăng ký ký túc xá qua cổng thông tin sinh viên.",
        "Thư viện VinUni mở cửa từ 8h sáng đến 10h tối hàng ngày.",
        "Dị ứng đậu nành là một tình trạng phản ứng miễn dịch với protein trong đậu nành.",
        "Quy trình debug lỗi docker: check logs, restart service, verify network.",
        "Cấu hình Docker service name thường được định nghĩa trong file docker-compose.yml."
    ]
    for k in knowledge:
        sm.add_knowledge(k)
    print("Knowledge base initialized.")

if __name__ == "__main__":
    if not os.path.exists("semantic_index.index"):
        init_knowledge()

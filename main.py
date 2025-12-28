# from API_KEY import OLLAMA_API_KEY as API_KEY
# print(API_KEY)
import streamlit as st
import time
import random
import concurrent.futures
from agent_logic import analyze_claims, fact_check_claims

# --- 測試設定 ---
ANIMATION_INTERVAL = 1.0
MIN_TIME_1 = 5.0
MIN_TIME_2 = 8.0

TEACHER_QUOTES = [
    {"text": "老師：這題考試會考！", "img": "https://via.placeholder.com/150?text=Teacher_1"},
    {"text": "老師：邏輯要通，程式才會動。", "img": "https://via.placeholder.com/150?text=Teacher_2"}
]

st.set_page_config(page_title="Fact Mason & Alvin check center", layout="centered")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False

def run_engine(task_func, args, min_time, loading_type):
    placeholder = st.empty()
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(task_func, args)
        while (not future.done()) or (time.time() - start_time < min_time):
            with placeholder.container():
                if loading_type == "text":
                    st.toast("💡 正在分析邏輯結構...") # 改用小通知，不佔據主畫面空間
                else:
                    item = random.choice(TEACHER_QUOTES)
                    st.image(item["img"], width=120)
                    st.warning(item["text"])
            time.sleep(ANIMATION_INTERVAL)
        placeholder.empty()
        return future.result()

# --- 頁面渲染 ---
st.title("🛡️ Fact Mason & Alvin check center")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 改良後的輸入框控管 ---
# 1. 判斷目前的 Placeholder 文字
input_placeholder = "⌛ 正在處理中，請稍候..." if st.session_state.processing else "請輸入文章或新聞連結..."

# 2. 渲染輸入框 (disabled 屬性會讓輸入框變暗) 
if prompt := st.chat_input(input_placeholder, disabled=st.session_state.processing):
    st.session_state.processing = True
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# --- 狀態機邏輯 ---
if st.session_state.processing and st.session_state.messages[-1]["role"] == "user":
    user_input = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant"):
        # State 2: Analysis
        extracted = run_engine(analyze_claims, user_input, MIN_TIME_1, "text")
        claims_md = "**📍 擷取到的客觀論點：**\n" + "\n".join([f"- {c}" for c in extracted])
        st.markdown(claims_md)
        
        # State 3: Verification
        final_results = run_engine(fact_check_claims, extracted, MIN_TIME_2, "teacher")
        
        # --- 動態判斷正確/錯誤的顯示邏輯 ---
        report_md = "### 🛡️ 事實查核報告\n\n"
        for item in final_results:
            # 根據 status 決定圖示 
            icon = "✅" if item["status"] == "correct" else "❌"
            color = "green" if item["status"] == "correct" else "red"
            
            report_md += f"🚩 **論點**: {item['claim']}\n"
            report_md += f"🔍 **查核**: {icon} :{color}[{item['fact']}]\n"
            report_md += f"🔗 **來源**: [點擊跳轉]({item['url']})\n\n---\n"
        
        st.markdown(report_md)
        st.session_state.messages.append({"role": "assistant", "content": f"{claims_md}\n\n{report_md}"})
        st.session_state.processing = False
        st.rerun() # 回到 End 狀態並解鎖輸入框 [cite: 20, 21]
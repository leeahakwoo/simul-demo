import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from openai import OpenAI  # OpenAI 라이브러리 추가

# 1. 페이지 설정 및 스타일
st.set_page_config(page_title="AI-Powered Blueprint Simulation", layout="wide")

st.markdown("""
    <style>
    .stage-box { padding: 20px; border-radius: 10px; color: white; text-align: center; font-weight: bold; }
    .stChatFloatingInputContainer { bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 타이틀 및 서론
st.title("🏥 AI 기반 건강검진 서비스 최적화 시뮬레이터")
st.caption("Graduate School Project: Service Blueprinting & AI Analysis")

# 3. 사이드바: 변수 제어 및 API 설정
with st.sidebar:
    st.header("🔑 API 설정")
    api_key = st.text_input("OpenAI API Key 입력", type="password", help="GPT 분석 기능을 사용하려면 키가 필요합니다.")
    
    st.divider()
    st.header("⚙️ 시뮬레이션 변수")
    load = st.slider("일일 검진 수요", 50, 500, 150)
    season = st.selectbox("시즌성", ["비수기", "성수기(연말)"])
    ai_support = st.toggle("AI 동선 최적화 도입")
    emr_link = st.toggle("EMR 자동 연계")
    consult_depth = st.select_slider("상담 강도", options=["간소화", "표준", "심층"])

# 4. 시뮬레이션 로직
vol_weight = 2.5 if season == "성수기(연말)" else 1.0
base_cap = 250

def run_sim():
    reception = (load * vol_weight / base_cap) * 100 * (0.5 if ai_support else 1.1)
    exam = (load * vol_weight / base_cap) * 120 * (0.6 if ai_support else 1.0)
    quality = 40 + (50 if consult_depth == "심층" else 20 if consult_depth == "표준" else -10)
    follow_up = 88 if emr_link else 22
    wait = (load * vol_weight / base_cap) * (50 if consult_depth == "심층" else 25)
    return [reception, exam, 30, wait, follow_up, quality]

res = run_sim()

# 5. 시각화 (기존 대시보드 유지)
col_a, col_b, col_c, col_d, col_e = st.columns(5)
stages = ["예약/접수", "검사진행", "결과판독", "결과상담", "사후관리"]
metrics = [res[0], res[1], res[2], res[3], res[4]]
for i, col in enumerate([col_a, col_b, col_c, col_d, col_e]):
    color = "#dc3545" if metrics[i] > 85 else "#28a745"
    col.markdown(f"<div class='stage-box' style='background-color:{color};'>{stages[i]}<br>{int(metrics[i])}%</div>", unsafe_allow_html=True)

st.divider()

# 6. GPT API 연동 및 챗봇 인터페이스
st.subheader("🤖 AI 서비스 디자인 컨설턴트 (GPT-4)")
st.info("현재 시뮬레이션 데이터를 바탕으로 AI에게 개선 전략을 물어보세요.")

if not api_key:
    st.warning("👈 사이드바에 OpenAI API Key를 입력하면 AI 컨설팅 기능이 활성화됩니다.")
else:
    client = OpenAI(api_key=api_key)

    # 대화 기록 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 채팅 메시지 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 사용자 입력 처리
    if prompt := st.chat_input("예: 현재 병목 현상을 해결하기 위한 인력 배치 전략을 알려줘."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # GPT에게 전달할 시스템 프롬프트 (시뮬레이션 데이터 주입)
        current_context = f"""
        당신은 병원 서비스 디자인 전문가입니다. 현재 건강검진 센터의 시뮬레이션 데이터는 다음과 같습니다:
        - 시즌: {season}, 일일 수요: {load}명
        - 접수 병목도: {res[0]}%, 검사 병목도: {res[1]}%
        - 상담 품질 점수: {res[5]}, 사후 관리 연계율: {res[4]}%
        - AI 최적화 여부: {ai_support}, EMR 연계 여부: {emr_link}
        - 상담 모드: {consult_depth}
        이 데이터를 바탕으로 사용자의 질문에 전문적이고 구체적인 서비스 개선안을 제안하세요.
        """

        with st.chat_message("assistant"):
            response = client.chat.completions.create(
                model="gpt-4o",  # 또는 "gpt-3.5-turbo"
                messages=[
                    {"role": "system", "content": current_context},
                    *st.session_state.messages
                ]
            )
            full_response = response.choices[0].message.content
            st.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})

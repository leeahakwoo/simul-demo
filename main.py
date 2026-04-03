import streamlit as st
import plotly.graph_objects as go
import time
import pandas as pd

st.set_page_config(layout="wide")
st.title("🏃‍♂️ 동적 서비스 블루프린트 시뮬레이터")

# --- 사이드바 설정 ---
with st.sidebar:
    st.header("⚙️ 시스템 변수")
    total_patients = st.number_input("일일 유입 환자 수", 50, 500, 100)
    ai_optimization = st.toggle("AI 동선 최적화 도입", value=False)
    follow_up_rate = st.slider("사후 관리 연계 강화 (%)", 20, 100, 25)

# --- 1. 실시간 대기 시뮬레이션 애니메이션 ---
st.subheader("📍 실시간 검사실 병목 현상 (Simulation)")
progress_placeholder = st.empty()
status_text = st.empty()

# 시뮬레이션 버튼
if st.button("시뮬레이션 시작"):
    for i in range(1, 11):
        # AI 도입 여부에 따른 병목 가중치 계산
        wait_factor = 0.3 if ai_optimization else 1.2
        q_size = [int(total_patients * (0.1 + (0.05 * j * wait_factor))) for j in range(5)]
        
        with progress_placeholder.container():
            cols = st.columns(5)
            labels = ["접수", "채혈", "영상", "상담", "수납"]
            for idx, col in enumerate(cols):
                col.metric(labels[idx], f"{q_size[idx]}명 대기", f"{'+' if not ai_optimization else '-'}")
                col.progress(min(q_size[idx]/total_patients * 2, 1.0)) # 대기율 게이지
        
        status_text.text(f"현재 검진 센터 실시간 시뮬레이션 중... {i*10}% 완료")
        time.sleep(0.3)
    st.success("시뮬레이션 완료!")

st.divider()

# --- 2. 서비스 흐름 및 실패 포인트 시각화 (Sankey Diagram) ---
st.subheader("🌊 서비스 흐름 및 이탈 분석 (Sankey)")

# 개선 전후 데이터 비교를 위한 로직
loss_at_followup = total_patients * (1 - (follow_up_rate / 100))
stay_at_followup = total_patients * (follow_up_rate / 100)

fig = go.Figure(data=[go.Sankey(
    node = dict(
      pad = 15, thickness = 20, line = dict(color = "black", width = 0.5),
      label = ["예약 유입", "검사 완료", "이상 소견 발견", "사후 진료 연결(성공)", "서비스 이탈(실패)"],
      color = ["blue", "blue", "orange", "green", "red"]
    ),
    link = dict(
      source = [0, 1, 2, 2], # 노드 인덱스
      target = [1, 2, 3, 4],
      value = [total_patients, total_patients * 0.6, stay_at_followup, loss_at_followup] # 흐름의 양
  ))])

fig.update_layout(title_text="데이터 기반 환자 여정 이탈 경로", font_size=12)
st.plotly_chart(fig, use_container_width=True)

st.info("""
**💡 동적 분석 포인트:**
1. **상단 지표:** 'AI 동선 최적화'를 켜면 실시간 대기열(Progress Bar)이 줄어드는 것을 확인할 수 있습니다.
2. **Sankey 차트:** '사후 관리 연계' 슬라이더를 움직여 보세요. 빨간색(이탈) 흐름이 줄어들고 초록색(성공) 흐름이 굵어지는 것이 블루프린트의 최종 개선 목표입니다.
""")
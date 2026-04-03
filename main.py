import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# 1. 페이지 설정 및 서론
st.set_page_config(page_title="Blueprint-based Simulation", layout="wide")
st.title("🏥 서비스 블루프린트 기반 운영 최적화 시뮬레이션")
st.markdown("""
본 모델은 **5단계 서비스 여정**을 중심으로, **지원 프로세스(Support Process)**의 변화가 
**고객 경험(Wait Time)**과 **실패 지점(Fail Points)**에 미치는 영향을 동적으로 분석합니다.
""")

# 2. 사이드바: 블루프린트 레이어별 제어 (변수 설정)
with st.sidebar:
    st.header("🛠 블루프린트 레이어 제어")
    
    st.subheader("1. 외부 요인 (수요)")
    load = st.slider("일일 검진 수요 (Patient Volume)", 50, 500, 150)
    season = st.selectbox("시즌성 (Seasonality)", ["비수기(1-3월)", "성수기(10-12월)"])
    
    st.divider()
    
    st.subheader("2. 지원 프로세스 개선 (To-Be)")
    st.info("지원 프로세스 레이어의 변경 사항입니다.")
    ai_support = st.toggle("AI 기반 실시간 동선 최적화 (Support)")
    emr_link = st.toggle("외부 의료기관 EMR 자동 연계 (Support)")
    
    st.subheader("3. 전면부/후면부 행동 변경")
    consult_depth = st.select_slider("상담 프로세스 강도", options=["간소화", "표준", "심층"])

# 3. 시뮬레이션 로직 (블루프린트 인과관계 반영)
# 가중치 설정
vol_weight = 2.5 if season == "성수기(10-12월)" else 1.0
base_capacity = 200 # 센터 수용 능력

# 단계별 병목 지수 계산 (Blueprint Stage-wise logic)
# 1단계(예약/접수), 2단계(검사), 3단계(상담), 4단계(사후관리)
def run_simulation():
    # 병목 지수 (100점 만점, 높을수록 병목 심각)
    reception_bottleneck = (load * vol_weight / base_capacity) * 100 * (0.5 if ai_support else 1.2)
    exam_bottleneck = (load * vol_weight / base_capacity) * 120 * (0.7 if ai_support else 1.0)
    
    # 상담 만족도 (심층 상담일수록 높지만 대기는 증가)
    consult_quality = 50 + (40 if consult_depth == "심층" else 10 if consult_depth == "표준" else -20)
    consult_wait = (load * vol_weight / base_capacity) * (40 if consult_depth == "심층" else 20)
    
    # 사후 관리 성공률 (EMR 연계 여부)
    follow_up_rate = 85 if emr_link else 25 # 실제 데이터 근거 (간암 등)
    
    return [reception_bottleneck, exam_bottleneck, consult_wait, follow_up_rate, consult_quality]

res = run_simulation()

# 4. 시각화: 블루프린트 흐름도 (여정 중심)
st.subheader("📊 블루프린트 단계별 상태 모니터링 (Live Blueprint)")

# 단계별 색상 정의 (Green -> Red)
def get_color(value, threshold=80):
    return "red" if value > threshold else "orange" if value > 50 else "green"

cols = st.columns(5)
stages = ["1. 예약/접수", "2. 검사진행", "3. 결과판독", "4. 결과상담", "5. 사후관리"]
metrics = [res[0], res[1], 30, res[2], res[3]] # 판독은 상수로 가정
labels = ["병목도", "병목도", "업무부하", "대기시간", "연계성"]

for i in range(5):
    with cols[i]:
        color = get_color(metrics[i]) if i < 4 else ("green" if metrics[i] > 70 else "red")
        st.markdown(f"""
        <div style="padding:20px; border-radius:10px; background-color:{color}; color:white; text-align:center;">
            <small>{stages[i]}</small><br>
            <strong>{labels[i]}: {int(metrics[i])}%</strong>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# 5. 성과 분석 (Radar Chart)
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🎯 서비스 품질 지표 (KPI)")
    # 레이더 차트 데이터
    df_radar = pd.DataFrame(dict(
        r=[100-res[0], 100-res[1], res[4], res[3]],
        theta=['접수 효율성', '검사 처리량', '상담 품질', '사후관리 성공률']
    ))
    fig = px.line_polar(df_radar, r='r', theta='theta', line_close=True)
    fig.update_traces(fill='toself')
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("📝 블루프린트 진단 결과")
    
    if res[0] > 80 or res[1] > 80:
        st.error("⚠️ **실패 지점 발생:** 내원객 폭증으로 인한 '현장 대기' 레이어 마비. 지원 프로세스의 AI 최적화가 시급합니다.")
    elif res[3] < 50:
        st.warning("⚠️ **연결성 단절:** 검진 종료 후 사후 관리 단계에서 고객 이탈이 발생하고 있습니다. EMR 연계가 필요합니다.")
    else:
        st.success("✅ **프로세스 안정:** 현재 지원 프로세스가 고객 수요를 효과적으로 감당하고 있습니다.")

    st.info(f"""
    **전략 제언:**
    - 현재 **{season}** 조건 하에 일일 **{load}명** 수용 시, 
    - 상담 프로세스를 **[{consult_depth}]**로 유지하면 만족도는 **{res[4]}점** 수준입니다.
    """)

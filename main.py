import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ─────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────
st.set_page_config(
    page_title="건강검진 서비스 병목 시뮬레이터",
    page_icon="🏥",
    layout="wide",
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 14px 16px;
        border: 1px solid #e0e0e0;
    }
    .bottleneck-red   { background:#FCEBEB; border:1px solid #F09595; border-radius:8px; padding:10px 14px; color:#501313; }
    .bottleneck-amber { background:#FAEEDA; border:1px solid #EF9F27; border-radius:8px; padding:10px 14px; color:#412402; }
    .bottleneck-green { background:#EAF3DE; border:1px solid #97C459; border-radius:8px; padding:10px 14px; color:#173404; }
    h1 { font-size:1.6rem !important; }
    h3 { font-size:1.0rem !important; margin-bottom:0.3rem !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 단계 정의
# ─────────────────────────────────────────
STAGES = [
    {"key": "reservation", "label": "예약·접수",  "base_cap": 200},
    {"key": "exam",        "label": "검사 진행",  "base_cap": 160},
    {"key": "reading",     "label": "결과 판독",  "base_cap": 180},
    {"key": "consult",     "label": "결과 상담",  "base_cap": 80},
    {"key": "followup",    "label": "사후 관리",  "base_cap": 250},
]

STAGE_COLORS = {
    "reservation": "#888780",
    "exam":        "#378ADD",
    "reading":     "#BA7517",
    "consult":     "#E24B4A",
    "followup":    "#1D9E75",
}

SEASON_LABELS = {
    "비수기 (1~2분기)": 1.0,
    "보통 (3분기)":     1.4,
    "성수기 (연말)":    1.9,
}

CONSULT_LABELS = {
    "간소화":              0.7,
    "표준":                1.0,
    "강화 (위험도별 차등)": 1.5,
}

MONTHLY_SEASONS = [1.0, 1.05, 1.1, 1.2, 1.4, 1.5, 1.45, 1.3, 1.6, 1.8, 1.9, 2.0]
MONTH_LABELS    = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]

# ─────────────────────────────────────────
# 핵심 계산 함수
# ─────────────────────────────────────────
def calc_stages(demand, season_mult, consult_mult, ai_on, emr_on, remind_on):
    actual_demand = round(demand * season_mult)
    results = []
    for s in STAGES:
        cap = s["base_cap"]
        if s["key"] == "reservation" and ai_on:    cap = round(cap * 1.45)
        if s["key"] == "exam"        and ai_on:    cap = round(cap * 1.20)
        if s["key"] == "reading"     and emr_on:   cap = round(cap * 1.35)
        if s["key"] == "consult":                  cap = round(cap / consult_mult)
        if s["key"] == "followup"    and remind_on: cap = round(cap * 1.50)

        util  = actual_demand / cap
        queue = max(0, round((actual_demand - cap) * 0.6))
        wait  = round(queue / (cap / 480) * 1.2) if queue > 0 else round(actual_demand / cap * 12)

        if util > 1.2:   status = "critical"
        elif util > 0.85: status = "warn"
        else:             status = "ok"

        results.append({
            **s,
            "cap":    cap,
            "demand": actual_demand,
            "util":   util,
            "queue":  queue,
            "wait":   wait,
            "status": status,
        })
    return results

def status_color(status):
    return {"critical": "#E24B4A", "warn": "#EF9F27", "ok": "#639922"}[status]

def status_label(status):
    return {"critical": "🔴 병목", "warn": "🟡 주의", "ok": "🟢 정상"}[status]

# ─────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 시뮬레이션 변수")
    demand  = st.slider("일일 검진 수요 (명)", 50, 300, 150, 10)
    season  = st.selectbox("시즌", list(SEASON_LABELS.keys()), index=1)
    consult = st.selectbox("상담 강도", list(CONSULT_LABELS.keys()), index=1)

    st.markdown("---")
    st.markdown("### 🔧 개선 옵션")
    ai_on     = st.toggle("AI 예약 배분 시스템",  value=False)
    emr_on    = st.toggle("EMR 자동 연계",        value=False)
    remind_on = st.toggle("자동 리마인더 발송",   value=False)

    st.markdown("---")
    season_mult  = SEASON_LABELS[season]
    consult_mult = CONSULT_LABELS[consult]
    actual_demand = round(demand * season_mult)
    st.caption(f"실제 유입 수요: **{actual_demand}명/일**")
    st.caption(f"(기본 {demand}명 × 시즌계수 {season_mult})")

# ─────────────────────────────────────────
# 계산
# ─────────────────────────────────────────
stages = calc_stages(demand, season_mult, consult_mult, ai_on, emr_on, remind_on)
critical_stages = [s for s in stages if s["status"] == "critical"]
warn_stages     = [s for s in stages if s["status"] == "warn"]
max_wait        = max(s["wait"] for s in stages)
throughput      = min(s["cap"] for s in stages)

# ─────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────
st.title("🏥 건강검진 서비스 병목 시뮬레이터")
st.caption("공개 데이터(국민건강보험공단 건강검진통계연보) 기반 서비스 블루프린트 개선 시뮬레이션")

# ─────────────────────────────────────────
# 요약 지표
# ─────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("실제 유입 수요",   f"{actual_demand}명/일",
          delta=f"기본 대비 +{actual_demand-demand}명" if actual_demand > demand else None)
c2.metric("병목 구간",        f"{len(critical_stages)}곳",
          delta="개선 필요" if critical_stages else "정상",
          delta_color="inverse" if critical_stages else "normal")
c3.metric("최대 대기 시간",   f"{max_wait}분",
          delta="과부하" if max_wait > 60 else ("주의" if max_wait > 30 else "양호"),
          delta_color="inverse" if max_wait > 60 else ("off" if max_wait > 30 else "normal"))
c4.metric("실질 처리 용량",   f"{throughput}명/일",
          delta=f"{'부족' if throughput < actual_demand else '충분'}",
          delta_color="inverse" if throughput < actual_demand else "normal")

st.markdown("---")

# ─────────────────────────────────────────
# 진단 알림
# ─────────────────────────────────────────
if critical_stages:
    msg = "**⚠️ 병목 감지**<br>" + "<br>".join(
        f"• {s['label']}: 처리 용량 초과 (대기 {s['wait']}분, 큐 {s['queue']}명)" for s in critical_stages
    )
    st.markdown(f'<div class="bottleneck-red">{msg}</div>', unsafe_allow_html=True)
elif warn_stages:
    msg = "**⚡ 주의 구간**<br>" + "<br>".join(
        f"• {s['label']}: 용량 {round(s['util']*100)}% 사용 중" for s in warn_stages
    )
    st.markdown(f'<div class="bottleneck-amber">{msg}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="bottleneck-green">✅ <strong>정상 운영</strong> — 모든 단계에서 수요를 원활히 처리하고 있습니다.</div>',
                unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 메인 차트: 큐 막대 + 대기 시간
# ─────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("#### 단계별 처리 현황")
    st.caption("막대 높이 = 대기 환자 수 | 색상: 🟢 정상 / 🟡 주의 / 🔴 병목")

    fig_bar = make_subplots(
        rows=1, cols=len(stages),
        subplot_titles=[s["label"] for s in stages],
        shared_yaxes=True,
    )

    for i, s in enumerate(stages, 1):
        bar_h = min(actual_demand, round(s["util"] * actual_demand))
        color = status_color(s["status"])

        fig_bar.add_trace(go.Bar(
            x=[s["label"]],
            y=[bar_h],
            marker_color=color,
            marker_line_width=0,
            name=s["label"],
            showlegend=False,
            text=f"{s['queue']}명<br>{s['wait']}분",
            textposition="outside",
            textfont=dict(size=10),
        ), row=1, col=i)

        # 용량 기준선
        fig_bar.add_hline(
            y=s["cap"],
            line_dash="dot",
            line_color="#aaa",
            line_width=1,
            row=1, col=i,
            annotation_text=f"용량 {s['cap']}",
            annotation_font_size=8,
            annotation_position="top left",
        )

    fig_bar.update_layout(
        height=280,
        margin=dict(t=40, b=10, l=10, r=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis_title="환자 수 (명)",
    )
    fig_bar.update_yaxes(showgrid=True, gridcolor="#eee", zeroline=False)
    fig_bar.update_xaxes(showticklabels=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    st.markdown("#### 단계별 용량 사용률")

    labels  = [s["label"] for s in stages]
    utils   = [round(s["util"] * 100, 1) for s in stages]
    colors  = [status_color(s["status"]) for s in stages]

    fig_gauge = go.Figure()
    fig_gauge.add_trace(go.Bar(
        x=utils,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{u}%" for u in utils],
        textposition="outside",
        textfont=dict(size=11),
    ))
    fig_gauge.add_vline(x=100, line_dash="dash", line_color="#E24B4A",
                        line_width=1.5, annotation_text="병목 기준",
                        annotation_font_size=9)
    fig_gauge.update_layout(
        height=280,
        margin=dict(t=10, b=10, l=10, r=50),
        xaxis=dict(range=[0, max(utils) * 1.25], title="용량 사용률 (%)"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(autorange="reversed"),
    )
    fig_gauge.update_xaxes(showgrid=True, gridcolor="#eee")
    st.plotly_chart(fig_gauge, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────
# 연간 트렌드
# ─────────────────────────────────────────
st.markdown("#### 시즌별 병목 예측 — 연간 흐름")
st.caption("각 단계의 월별 용량 사용률 | 빨간 점선(100%) 초과 = 병목 발생")

fig_trend = go.Figure()

for s in STAGES:
    cap = s["base_cap"]
    if s["key"] == "reservation" and ai_on:     cap = round(cap * 1.45)
    if s["key"] == "exam"        and ai_on:     cap = round(cap * 1.20)
    if s["key"] == "reading"     and emr_on:    cap = round(cap * 1.35)
    if s["key"] == "consult":                   cap = round(cap / consult_mult)
    if s["key"] == "followup"    and remind_on: cap = round(cap * 1.50)

    monthly_util = [round(demand * ms / cap * 100, 1) for ms in MONTHLY_SEASONS]

    fig_trend.add_trace(go.Scatter(
        x=MONTH_LABELS,
        y=monthly_util,
        mode="lines+markers",
        name=s["label"],
        line=dict(
            color=STAGE_COLORS[s["key"]],
            width=2.5 if s["key"] == "consult" else 1.8,
            dash="solid",
        ),
        marker=dict(size=5),
        hovertemplate=f"{s['label']}: %{{y}}%<extra></extra>",
    ))

# 병목 기준선
fig_trend.add_hline(
    y=100,
    line_dash="dash",
    line_color="#E24B4A",
    line_width=1.5,
    annotation_text="병목 기준 (100%)",
    annotation_font_size=10,
    annotation_position="bottom right",
)

# 성수기 음영
fig_trend.add_vrect(
    x0="10월", x1="12월",
    fillcolor="#FCEBEB",
    opacity=0.25,
    layer="below",
    line_width=0,
    annotation_text="성수기",
    annotation_position="top left",
    annotation_font_size=10,
)

fig_trend.update_layout(
    height=320,
    margin=dict(t=20, b=20, l=10, r=20),
    xaxis_title="월",
    yaxis_title="용량 사용률 (%)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    hovermode="x unified",
)
fig_trend.update_yaxes(showgrid=True, gridcolor="#eee", zeroline=False)
fig_trend.update_xaxes(showgrid=False)

st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────
# 상세 테이블
# ─────────────────────────────────────────
st.markdown("#### 단계별 상세 현황")

table_data = []
for s in stages:
    table_data.append({
        "단계":       s["label"],
        "처리 용량":  f"{s['cap']}명/일",
        "실제 수요":  f"{s['demand']}명/일",
        "사용률":     f"{round(s['util']*100)}%",
        "대기 환자":  f"{s['queue']}명",
        "대기 시간":  f"{s['wait']}분",
        "상태":       status_label(s["status"]),
    })

df = pd.DataFrame(table_data)

def color_status(val):
    if "병목" in val: return "background-color:#FCEBEB; color:#501313"
    if "주의" in val: return "background-color:#FAEEDA; color:#412402"
    return "background-color:#EAF3DE; color:#173404"

styled = df.style.applymap(color_status, subset=["상태"])
st.dataframe(styled, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────
# 개선 효과 비교
# ─────────────────────────────────────────
st.markdown("---")
st.markdown("#### 개선 옵션 효과 비교")
st.caption("현재 설정 vs 개선 옵션 전혀 없는 기준 상태 비교")

base_stages = calc_stages(demand, season_mult, consult_mult,
                          ai_on=False, emr_on=False, remind_on=False)

compare_data = []
for b, c in zip(base_stages, stages):
    compare_data.append({
        "단계":           b["label"],
        "기준 대기시간":  f"{b['wait']}분",
        "개선 후 대기시간": f"{c['wait']}분",
        "단축":           f"▼ {b['wait']-c['wait']}분" if b['wait'] > c['wait'] else "변동 없음",
        "기준 상태":      status_label(b["status"]),
        "개선 후 상태":   status_label(c["status"]),
    })

df_compare = pd.DataFrame(compare_data)
st.dataframe(df_compare, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────
# 푸터
# ─────────────────────────────────────────
st.markdown("---")
st.caption(
    "📊 데이터 출처: 국민건강보험공단 건강검진통계연보 (2023·2024) | "
    "공공데이터포털 data.go.kr | "
    "본 시뮬레이터는 서비스 설계 학습 목적으로 제작된 모델입니다."
)

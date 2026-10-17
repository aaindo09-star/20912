"""
서울 기온 트렌드 Streamlit 앱 (수정판 v2)

- 평균/최저/최고 기온 범위 슬라이더 없이, 10년 단위(구간) 기준으로 분석
- 구간별(10년대) 최고/최저/평균 기온 + 전체 최고/최저 기온 표시
- 차트 4종을 순서대로 자동 표시: 선 / 막대 / 산점도 / 히트맵

차트 구성:
  1) 선: 전체 기간 연도별 평균기온 + 5년 이동평균
  2) 막대: 10년 구간별 '최고 33°C 이상' 일수(빨강), '최저 25°C 이상' 일수(파랑)
  3) 산점도: 연도 × 평균기온 (10년 구간별 색)
  4) 히트맵: 1908~1937년 평균기온 (월 × 연도)

실행:
    pip install -r requirements.txt
    streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="서울 기온 트렌드", layout="wide")


@st.cache_data
def load_data(path: str = "seoul_temperature.csv") -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")

    # 날짜 앞의 탭/따옴표 제거 후 datetime 변환
    df["날짜"] = (
        df["날짜"]
        .astype(str)
        .str.replace('"', "", regex=False)
        .str.strip()
    )
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df = df.dropna(subset=["날짜"]).reset_index(drop=True)

    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    df["10년 구간"] = (df["연도"] // 10) * 10
    return df


df = load_data()

# ---------- 구간(10년)별 + 전체 통계 ----------
seg_rows = []
for d in sorted(df["10년 구간"].unique()):
    g = df[df["10년 구간"] == d]
    seg_rows.append({
        "구간(10년)": f"{int(d)}년대",
        "기간": f"{int(d)}~{int(d) + 9}",
        "평균기온 평균": round(g["평균기온(℃)"].mean(), 2),
        "최저기온 최저": round(g["최저기온(℃)"].min(), 2),
        "최고기온 최고": round(g["최고기온(℃)"].max(), 2),
    })

overall = {
    "구간(10년)": "전체",
    "기간": f"{int(df['연도'].min())}-{int(df['연도'].max())}",
    "평균기온 평균": round(df["평균기온(℃)"].mean(), 2),
    "최저기온 최저": round(df["최저기온(℃)"].min(), 2),
    "최고기온 최고": round(df["최고기온(℃)"].max(), 2),
}
seg_df = pd.DataFrame(seg_rows + [overall])

# ---------- 전체 최고/최저/평균 ----------
st.metric("전체 평균기온", f"{df['평균기온(℃)'].mean():.2f} ℃")
st.metric("전체 최저기온", f"{df['최저기온(℃)'].min():.2f} ℃")
st.metric("전체 최고기온", f"{df['최고기온(℃)'].max():.2f} ℃")

st.subheader("구간(10년 단위)별 기온 요약")
st.table(seg_df)

# ---------- 차트 ----------
st.subheader("그래프")

# 1) 선 그래프 (전체 연평균기온 + 5년 이동평균)
yearly = df.groupby("연도")["평균기온(℃)"].mean().reset_index()
yearly["5년 이동평균"] = yearly["평균기온(℃)"].rolling(window=5, center=True).mean()

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=yearly["연도"], y=yearly["평균기온(℃)"],
        mode="lines+markers", name="연평균기온",
        line=dict(color="#1f77b4", width=2),
    )
)
fig.add_trace(
    go.Scatter(
        x=yearly["연도"], y=yearly["5년 이동평균"],
        mode="lines", name="5년 이동평균",
        line=dict(color="#d62728", width=2, dash="dash"),
    )
)
fig.update_layout(
    title="연도별 평균기온 추이",
    xaxis_title="연도",
    yaxis_title="기온 (℃)",
    hovermode="x unified",
    margin=dict(l=40, r=20, t=40, b=40),
    height=450,
)
st.plotly_chart(fig, use_container_width=True)

# 2) 막대 그래프 (10년 구간별: 최고 33°C 이상 빨강, 최저 25°C 이상 파랑)
bar_rows = []
for d in sorted(df["10년 구간"].unique()):
    g = df[df["10년 구간"] == d]
    bar_rows.append({
        "10년 구간": f"{int(d)}년대",
        "최고기온 33°C 이상 일수": int((g["최고기온(℃)"] >= 33).sum()),
        "최저기온 25°C 이상 일수": int((g["최저기온(℃)"] >= 25).sum()),
    })
bar_df = pd.DataFrame(bar_rows)

fig = go.Figure()
fig.add_trace(
    go.Bar(
        x=bar_df["10년 구간"],
        y=bar_df["최고기온 33°C 이상 일수"],
        name="최고기온 33°C 이상",
        marker_color="red",
    )
)
fig.add_trace(
    go.Bar(
        x=bar_df["10년 구간"],
        y=bar_df["최저기온 25°C 이상 일수"],
        name="최저기온 25°C 이상",
        marker_color="blue",
    )
)
fig.update_layout(
    title="10년 구간별 고온일수 (빨강: 최고 33°C 이상, 파랑: 최저 25°C 이상)",
    xaxis_title="10년 구간",
    yaxis_title="일수",
    barmode="group",
    legend=dict(x=0.02, y=0.98),
    margin=dict(l=40, r=20, t=40, b=40),
    height=450,
)
st.plotly_chart(fig, use_container_width=True)

# 3) 산점도 (연도 × 평균기온, 10년 구간별 색)
scatter_df = df.sample(n=min(20000, len(df)), random_state=42)
fig = px.scatter(
    scatter_df,
    x="연도",
    y="평균기온(℃)",
    color="10년 구간",
    opacity=0.35,
    title="산점도 (연도 × 평균기온, 10년 구간별 색)",
)
fig.update_layout(
    hovermode="x unified",
    margin=dict(l=40, r=20, t=40, b=40),
    height=450,
)
st.plotly_chart(fig, use_container_width=True)

# 4) 히트맵 (1908~1937년 평균기온 기준)
heat = df[(df["연도"] >= 1908) & (df["연도"] <= 1937)]
if heat.empty:
    st.warning("히트맵에 사용할 데이터(1908~1937년)가 없습니다.")
else:
    piv = heat.pivot_table(
        index="월", columns="연도", values="평균기온(℃)", aggfunc="mean"
    )
    fig = px.imshow(
        piv,
        aspect="auto",
        labels={"x": "연도", "y": "월", "color": "평균기온(℃)"},
        title="히트맵 (1908~1937년 평균기온 by 월×연도)",
    )
    fig.update_layout(
        margin=dict(l=60, r=20, t=40, b=40),
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

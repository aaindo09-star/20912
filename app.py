"""
서울 기온 트렌드 Streamlit 앱
- 연도별로 연평균기온 꺾은선 그래프 표시
- 5년 이동평균선을 같은 그래프에 겹쳐서 표시
- 사이드바 연도 범위 슬라이더
- 선택 구간의 평균/최저/최고 기온 표시

실행 방법:
    pip install -r requirements.txt
    streamlit run seoul_temperature_streamlit.py
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="서울 기온 트렌드", layout="wide")

# ---------------------------------------------------------------
# 데이터 로드 (탭 문자 처리 포함)
# ---------------------------------------------------------------
@st.cache_data
def load_data(path: str = "seoul_temperature.csv") -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")

    # 주의: 날짜 값 앞에 탭 문자("	1907-10-01")가 있음
    # - 따옴표 제거 후 .str.strip()으로 앞뒤 공백·탭 제거
    # - datetime으로 변환
    df["날짜"] = (
        df["날짜"]
        .astype(str)
        .str.replace('"', "", regex=False)
        .str.strip()
    )
    df["날짜"] = pd.to_datetime(df["날짜"])
    return df

df = load_data()

# ---------------------------------------------------------------
# 연도별 연평균기온 및 5년 이동평균
# ---------------------------------------------------------------
yearly = (
    df.groupby(df["날짜"].dt.year)["평균기온(℃)"]
    .mean()
    .reset_index(name="연평균기온")
    .sort_values("연도")
)

# 5년 이동평균 (연평균기온 기준, 중심 이동)
yearly["5년 이동평균"] = yearly["연평균기온"].rolling(window=5, center=True).mean()

# ---------------------------------------------------------------
# 사이드바: 연도 범위 슬라이더
# ---------------------------------------------------------------
min_year, max_year = int(yearly["연도"].min()), int(yearly["연도"].max())
selected = st.sidebar.slider(
    "연도 범위",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    help="슬라이더를 움직여 분석 구간을 선택하세요.",
)

# 선택 구간 데이터
selected_df = df[
    (df["날짜"].dt.year >= selected[0]) & (df["날짜"].dt.year <= selected[1])
]
year_range = yearly[
    (yearly["연도"] >= selected[0]) & (yearly["연도"] <= selected[1])
]

# 선택 구간 통계 (평균/최저/최고)
c1, c2, c3 = st.sidebar.columns(3)
c1.metric("평균기온", f"{selected_df['평균기온(℃)'].mean():.2f} ℃")
c2.metric("최저기온", f"{selected_df['최저기온(℃)'].min():.2f} ℃")
c3.metric("최고기온", f"{selected_df['최고기온(℃)'].max():.2f} ℃")

# ---------------------------------------------------------------
# 그래프
# ---------------------------------------------------------------
st.title("서울 연평균기온 추이")
st.caption(f"표시 구간: {selected[0]}년 ~ {selected[1]}년")

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=year_range["연도"],
        y=year_range["연평균기온"],
        mode="lines+markers",
        name="연평균기온",
        line=dict(color="#1f77b4", width=2),
    )
)
fig.add_trace(
    go.Scatter(
        x=year_range["연도"],
        y=year_range["5년 이동평균"],
        mode="lines",
        name="5년 이동평균",
        line=dict(color="#d62728", width=2, dash="dash"),
    )
)

fig.update_layout(
    xaxis_title="연도",
    yaxis_title="기온 (℃)",
    hovermode="x unified",
    margin=dict(l=40, r=20, t=40, b=40),
    height=520,
)
st.plotly_chart(fig, use_container_width=True)

"""
서울 기온 트렌드 Streamlit 앱

- CSV 경로를 자동 탐색하고, 없으면 업로드
- 날짜 앞의 탭/따옴표 제거 후 datetime 변환
- 연도별 연평균기온 + 5년 이동평균 그래프
- 사이드바 연도 슬라이더와 구간 통계
"""

from __future__ import annotations

import glob
import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="서울 기온 트렌드", layout="wide")


def find_csv() -> str | None:
    candidates = [
        "seoul_temperature.csv",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "seoul_temperature.csv"),
        "/mnt/data/seoul_temperature.csv",
        "/mount/src/20261017/seoul_temperature.csv",
        "/mount/src/20261017_/seoul_temperature.csv",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    matches = glob.glob("**/seoul_temperature.csv", recursive=True)
    return matches[0] if matches else None


def load_data() -> pd.DataFrame:
    path = find_csv()

    if path is None:
        st.error("seoul_temperature.csv 파일을 찾을 수 없습니다. 파일을 올려주세요.")
        uploaded = st.file_uploader("CSV 파일 업로드", type="csv")
        if uploaded is None:
            st.stop()
        df = pd.read_csv(uploaded, encoding="utf-8-sig")
    else:
        st.info(f"데이터를 찾습니다: {path}")
        df = pd.read_csv(path, encoding="utf-8-sig")

    df["날짜"] = (
        df["날짜"]
        .astype(str)
        .str.replace('"', "", regex=False)
        .str.strip()
    )
    df["날짜"] = pd.to_datetime(df["날짜"])
    return df


df = load_data()

# 열 이름 검증
expected_cols = {"날짜", "지점", "평균기온(℃)", "최저기온(℃)", "최고기온(℃)"}
missing = expected_cols - set(df.columns)
if missing:
    st.error(f"CSV 열 이름이 예상과 다릅니다. 발견된 열: {list(df.columns)}")
    st.stop()

# 연도별 연평균기온 + 5년 이동평균
yearly = (
    df.groupby(df["날짜"].dt.year)["평균기온(℃)"]
    .mean()
    .reset_index(name="연평균기온")
)

# 원본 열 이름과 무관하게 열 이름을 직접 지정 (KeyError 방지)
yearly.columns = ["연도", "연평균기온"]
yearly = yearly.sort_values("연도").reset_index(drop=True)
yearly["5년 이동평균"] = yearly["연평균기온"].rolling(window=5, center=True).mean()

# 사이드바 연도 슬라이더
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

# 그래프
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

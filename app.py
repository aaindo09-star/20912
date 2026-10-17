"""
서울 기온 트렌드 Streamlit 앱
- 연도별로 연평균기온 꺾은선 그래프 표시
- 5년 이동평균선을 같은 그래프에 겹쳐서 표시
- 사이드바 연도 범위 슬라이더
- 사이드바 옵션: 결측치가 있는 연도 제외
- 선택 구간의 평균/최저/최고 기온 표시

실행 방법:
    pip install -r requirements.txt
    streamlit run app.py
"""

from __future__ import annotations

import calendar

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
    # 변환 불가(빈 값 등) 행은 NaT로 만든 뒤 제거
    # (CSV 맨 끝에 날짜가 탭 문자뿐인 빈 행이 있음)
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df = df.dropna(subset=["날짜"]).reset_index(drop=True)
    df["연도"] = df["날짜"].dt.year
    return df


def format_years(years) -> str:
    """[1950, 1951, 1952, 1953, 2026] -> '1950~1953, 2026'"""
    parts, start, prev = [], None, None
    for y in sorted(years):
        if start is None:
            start = prev = y
        elif y == prev + 1:
            prev = y
        else:
            parts.append(str(start) if start == prev else f"{start}~{prev}")
            start = prev = y
    if start is not None:
        parts.append(str(start) if start == prev else f"{start}~{prev}")
    return ", ".join(parts)


df = load_data()

# ---------------------------------------------------------------
# 연도별 연평균기온 + 결측 여부
#   - 완전한 연도: 그 해의 모든 날(365/366일)에 평균기온 값이 있음
#   - 날짜 행이 통째로 없거나, 평균기온이 비어 있으면 결측 연도
# ---------------------------------------------------------------
year_stats = df.groupby("연도").agg(
    연평균기온=("평균기온(℃)", "mean"),
    유효일수=("평균기온(℃)", "count"),
)
year_stats["연일수"] = [366 if calendar.isleap(y) else 365 for y in year_stats.index]
year_stats["완전연도"] = year_stats["유효일수"] == year_stats["연일수"]
yearly = year_stats.reset_index().sort_values("연도").reset_index(drop=True)

# ---------------------------------------------------------------
# 사이드바: 결측 연도 제외 옵션
# ---------------------------------------------------------------
exclude_incomplete = st.sidebar.checkbox(
    "결측치가 있는 연도 제외",
    value=True,
    help=(
        "평균기온이 하루라도 비어 있거나 날짜 자체가 없는 연도를 "
        "그래프·이동평균·통계에서 뺍니다. 끄면 있는 날짜만으로 평균을 냅니다."
    ),
)

if exclude_incomplete:
    # 결측 연도의 값은 비우고(NaN) 연도 칸은 남겨 둔다.
    # -> 그래프 선이 끊기고, 5년 이동평균도 연속된 5개 연도가 모두 있을 때만 계산된다.
    yearly.loc[~yearly["완전연도"], "연평균기온"] = float("nan")

# 5년 이동평균 (연평균기온 기준, 중심 이동, 5개 연도가 모두 있을 때만 계산)
yearly["5년 이동평균"] = yearly["연평균기온"].rolling(window=5, center=True).mean()

# ---------------------------------------------------------------
# 사이드바: 연도 범위 슬라이더
# ---------------------------------------------------------------
slider_pool = yearly[yearly["완전연도"]] if exclude_incomplete else yearly
min_year, max_year = int(slider_pool["연도"].min()), int(slider_pool["연도"].max())
selected = st.sidebar.slider(
    "연도 범위",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    help="슬라이더를 움직여 분석 구간을 선택하세요.",
)

# 선택 구간 데이터
in_range = (df["연도"] >= selected[0]) & (df["연도"] <= selected[1])
if exclude_incomplete:
    complete_years = yearly.loc[yearly["완전연도"], "연도"]
    in_range &= df["연도"].isin(complete_years)
selected_df = df[in_range]

year_range = yearly[
    (yearly["연도"] >= selected[0]) & (yearly["연도"] <= selected[1])
]
incomplete_in_range = year_range.loc[~year_range["완전연도"], "연도"].tolist()

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
if incomplete_in_range:
    if exclude_incomplete:
        st.caption(f"결측치로 제외된 연도: {format_years(incomplete_in_range)}")
    else:
        st.caption(
            f"결측치가 있는 연도 포함 (있는 날짜만으로 평균 계산): "
            f"{format_years(incomplete_in_range)}"
        )

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=year_range["연도"],
        y=year_range["연평균기온"],
        mode="lines+markers",
        name="연평균기온",
        line=dict(color="#1f77b4", width=2),
        connectgaps=False,
    )
)
fig.add_trace(
    go.Scatter(
        x=year_range["연도"],
        y=year_range["5년 이동평균"],
        mode="lines",
        name="5년 이동평균",
        line=dict(color="#d62728", width=2, dash="dash"),
        connectgaps=False,
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

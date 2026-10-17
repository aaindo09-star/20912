"""
서울 기온 트렌드 Streamlit 앱 (수정판)

- 평균/최저/최고 기온 범위와 연도 구간을 화면(메인)에 배치
- 구간(연도/월/계절)별 분석
- 차트: 선 / 막대 / 히트맵 / 3D 산점도
실행:
    pip install -r requirements.txt
    streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
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
    df["계절"] = df["월"].map({
        12: "겨울", 1: "겨울", 2: "겨울",
        3: "봄", 4: "봄", 5: "봄",
        6: "여름", 7: "여름", 8: "여름",
        9: "가을", 10: "가을", 11: "가을",
    })
    return df


df = load_data()

# 기온 범위 기본값 (자료의 10~90 백분위)
avg_l, avg_h = df["평균기온(℃)"].quantile([0.1, 0.9])
min_l, min_h = df["최저기온(℃)"].quantile([0.1, 0.9])
max_l, max_h = df["최고기온(℃)"].quantile([0.1, 0.9])

# ---------- 메인 화면 설정 (사이드바 아님) ----------
st.subheader("설정")

# 기간
min_year, max_year = int(df["연도"].min()), int(df["연도"].max())
year_range = st.slider("연도 범위", min_year, max_year, (min_year, max_year))

# 기온 범위
avg_range = st.slider(
    "평균기온(℃) 범위", float(avg_l), float(avg_h),
    (float(avg_l), float(avg_h)),
)
min_range = st.slider(
    "최저기온(℃) 범위", float(min_l), float(min_h),
    (float(min_l), float(min_h)),
)
max_range = st.slider(
    "최고기온(℃) 범위", float(max_l), float(max_h),
    (float(max_l), float(max_h)),
)

# 구간(그룹) 기준
seg_option = st.selectbox("구간(그룹) 기준", ["연도", "월", "계절"])

# 차트 종류
chart_type = st.selectbox("차트 종류", ["선", "막대", "히트맵", "3D 산점도"])

# ---------- 필터 ----------
in_range = (df["연도"] >= year_range[0]) & (df["연도"] <= year_range[1])
avg_f = (df["평균기온(℃)"] >= avg_range[0]) & (df["평균기온(℃)"] <= avg_range[1])
min_f = (df["최저기온(℃)"] >= min_range[0]) & (df["최저기온(℃)"] <= min_range[1])
max_f = (df["최고기온(℃)"] >= max_range[0]) & (df["최고기온(℃)"] <= max_range[1])
df_f = df[in_range & avg_f & min_f & max_f].copy()

# ---------- 구간별 통계 (메인 화면) ----------
y1, y2 = year_range
sel = df[(df["연도"] >= y1) & (df["연도"] <= y2)]
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("평균기온 평균", f"{sel['평균기온(℃)'].mean():.2f} ℃")
with c2:
    st.metric("최저기온 최저", f"{sel['최저기온(℃)'].min():.2f} ℃")
with c3:
    st.metric("최고기온 최고", f"{sel['최고기온(℃)'].max():.2f} ℃")

# ---------- 차트 ----------
st.subheader("그래프")

if df_f.empty:
    st.warning("표시할 데이터가 없습니다. 연도나 기온 범위를 조정해 주세요.")
else:
    if chart_type == "선":
        yearly_avg = df_f.groupby("연도")["평균기온(℃)"].mean().reset_index()
        fig = px.line(
            yearly_avg, x="연도", y="평균기온(℃)", markers=True,
            labels={"연도": "연도", "평균기온(℃)": "평균기온(℃)"},
            title="연도별 평균기온",
        )
        fig.update_layout(margin=dict(l=40, r=20, t=40, b=40), height=450)

    elif chart_type == "막대":
        if seg_option == "연도":
            grp = df_f.groupby("연도")["평균기온(℃)"].mean().reset_index()
        elif seg_option == "월":
            grp = df_f.groupby("월")["평균기온(℃)"].mean().reset_index()
            grp = grp.rename(columns={"월": "월", "평균기온(℃)": "평균기온(℃)"})
        else:
            grp = df_f.groupby("계절")["평균기온(℃)"].mean().reset_index()
        fig = px.bar(
            grp, x=grp.columns[0], y="평균기온(℃)",
            title="구간별 평균기온",
            labels={grp.columns[0]: "구간", "평균기온(℃)": "평균기온(℃)"},
        )
        fig.update_layout(margin=dict(l=40, r=20, t=40, b=40), height=450)

    elif chart_type == "히트맵":
        piv = df_f.pivot_table(
            index="월", columns="연도", values="평균기온(℃)", aggfunc="mean"
        )
        fig = px.imshow(
            piv, aspect="auto",
            labels={"x": "연도", "y": "월", "color": "평균기온(℃)"},
            title="월 × 연도 히트맵 (평균기온)",
        )
        fig.update_layout(margin=dict(l=60, r=20, t=40, b=40), height=450)

    elif chart_type == "3D 산점도":
        fig = px.scatter_3d(
            df_f, x="연도", y="월", z="평균기온(℃)",
            color="평균기온(℃)", opacity=0.5,
            title="3D 산점도 (연도 × 월 × 평균기온)",
        )
        fig.update_layout(margin=dict(l=60, r=20, t=40, b=40), height=450)

    st.plotly_chart(fig, use_container_width=True)

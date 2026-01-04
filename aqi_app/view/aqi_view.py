import streamlit as st
import pandas as pd
import altair as alt


def render_header(raw_preview: str) -> None:
    st.title("实时AQI抓取与城市排行榜")
    st.markdown(
        """
        本页面演示如何遵守爬虫礼仪，从[中国空气质量在线监测平台](https://www.aqistudy.cn/historydata/index.php)
        抓取城市AQI信息，并展示数据清洗、排序与可视化结果。
        """
    )
    with st.expander("查看返回内容片段（前500字符）"):
        st.code(raw_preview or "无内容", language="html")


def render_table(df: pd.DataFrame) -> None:
    st.subheader("抓取到的城市AQI数据")
    st.dataframe(df, use_container_width=True)


def render_insights(best: pd.DataFrame, worst: pd.DataFrame) -> None:
    st.subheader("空气质量概览")
    cols = st.columns(2)
    cols[0].metric("空气质量最好 (AQI最低)", best.iloc[0]["城市"], int(best.iloc[0]["AQI"]))
    cols[1].metric("空气质量最差 (AQI最高)", worst.iloc[0]["城市"], int(worst.iloc[0]["AQI"]))

    st.markdown("### 最佳 3 城市")
    st.table(best.reset_index(drop=True))
    st.markdown("### 最差 3 城市")
    st.table(worst.reset_index(drop=True))


def render_chart(df: pd.DataFrame) -> None:
    st.subheader("城市AQI条形图")
    chart_data = df.rename(columns={"城市": "city", "AQI": "aqi"})
    chart = (
        alt.Chart(chart_data)
        .mark_bar()
        .encode(
            x=alt.X("city", sort="-y", title="城市"),
            y=alt.Y("aqi", title="AQI数值"),
            tooltip=["city", "aqi"],
            color=alt.condition(alt.datum.aqi <= 80, alt.value("#2ecc71"), alt.value("#e74c3c")),
        )
    )
    st.altair_chart(chart, use_container_width=True)


def render_city_trend(monthly_df: pd.DataFrame) -> None:
    st.subheader("单城市AQI月度趋势")
    if monthly_df.empty:
        st.info("暂无可用的月度数据。")
        return
    city = st.selectbox("选择城市", options=sorted(monthly_df["城市"].unique()))
    filtered = monthly_df[monthly_df["城市"] == city].sort_values("月份")
    line = (
        alt.Chart(filtered)
        .mark_line(point=True)
        .encode(x="月份", y="AQI", tooltip=["城市", "月份", "AQI"], color=alt.value("#3498db"))
    )
    st.altair_chart(line, use_container_width=True)


def render_monthly_top20(monthly_df: pd.DataFrame) -> None:
    st.subheader("指定月份前20城市对比")
    if monthly_df.empty:
        st.info("暂无可用的月度数据。")
        return
    months = sorted(monthly_df["月份"].unique())
    month = st.selectbox("选择月份", options=months)
    filtered = monthly_df[monthly_df["月份"] == month].sort_values("AQI").head(20)
    chart = (
        alt.Chart(filtered)
        .mark_bar()
        .encode(
            x=alt.X("城市", sort="-y", title="城市"),
            y=alt.Y("AQI", title="AQI数值"),
            tooltip=["城市", "AQI"],
            color=alt.condition(alt.datum.AQI <= filtered["AQI"].median(), alt.value("#2ecc71"), alt.value("#e67e22")),
        )
    )
    st.altair_chart(chart, use_container_width=True)


def render_city_comparison(monthly_df: pd.DataFrame) -> None:
    st.subheader("任意两城趋势对比")
    if monthly_df.empty:
        st.info("暂无可用的月度数据。")
        return
    cities = sorted(monthly_df["城市"].unique())
    col1, col2 = st.columns(2)
    city_a = col1.selectbox("城市 A", options=cities, index=0)
    remaining = [c for c in cities if c != city_a]
    city_b = col2.selectbox("城市 B", options=remaining, index=0 if remaining else None)

    if not city_b:
        st.info("请选择两个不同的城市进行对比。")
        return

    subset = monthly_df[monthly_df["城市"].isin([city_a, city_b])].sort_values("月份")
    line = (
        alt.Chart(subset)
        .mark_line(point=True)
        .encode(x="月份", y="AQI", color="城市", tooltip=["城市", "月份", "AQI"])
    )
    st.altair_chart(line, use_container_width=True)

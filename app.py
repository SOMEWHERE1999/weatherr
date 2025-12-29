import logging

import streamlit as st

from aqi_app.controller.aqi_controller import AQIController
from aqi_app.view import aqi_view

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def main() -> None:
    st.set_page_config(page_title="AQI城市排行榜", layout="wide")
    controller = AQIController()

    st.sidebar.header("抓取配置")
    limit = st.sidebar.slider("城市数量", min_value=10, max_value=30, value=12, step=2)
    top_n = st.sidebar.slider("排行数量", min_value=3, max_value=5, value=3)

    with st.spinner("正在抓取数据并解析..."):
        df, raw_preview = controller.load_data(limit=limit)
        best, worst = controller.summarize(df, top_n=top_n)
        ordered = controller.to_bar_chart_data(df)

    aqi_view.render_header(raw_preview)
    aqi_view.render_table(df)
    aqi_view.render_insights(best, worst)
    aqi_view.render_chart(ordered)


if __name__ == "__main__":
    main()

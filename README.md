# weatherr

实时AQI抓取与城市排行榜示例。使用MVC分层和Streamlit构建页面，展示城市空气质量排行与可视化。

## 功能概览
- requests 抓取目标站点首页，并遵守 `robots.txt` 与 `time.sleep(1)` 的请求节奏。
- BeautifulSoup 解析城市与AQI（若抓取失败则使用内置示例数据）。
- Pandas 清洗与排序数据，输出空气质量最好/最差的3个城市。
- Altair/Streamlit 展示表格、指标与条形图。

## 运行
1. 安装依赖：`pip install -r requirements.txt`
2. 启动应用：`streamlit run app.py`

侧边栏可调整抓取的城市数量与排行榜数量。

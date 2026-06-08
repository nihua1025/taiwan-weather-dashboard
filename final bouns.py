import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(page_title="Taiwan Weather Dashboard", layout="wide")

st.title("台灣氣象分析 Dashboard")
st.caption("資料來源：中央氣象署未來 36 小時天氣預報資料，因此圖表呈現的是預測資料，而非實際觀測資料。")

conn = sqlite3.connect("weather.db")
df = pd.read_sql("SELECT * FROM weather_forecast", conn)
conn.close()

df["start_time"] = pd.to_datetime(df["start_time"])
df["end_time"] = pd.to_datetime(df["end_time"])

latest_update = df["updated_at"].max()
st.caption(f"資料更新時間：{latest_update}")

city_coords = {
    "臺北市": [25.0330, 121.5654],
    "新北市": [25.0169, 121.4628],
    "桃園市": [24.9937, 121.3010],
    "臺中市": [24.1477, 120.6736],
    "臺南市": [22.9999, 120.2270],
    "高雄市": [22.6273, 120.3014],
    "基隆市": [25.1276, 121.7392],
    "新竹市": [24.8138, 120.9675],
    "嘉義市": [23.4801, 120.4491],
    "新竹縣": [24.8387, 121.0177],
    "苗栗縣": [24.5602, 120.8214],
    "彰化縣": [24.0518, 120.5161],
    "南投縣": [23.9609, 120.9719],
    "雲林縣": [23.7092, 120.4313],
    "嘉義縣": [23.4518, 120.2555],
    "屏東縣": [22.5519, 120.5487],
    "宜蘭縣": [24.7021, 121.7378],
    "花蓮縣": [23.9872, 121.6015],
    "臺東縣": [22.7583, 121.1444],
    "澎湖縣": [23.5711, 119.5793],
    "金門縣": [24.4321, 118.3171],
    "連江縣": [26.1602, 119.9517]
}

def travel_score(max_temp, pop):
    score = 100

    if max_temp >= 34:
        score -= 30
    elif max_temp >= 32:
        score -= 20
    elif max_temp >= 30:
        score -= 10

    if pop >= 80:
        score -= 40
    elif pop >= 60:
        score -= 25
    elif pop >= 40:
        score -= 10

    return max(score, 0)

city = st.sidebar.selectbox("選擇縣市", sorted(df["city"].unique()))
filtered = df[df["city"] == city].sort_values("start_time")

st.subheader(f"{city} 天氣概況")

col1, col2, col3, col4 = st.columns(4)

col1.metric("平均最高溫", f"{filtered['max_temp'].mean():.1f} °C")
col2.metric("平均最低溫", f"{filtered['min_temp'].mean():.1f} °C")
col3.metric("平均降雨機率", f"{filtered['pop'].mean():.1f}%")
col4.metric("近期天氣", filtered.iloc[0]["weather"])

st.markdown("### 溫度變化")

fig1 = px.line(
    filtered,
    x="start_time",
    y=["min_temp", "max_temp"],
    markers=True,
    title=f"{city} 未來 36 小時溫度變化"
)
fig1.update_layout(
    xaxis_title="預報時間",
    yaxis_title="溫度（°C）",
    legend_title="溫度類型"
)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("### 降雨機率")

fig2 = px.bar(
    filtered,
    x="start_time",
    y="pop",
    color="pop",
    color_continuous_scale="Blues",
    title=f"{city} 未來 36 小時降雨機率"
)
fig2.update_layout(
    xaxis_title="預報時間",
    yaxis_title="降雨機率（%）",
    coloraxis_colorbar_title="降雨機率"
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
st.header("全台縣市比較與重點分析")

city_summary = df.groupby("city", as_index=False).agg({
    "max_temp": "mean",
    "min_temp": "mean",
    "pop": "mean"
})

city_summary["travel_score"] = city_summary.apply(
    lambda x: travel_score(x["max_temp"], x["pop"]),
    axis=1
)

city_summary["lat"] = city_summary["city"].map(lambda x: city_coords.get(x, [None, None])[0])
city_summary["lon"] = city_summary["city"].map(lambda x: city_coords.get(x, [None, None])[1])
city_summary = city_summary.dropna(subset=["lat", "lon"])

top5_travel = city_summary.sort_values("travel_score", ascending=False).head(5)
top5_hot = city_summary.sort_values("max_temp", ascending=False).head(5)
rain_warning = city_summary[city_summary["pop"] >= 70].sort_values("pop", ascending=False)

st.markdown("### 🏖️ 旅遊適宜指數 Top 5 縣市")

st.dataframe(
    top5_travel[["city", "travel_score", "max_temp", "pop"]].rename(columns={
        "city": "縣市",
        "travel_score": "旅遊適宜指數",
        "max_temp": "平均最高溫",
        "pop": "平均降雨機率"
    }),
    use_container_width=True
)

col5, col6 = st.columns(2)

with col5:
    st.markdown("### 🔥 最熱 Top 5 縣市")
    st.dataframe(
        top5_hot[["city", "max_temp", "pop"]].rename(columns={
            "city": "縣市",
            "max_temp": "平均最高溫",
            "pop": "平均降雨機率"
        }),
        use_container_width=True
    )

with col6:
    st.markdown("### ⚠️ 降雨警戒區")
    if rain_warning.empty:
        st.success("目前沒有平均降雨機率超過 70% 的縣市。")
    else:
        st.dataframe(
            rain_warning[["city", "pop", "max_temp"]].rename(columns={
                "city": "縣市",
                "pop": "平均降雨機率",
                "max_temp": "平均最高溫"
            }),
            use_container_width=True
        )

st.markdown("### 台灣旅遊適宜指數地圖")

fig_map = px.scatter_mapbox(
    city_summary,
    lat="lat",
    lon="lon",
    size="travel_score",
    color="travel_score",
    hover_name="city",
    hover_data={
        "travel_score": ":.0f",
        "max_temp": ":.1f",
        "min_temp": ":.1f",
        "pop": ":.1f",
        "lat": False,
        "lon": False
    },
    color_continuous_scale="RdYlGn",
    size_max=30,
    zoom=6,
    height=600,
    title="各縣市旅遊適宜指數地圖"
)

fig_map.update_layout(
    mapbox_style="open-street-map",
    margin={"r": 0, "t": 40, "l": 0, "b": 0},
    coloraxis_colorbar_title="旅遊適宜指數"
)

st.plotly_chart(fig_map, use_container_width=True)

st.markdown("### 各縣市平均最高溫比較")

city_summary_hot = city_summary.sort_values("max_temp", ascending=False)

fig3 = px.bar(
    city_summary_hot,
    x="city",
    y="max_temp",
    color="max_temp",
    color_continuous_scale="RdYlBu_r",
    title="各縣市平均最高溫比較"
)
fig3.update_layout(
    xaxis_title="縣市",
    yaxis_title="平均最高溫（°C）",
    coloraxis_colorbar_title="溫度"
)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("### 各縣市平均降雨機率比較")

rain_summary = city_summary.sort_values("pop", ascending=False)

fig4 = px.bar(
    rain_summary,
    x="city",
    y="pop",
    color="pop",
    color_continuous_scale="Blues",
    title="各縣市平均降雨機率比較"
)
fig4.update_layout(
    xaxis_title="縣市",
    yaxis_title="平均降雨機率（%）",
    coloraxis_colorbar_title="降雨機率"
)
st.plotly_chart(fig4, use_container_width=True)
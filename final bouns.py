import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(page_title="Taiwan Weather Dashboard", layout="wide")

st.title("台灣氣象分析 Dashboard")

conn = sqlite3.connect("weather.db")
df = pd.read_sql("SELECT * FROM weather_forecast", conn)
conn.close()

st.write("資料預覽")
st.dataframe(df)

city = st.sidebar.selectbox("選擇縣市", sorted(df["city"].unique()))
filtered = df[df["city"] == city]

st.subheader(f"{city} 天氣概況")

col1, col2, col3 = st.columns(3)
col1.metric("平均最高溫", f"{filtered['max_temp'].mean():.1f} °C")
col2.metric("平均最低溫", f"{filtered['min_temp'].mean():.1f} °C")
col3.metric("平均降雨機率", f"{filtered['pop'].mean():.1f}%")

fig1 = px.line(
    filtered,
    x="start_time",
    y=["min_temp", "max_temp"],
    title=f"{city} 溫度變化"
)
st.plotly_chart(fig1, use_container_width=True)

fig2 = px.bar(
    filtered,
    x="start_time",
    y="pop",
    title=f"{city} 降雨機率"
)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("全台縣市比較")

city_summary = df.groupby("city", as_index=False).agg({
    "max_temp": "mean",
    "min_temp": "mean",
    "pop": "mean"
})

fig3 = px.bar(
    city_summary,
    x="city",
    y="max_temp",
    title="各縣市平均最高溫比較"
)
st.plotly_chart(fig3, use_container_width=True)

fig4 = px.bar(
    city_summary,
    x="city",
    y="pop",
    title="各縣市平均降雨機率比較"
)
st.plotly_chart(fig4, use_container_width=True)
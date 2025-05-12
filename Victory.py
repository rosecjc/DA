# 隔日沖勝率分析工具
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="隔日沖勝率工具", layout="wide")
st.title("⚡ 隔日沖勝率分析小工具")

symbol = st.text_input("請輸入股票代號（如 AAPL, TSM, 2330.TW）:", value="AAPL")
period = st.selectbox("回測區間：", ["3mo", "6mo", "1y", "2y"], index=2)
threshold = st.slider("隔日漲幅門檻（%）", 0.5, 5.0, 1.5, 0.1)

@st.cache_data
def load_data(symbol, period):
    try:
        df = yf.download(symbol, period=period)
        if df.empty:
            st.error("❌ 無法取得資料，請確認股票代號是否正確。")
            return None
        expected_cols = {'Open', 'Close'}
        if not expected_cols.issubset(df.columns):
            st.error(f"❌ 資料缺少必要欄位：{expected_cols - set(df.columns)}")
            return None
        df.dropna(inplace=True)
        return df
    except Exception as e:
        st.error(f"資料載入錯誤：{e}")
        return None

if symbol:
    df = load_data(symbol, period)
    if df is None:
        st.stop()
    df['Next_Open'] = df['Open'].shift(-1)
    df['Day3_Close'] = df['Close'].shift(-2)  # 持有三日，Day0, Day1, Day2

    df['Overnight_Change'] = ((df['Next_Open'].values - df['Close'].values) / df['Close'].values) * 100
    df['Win'] = df['Overnight_Change'] >= threshold

    df['ThreeDay_Change'] = ((df['Day3_Close'].values - df['Close'].values) / df['Close'].values) * 100
    df['ThreeDay_Win'] = df['ThreeDay_Change'] >= 2.5

    valid_rows = df.dropna(subset=['Next_Open', 'Day3_Close', 'Close', 'Overnight_Change', 'ThreeDay_Change'])
    total = len(valid_rows)
    win_count = valid_rows['Win'].sum()
    win_rate = round(win_count / total * 100, 2) if total > 0 else 0

    three_day_count = valid_rows['ThreeDay_Win'].sum()
    three_day_rate = round(three_day_count / total * 100, 2) if total > 0 else 0

    st.metric("隔日沖勝率（漲幅 ≥ {:.1f}%）".format(threshold), f"{win_rate}%")
    st.metric("三日沖勝率（漲幅 ≥ 2.5%）", f"{three_day_rate}%")
    if total > 0:
        st.metric("平均隔日漲幅", f"{valid_rows['Overnight_Change'].mean():.2f}%")
        st.metric("平均三日漲幅", f"{valid_rows['ThreeDay_Change'].mean():.2f}%")
        st.metric("最大隔日跌幅", f"{valid_rows['Overnight_Change'].min():.2f}%")
    else:
        st.warning("⚠️ 無足夠樣本數進行統計。")
    st.caption(f"樣本總數：{total} 次 | 隔日勝出次數：{win_count} 次 | 三日勝出次數：{three_day_count} 次")

    st.subheader("📈 隔日開盤漲幅分布圖")
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.hist(valid_rows['Overnight_Change'], bins=30, color='skyblue', edgecolor='black')
    ax.axvline(threshold, color='red', linestyle='--', label=f"門檻 {threshold}%")
    ax.set_title("隔日開盤漲幅分布", fontsize=10)
    ax.set_xlabel("隔日漲幅（%）", fontsize=8)
    ax.set_ylabel("出現次數", fontsize=8)
    ax.legend(fontsize=8)
    ax.tick_params(labelsize=6)
    st.pyplot(fig)

    st.subheader("📋 詳細資料預覽（最近20筆）")
    st.dataframe(valid_rows[['Close', 'Next_Open', 'Day3_Close', 'Overnight_Change', 'ThreeDay_Change', 'Win', 'ThreeDay_Win']].tail(20).style.format("{:.2f}"))


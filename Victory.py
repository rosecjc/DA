# 股票分析工具：使用 FinMind API
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="股票分析工具", layout="wide")

FINMIND_TOKEN = st.secrets["FINMIND_TOKEN"]
API_URL = "https://api.finmindtrade.com/api/v4/data"

# --- 抓取資料工具函式 ---
@st.cache_data
def get_price_data(stock_id, days=180):
    today = datetime.today()
    start_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    params = {
        "dataset": "TaiwanStockPrice",
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date
    }
    headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}
    res = requests.get(API_URL, params=params, headers=headers)
    data = res.json()
    if data['status'] != 200 or not data['data']:
        return None
    df = pd.DataFrame(data['data'])
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df['Next_Open'] = df['open'].shift(-1)
    df['Day3_Close'] = df['close'].shift(-2)
    df['Overnight_Change'] = ((df['Next_Open'] - df['close']) / df['close']) * 100
    df['ThreeDay_Change'] = ((df['Day3_Close'] - df['close']) / df['close']) * 100
    df['Win'] = df['Overnight_Change'] >= 1.5
    df['ThreeDay_Win'] = df['ThreeDay_Change'] >= 2.5
    return df.dropna(subset=['Next_Open', 'Day3_Close'])

@st.cache_data
def get_eps_data(stock_id):
    params = {"dataset": "TaiwanStockFinancialStatements", "data_id": stock_id}
    headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}
    res = requests.get(API_URL, params=params, headers=headers)
    data = res.json()
    return pd.DataFrame(data['data']) if data['status'] == 200 else None

@st.cache_data
def get_dividend_data(stock_id):
    params = {"dataset": "TaiwanStockDividend", "data_id": stock_id}
    headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}
    res = requests.get(API_URL, params=params, headers=headers)
    data = res.json()
    return pd.DataFrame(data['data']) if data['status'] == 200 else None

# --- 頁面切換 ---
page = st.sidebar.radio("📁 功能選單", ["🔍 個股分析", "📊 勝率排行", "🧪 勝率模擬器"])

if page == "🔍 個股分析":
    st.title("🔍 個股分析")
    symbol = st.text_input("請輸入台股股票代號（例如：2330）", value="2330")
    df_price = get_price_data(symbol)
    if df_price is not None:
        st.subheader("📈 股價趨勢圖")
        st.line_chart(df_price[['close', 'Next_Open']])

        st.subheader("📊 勝率統計")
        win_rate = round(df_price['Win'].mean() * 100, 1)
        three_rate = round(df_price['ThreeDay_Win'].mean() * 100, 1)
        st.metric("隔日沖勝率（1.5%↑）", f"{win_rate}%")
        st.metric("三日沖勝率（2.5%↑）", f"{three_rate}%")

        st.dataframe(df_price.rename(columns={
            'close': '收盤價',
            'Next_Open': '次日開盤價',
            'Day3_Close': '第3日收盤價',
            'Overnight_Change': '隔日漲跌幅(%)',
            'ThreeDay_Change': '三日漲跌幅(%)',
            'Win': '隔日勝',
            'ThreeDay_Win': '三日勝'
        })[['收盤價', '次日開盤價', '第3日收盤價', '隔日漲跌幅(%)', '三日漲跌幅(%)', '隔日勝', '三日勝']].tail(20).round(2), use_container_width=True)

        st.subheader("📑 基本面資訊")
        with st.expander("📘 名詞解釋"):
            st.markdown("""
            - **每股盈餘 EPS**：公司每股可分得的稅後純益。數值越高，代表公司賺錢能力越好。
            - **殖利率 (%)**：股息除以股價的比率，衡量投資回報。一般而言超過 **4%** 被視為偏高，但也需注意是否因股價下跌造成。
            - **現金股利 (元)**：公司發放的現金股息總額（每股）。越穩定、連續配息紀錄越佳。
            """)
        df_eps = get_eps_data(symbol)
        df_div = get_dividend_data(symbol)

        if df_eps is not None and not df_eps.empty:
            latest_eps = df_eps[df_eps['type'] == 'Q4'].sort_values('date').iloc[-1]
            st.metric("每股盈餘 EPS", latest_eps.get('EPS', '無資料'))
        else:
            st.metric("每股盈餘 EPS", "無資料")

        if df_div is not None and not df_div.empty:
            latest_div = df_div.sort_values('date').iloc[-1]
            st.metric("殖利率 (%)", latest_div.get('DividendYield', '無資料'))
            st.metric("現金股利 (元)", latest_div.get('CashEarningsDistribution', '無資料'))
        else:
            st.metric("殖利率 (%)", "無資料")
            st.metric("現金股利 (元)", "無資料")
    else:
        st.error("❌ 查無股價資料，請確認代碼或 API token")

elif page == "📊 勝率排行":
    st.title("📊 多檔勝率排行推薦")
    target_stocks = ['2330', '2303', '2603', '2882', '2317', '2408', '3008', '1301', '1101', '2891']
    ranking = []
    progress = st.progress(0.0, text="🔍 正在分析勝率...")

    for i, symbol in enumerate(target_stocks):
        df = get_price_data(symbol)
        if df is not None and len(df) >= 20:
            win_rate = round(df['Win'].mean() * 100, 1)
            three_rate = round(df['ThreeDay_Win'].mean() * 100, 1)
            avg_return = round(df['Overnight_Change'].mean(), 2)
            ranking.append({
                "股票代號": symbol,
                "隔日勝率": f"{win_rate}%",
                "三日勝率": f"{three_rate}%",
                "平均隔日漲幅": f"{avg_return}%",
                "樣本數": len(df)
            })
        progress.progress((i + 1) / len(target_stocks))

    progress.empty()

    if ranking:
        df_rank = pd.DataFrame(ranking)
        df_rank = df_rank.sort_values(by="隔日勝率", key=lambda x: x.str.replace('%','').astype(float), ascending=False)
        st.success("✅ 分析完成！以下為推薦股票勝率排行：")
        st.dataframe(df_rank, use_container_width=True)
    else:
        st.warning("⚠️ 無法取得足夠資料進行排行分析。")

elif page == "🧪 勝率模擬器":
    st.title("🧪 勝率模擬器")
    symbol = st.text_input("請輸入股票代號進行模擬分析", value="2330")
    threshold = st.slider("漲幅門檻 %（若達此漲幅視為成功）", min_value=0.5, max_value=5.0, step=0.1, value=1.5)
    df = get_price_data(symbol)
    if df is not None:
        df['CustomWin'] = df['Overnight_Change'] >= threshold
        win_rate = round(df['CustomWin'].mean() * 100, 1)
        avg_return = round(df['Overnight_Change'].mean(), 2)
        st.metric("模擬勝率", f"{win_rate}%")
        st.metric("平均報酬率", f"{avg_return}%")
        st.dataframe(df[['close', 'Next_Open', 'Overnight_Change', 'CustomWin']].tail(20).round(2), use_container_width=True)
    else:
        st.warning("查無資料，請確認代碼")










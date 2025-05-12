# 分析工具（使用 twstock 來源）
import matplotlib

# 設定支援中文字型與負號（強制嵌入字體）
from matplotlib import font_manager
import matplotlib.pyplot as plt
font_path = "./fonts/NotoSansTC-VariableFont_wght.ttf"
font_prop = font_manager.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime, timedelta
import twstock

st.set_page_config(page_title="隔日沖勝率工具", layout="wide")

# 預設多檔篩選資料（未來可改為讀取 CSV 或動態來源）
from datetime import date
latest_date = date.today().strftime("%Y-%m-%d")
start_date = (date.today() - timedelta(days=180)).strftime("%Y-%m-%d")
from datetime import date
latest_date = date.today().strftime("%Y-%m-%d")
start_date = (date.today() - timedelta(days=180)).strftime("%Y-%m-%d")
data_update = latest_date
@st.cache_data

def get_top_twstock_data(days_back=180, threshold=1.5):
    import os
    cache_file = "top10_cached.csv"
    # 若有快取檔且未點重新整理，直接讀
    if os.path.exists(cache_file) and not refresh:
        return pd.read_csv(cache_file)

    # 僅篩熱門股（可換成其他清單）
    popular_codes = ['2330', '2303', '2603', '2609', '2615', '2308', '2412', '2454', '2882', '2891', '2379', '3034', '8069', '3661', '2327', '3008', '3017', '2382', '6116', '3481', '1101', '1216', '2105', '2301', '3045', '3702', '4904', '3231', '1314', '1303', '1301']

    progress_bar = st.progress(0)
    result = []
    for i, code in enumerate(popular_codes):
        name = twstock.codes.get(code, {}).get('name', code)
        progress_bar.progress(i / len(popular_codes))
        try:
            stock = twstock.Stock(code)
            raw_data = stock.fetch_from((date.today() - timedelta(days=days_back + 10)).year, (date.today() - timedelta(days=days_back + 10)).month)
            if not raw_data or len(raw_data) < 10:
                continue
            df = pd.DataFrame([{ 'date': d.date, 'open': d.open, 'close': d.close } for d in raw_data])
            df.set_index('date', inplace=True)
            df.dropna(inplace=True)
            df['Next_Open'] = df['open'].shift(-1)
            df['Day3_Close'] = df['close'].shift(-2)
            df['Overnight_Change'] = ((df['Next_Open'] - df['close']) / df['close']) * 100
            df['ThreeDay_Change'] = ((df['Day3_Close'] - df['close']) / df['close']) * 100
            df['Win'] = df['Overnight_Change'] >= threshold
            df['ThreeDay_Win'] = df['ThreeDay_Change'] >= 2.5
            valid_rows = df.dropna(subset=['Next_Open', 'Day3_Close'])
            total = len(valid_rows)
            if total == 0:
                continue
            win_rate = round(valid_rows['Win'].mean() * 100, 1)
            three_day_rate = round(valid_rows['ThreeDay_Win'].mean() * 100, 1)
            if total >= 10:
                result.append({
                    "日期區間": f"{start_date} ~ {latest_date}",
                    "股票名稱": name,
                    "代號": code,
                    "隔日沖勝率": f"{win_rate}%",
                    "樣本數": total,
                    "三日沖勝率": f"{three_day_rate}%",
                    "開盤買入勝率": f"{round((valid_rows['Overnight_Change'] > 0).mean() * 100, 1)}%",
                    "資料更新日": latest_date
                })
        except:
            continue
    progress_bar.empty()
    df_top = pd.DataFrame(result)
    df_top = df_top[df_top['隔日沖勝率'].str.replace('%','').astype(float) > 70]
    df_top = df_top.sort_values(by='隔日沖勝率', key=lambda x: x.str.replace('%','').astype(float), ascending=False).head(10)
    df_top.to_csv(cache_file, index=False)
    return df_top

refresh = st.button("🔄 重新整理推薦個股")
if refresh:
    st.cache_data.clear()
multistock_data = get_top_twstock_data(days_back=180, threshold=1.5)

tab1, tab2 = st.tabs(["📈 個股分析", "📊 多檔篩選勝率表"])
with tab2:
    st.title("📊 多檔篩選勝率表")
    st.caption(f"📆 資料更新日：{data_update}")
    clicked = st.data_editor(multistock_data, use_container_width=True, height=500, hide_index=True, key='multi')
    if clicked is not None and '代號' in clicked.columns:
        selected_row = clicked.iloc[0]  # 預設選第一筆互動項
        symbol = selected_row['代號']
        st.success(f"🔍 已選擇個股：{selected_row['股票名稱']}（{symbol}）")
with tab1:
    st.title("⚡ 分析小工具（twstock 來源）")

days_back = st.slider("回測天數：", 30, 300, 180, 10)
threshold = st.slider("隔日漲幅門檻（%）", 0.5, 5.0, 1.5, 0.1)

@st.cache_data
def load_twstock_data(symbol, days_back):
    try:
        stock = twstock.Stock(symbol)
        fetch_from_date = datetime.today() - timedelta(days=days_back + 10)
        raw_data = stock.fetch_from(fetch_from_date.year, fetch_from_date.month)
        if not raw_data:
            return None
        df = pd.DataFrame([{ 'date': d.date, 'open': d.open, 'close': d.close } for d in raw_data])
        df.set_index('date', inplace=True)
        df.dropna(inplace=True)
        return df
    except Exception as e:
        st.error(f"無法取得資料：{e}")
        return None

with tab1:
    if symbol:
        df = load_twstock_data(symbol, days_back)
    if df is None or df.empty:
        st.stop()

    df['Next_Open'] = df['open'].shift(-1)
    df['Day3_Close'] = df['close'].shift(-2)
    df['Overnight_Change'] = ((df['Next_Open'] - df['close']) / df['close']) * 100
    df['ThreeDay_Change'] = ((df['Day3_Close'] - df['close']) / df['close']) * 100
    df['Win'] = df['Overnight_Change'] >= threshold
    df['ThreeDay_Win'] = df['ThreeDay_Change'] >= 2.5

    valid_rows = df.dropna(subset=['Next_Open', 'Day3_Close'])
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

    
    st.subheader("📋 勝率統計表（最近 20 筆）")
    styled_df = valid_rows[['close', 'Next_Open', 'Day3_Close', 'Overnight_Change', 'ThreeDay_Change', 'Win', 'ThreeDay_Win']].tail(20)
    styled_df.index.name = '日期'
    styled_df.reset_index(inplace=True)
    styled_df = styled_df.rename(columns={
        'close': '收盤價',
        'Next_Open': '隔日開盤',
        'Day3_Close': '第三日收盤',
        'Overnight_Change': '隔日漲幅%',
        'ThreeDay_Change': '三日漲幅%',
        'Win': f'隔日是否 ≥ {threshold}%',
        'ThreeDay_Win': '三日是否 ≥ 2.5%'
    })
    st.dataframe(styled_df.round(2), use_container_width=True, height=800)

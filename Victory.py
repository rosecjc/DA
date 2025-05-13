# 分析工具（twstock 為主 + TSE法人與收盤價補充）
import matplotlib
from matplotlib import font_manager
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import twstock

# 字體設定
font_path = "./fonts/NotoSansTC-VariableFont_wght.ttf"
font_prop = font_manager.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="隔日沖勝率工具", layout="wide")

# 取得今日法人買賣資訊
@st.cache_data
def fetch_tse_institution_data(stock_id):
    today = datetime.today().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/fund/T86?response=json&date={today}&selectType=ALL&_=1683631540000"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    data = res.json()
    for entry in data.get("data", []):
        if entry[0] == stock_id:
            return {
                "外資買賣超": entry[4],
                "投信買賣超": entry[7],
                "自營商買賣超": entry[10]
            }
    return None

# 取得今日收盤價
@st.cache_data
def fetch_tse_closing_price(stock_id):
    today = datetime.today().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date={today}&type=ALL"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    data = res.json()
    for entry in data.get("data9", []):
        if entry[0].strip() == stock_id:
            return entry[8]  # 收盤價
    return None

# 建立資料清單（你提供的股票）
custom_codes = ['1528', '6165', '4533', '1536', '6547', '4303', '3312', '2009']
st.title("📊 精選台股資訊（含法人買賣＋即時收盤）")

rows = []
for code in custom_codes:
    name = twstock.codes.get(code, {}).get('name', code)
    price = fetch_tse_closing_price(code)
    inst = fetch_tse_institution_data(code)
    row = {
        "股票代號": code,
        "股票名稱": name,
        "今日收盤價": price if price else "-",
        "外資買賣超": inst["外資買賣超"] if inst else "-",
        "投信買賣超": inst["投信買賣超"] if inst else "-",
        "自營商買賣超": inst["自營商買賣超"] if inst else "-"
    }
    rows.append(row)

st.dataframe(pd.DataFrame(rows), use_container_width=True)

st.caption("📌 數據來源：台灣證券交易所 TSE")

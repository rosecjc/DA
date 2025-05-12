# 📊 台股隔日沖勝率分析工具（Streamlit + twstock）

這是一個基於 Python 與 Streamlit 的視覺化小工具，可用來分析台股的隔日與三日沖勝率，並搭配圖表顯示報酬分布情況。

---

## 🔧 功能特色

- 以 twstock 為資料來源，即時擷取開盤與收盤價
- 自訂回測天數與漲幅門檻
- 計算隔日沖與三日沖的勝率、平均報酬與最大跌幅
- 中文圖表支援（自帶字體檔）

---

## 🧱 專案結構
.
├── app.py # 主程式
├── fonts/
│ └── NotoSansTC-Regular.otf # 中文字體（Google Fonts 下載）
├── requirements.txt # Python 套件需求
└── README.md # 專案說明

---

## 🔤 字體設定（顯示中文）

請前往 [Google Fonts：Noto Sans TC](https://fonts.google.com/specimen/Noto+Sans+TC)  
下載 `NotoSansTC-Regular.otf` 並放入 `fonts/` 資料夾。

程式會自動載入該字體來正確顯示圖表中的中文文字。

---

## ☁️ 線上部署方式

1. 將本專案 push 到 GitHub 公開 repo
2. 登入 [Streamlit Cloud](https://streamlit.io/cloud)
3. 點選 `New app` → 選擇 repo → 指定主程式為 `app.py`
4. 點選 Deploy！🎉

> ✅ 注意：`fonts/NotoSansTC-Regular.otf` 必須在 repo 中，否則圖表中文字會無法顯示。

---

## 📷 預覽畫面

（你可以貼上範例截圖）

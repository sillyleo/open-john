---
name: crypto-analyzer
description: >
  專業加密貨幣市場情報分析技能。提供 BTC 市場深度掃描（含宏觀指標 DXY/US10Y/SP500/WTI、即時新聞、技術分析）、
  多週期共振分析（1H/4H/1D/3D）、流動性插針與槓桿清算價計算。
  當用戶提到加密貨幣、BTC、ETH、幣圈、技術分析、K線、支撐阻力、資金費率、插針、清算、
  多空比、市場情緒、宏觀指標、或任何幣種代號（如 SOL、SUI、DOGE）時，都應觸發此技能。
  即使用戶只是隨口問「現在盤面怎樣」或「幫我看一下大餅」，也要使用此技能。
---

# Crypto Analyzer — 純情報分析技能

## 身份
你是一位專業加密貨幣市場情報官。
此技能僅提供市場數據分析、多週期共振看盤與流動性插針測算，**不包含任何交易執行或資產追蹤能力**。所有數據皆來自公開 API（Binance、Yahoo Finance），不需要任何 API Key。

## 前置需求
```bash
pip install -r requirements.txt
```

## 可用腳本

所有腳本位於 plugin 的 `scripts/` 目錄。
如果作為 plugin 安裝，MCP server 會自動啟動，你可以直接呼叫 MCP tools（btc_market_data、mtf_trend_analysis、needle_stick_analysis）而不需手動執行腳本。
如果是用 `--skill` 直接載入，請用以下命令執行腳本：

### 1. BTC 市場深度分析
```bash
python3 scripts/btc_market_data.py
```
輸出包含：宏觀環境（美股狀態、DXY、US10Y、SP500、WTI）、即時新聞頭條、BTC 即時價格、4H/1D 技術指標（RSI、MA、布林通道）、關鍵支撐阻力位、資金費率、持倉量、成交量動態、風險評估。

### 2. 多週期共振分析
```bash
python3 scripts/mtf_trend_master.py [SYMBOL]
```
SYMBOL 預設為 BTC，支援任何 Binance 上的幣種（如 ETH、SOL、SUI）。
分析 1H→4H→1D→3D 四個週期的 RSI、MACD、EMA 排列、布林寬度、ATR，給出 -2 到 +2 的趨勢評分與綜合研判。

### 3. 流動性插針計算器
```bash
python3 scripts/needle_stick_v2.py [SYMBOL]
```
SYMBOL 預設為 BTC。計算多空賬戶比、資金費率、擠壓信號、槓桿清算價（50x/100x）、止損集群、ATR 延伸目標、心理關價、FVG 缺口，輸出插針候選位與交易建議。

## 使用指引
- 用戶問「現在盤面怎樣」→ 先跑腳本 1，再根據結果解讀
- 用戶問「X幣趨勢」→ 跑腳本 2，帶入對應 SYMBOL
- 用戶問「哪裡可能插針」或「清算價在哪」→ 跑腳本 3
- 可以組合使用多個腳本提供完整分析
- 輸出結果後，用你的專業知識為用戶做人話解讀，不要只丟 raw data

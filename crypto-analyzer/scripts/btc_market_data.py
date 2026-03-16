from datetime import datetime, timezone
#!/usr/bin/env python3
import requests
import json
import math


def get_kline_data(symbol="BTCUSDT", interval="4h", limit=50):
    """獲取K線數據"""
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    # 轉換為字典格式
    processed_data = []
    for row in data:
        processed_data.append({
            'timestamp': int(row[0]),
            'open': float(row[1]),
            'high': float(row[2]),
            'low': float(row[3]),
            'close': float(row[4]),
            'volume': float(row[5])
        })
    
    return processed_data

def get_24hr_stats(symbol="BTCUSDT"):
    """獲取24小時行情統計"""
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    response = requests.get(url)
    return response.json()

def get_funding_rate(symbol="BTCUSDT", limit=5):
    """獲取資金費率"""
    url = "https://fapi.binance.com/fapi/v1/fundingRate"
    params = {
        'symbol': symbol,
        'limit': limit
    }
    response = requests.get(url, params=params)
    return response.json()

def get_open_interest(symbol="BTCUSDT"):
    """獲取持倉量"""
    url = "https://fapi.binance.com/fapi/v1/openInterest"
    params = {'symbol': symbol}
    response = requests.get(url, params=params)
    return response.json()


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    if len(prices) < period: return None, None, None
    recent = prices[-period:]
    sma = sum(recent) / period
    variance = sum((x - sma) ** 2 for x in recent) / period
    std = math.sqrt(variance)
    return sma + (std_dev * std), sma, sma - (std_dev * std)

def calculate_atr(klines, period=14):
    if len(klines) < period + 1: return None
    trs = []
    for i in range(1, len(klines)):
        h, l, pc = klines[i]["high"], klines[i]["low"], klines[i-1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    atr = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr = (atr * (period - 1) + trs[i]) / period
    return atr

def calculate_rsi(prices, period=14):
    """計算RSI"""
    if len(prices) < period + 1:
        return None
    
    deltas = []
    for i in range(1, len(prices)):
        deltas.append(prices[i] - prices[i-1])
    
    gains = [delta if delta > 0 else 0 for delta in deltas]
    losses = [-delta if delta < 0 else 0 for delta in deltas]
    
    # 計算第一個RSI值
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    # 使用指數移動平均計算後續RSI
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_ma(prices, period):
    """計算移動平均"""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def check_us_market_status():
    """檢查美股是否開盤 (簡易判斷)"""
    now_utc = datetime.now(timezone.utc)
    # 簡易判斷 2026 夏令時 (3月8日已開始, EDT=UTC-4)
    is_dst = (now_utc.month > 3 and now_utc.month < 11) or (now_utc.month == 3 and now_utc.day >= 8) or (now_utc.month == 11 and now_utc.day <= 1)
    
    if is_dst:
        open_m = 13 * 60 + 30
        close_m = 20 * 60
    else:
        open_m = 14 * 60 + 30
        close_m = 21 * 60

    is_weekday = now_utc.weekday() < 5
    curr_m = now_utc.hour * 60 + now_utc.minute
    
    if is_weekday and open_m <= curr_m < close_m:
        return "🟢 美股開盤中 (機構活躍時間)"
    elif not is_weekday:
        return "🔴 週末休市 (流動性較差)"
    else:
        return "🔴 美股盤外時間 (亞洲/歐洲盤)"


def get_macro_data():
    """獲取宏觀金融數據 (Yahoo Finance)"""
    symbols = {
        "DXY (美元指數)": "DX-Y.NYB",
        "US10Y (美債10年)": "^TNX",
        "S&P 500 (標普)": "^GSPC",
        "WTI (原油)": "CL=F"
    }
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    macro_info = {}
    for name, sym in symbols.items():
        try:
            url = f"https://query2.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=2d"
            r = requests.get(url, headers=headers, timeout=5)
            data = r.json()
            current = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            prev_close = data["chart"]["result"][0]["meta"]["chartPreviousClose"]
            pct_change = ((current - prev_close) / prev_close) * 100
            macro_info[name] = {"price": current, "change": pct_change}
        except Exception as e:
            macro_info[name] = None
    return macro_info


def get_macro_news():
    """獲取最新市場頭條新聞 (Yahoo Finance)"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    url = "https://query2.finance.yahoo.com/v1/finance/search?q=crypto%20inflation%20market&quotesCount=0&newsCount=3"
    try:
        r = requests.get(url, headers=headers, timeout=5)
        news_items = r.json().get("news", [])
        headlines = []
        for item in news_items:
            title = item.get("title", "")
            pub = item.get("publisher", "News")
            if title:
                headlines.append(f"[{pub}] {title}")
        return headlines if headlines else ["目前無重大新聞"]
    except Exception as e:
        return ["暫時無法獲取新聞頭條"]

def analyze_btc_market():
    """完整的BTC市場分析"""
    print("🔍 比特幣市場深度分析 - " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    print("=" * 60)
    
    market_status = check_us_market_status()
    print(f"🌍 **宏觀環境**: {market_status}")
    
    macro_data = get_macro_data()
    for name, data in macro_data.items():
        if data:
            indicator = "🟢" if data["change"] > 0 else "🔴"
            # 對於避險資產/通膨指標，上漲為紅(利空BTC)，下跌為綠(利好BTC)
            if "US10Y" in name or "DXY" in name or "WTI" in name:
                indicator = "🔴" if data["change"] > 0 else "🟢"
            
            # 格式化輸出
            if "US10Y" in name:
                print(f"   {name}: {data["price"]:.3f}% ({data["change"]:+.2f}%) {indicator}")
            else:
                print(f"   {name}: {data["price"]:,.2f} ({data["change"]:+.2f}%) {indicator}")
        else:
            print(f"   {name}: 數據暫時無法獲取")
    
    print("   📰 **即時新聞頭條**:")
    news_headlines = get_macro_news()
    for headline in news_headlines:
        print(f"      - {headline}")
    print()
    
    # 獲取基礎數據
    stats_24h = get_24hr_stats()
    kline_4h = get_kline_data(interval="4h", limit=50)
    kline_1d = get_kline_data(interval="1d", limit=30)
    funding = get_funding_rate()
    oi = get_open_interest()
    
    current_price = float(stats_24h['lastPrice'])
    price_change_24h = float(stats_24h['priceChangePercent'])
    volume_24h = float(stats_24h['volume'])
    
    print(f"📊 **當前價格**: ${current_price:,.2f}")
    print(f"📈 **24H變化**: {price_change_24h:+.2f}%")
    print(f"📦 **24H成交量**: {volume_24h:,.0f} BTC")
    print()
    
    # 技術指標分析 - 4H
    print("🕐 **4H 技術指標**")
    close_4h = [k['close'] for k in kline_4h]
    rsi_4h = calculate_rsi(close_4h)
    ma7_4h = calculate_ma(close_4h, 7)
    ma25_4h = calculate_ma(close_4h, 25)
    ma99_4h = calculate_ma(close_4h, 99)
    
    print(f"   RSI(14): {rsi_4h:.1f}", end="")
    if rsi_4h > 70:
        print(" (超買)")
    elif rsi_4h < 30:
        print(" (超賣)")
    else:
        print(" (中性)")
    
    if ma7_4h: print(f"   MA7: ${ma7_4h:,.2f}")
    if ma25_4h: print(f"   MA25: ${ma25_4h:,.2f}")
    if ma99_4h: print(f"   MA99: ${ma99_4h:,.2f}")
    # 布林通道 (4H)
    upper_bb, mid_bb, lower_bb = calculate_bollinger_bands(close_4h)
    if upper_bb:
        bandwidth = (upper_bb - lower_bb) / mid_bb * 100
        print(f"   布林通道(20,2): 上軌 ${upper_bb:,.2f} | 下軌 ${lower_bb:,.2f}")
        print(f"   通道寬度: {bandwidth:.2f}% ", end="")
        if bandwidth < 4.0: print("(極度收斂 ⚠️ 即將變盤)")
        elif bandwidth > 10.0: print("(開口發散 🌊 波動劇烈)")
        else: print("(正常)")

    
    # 均線位置判斷
    if ma7_4h and ma25_4h and current_price > ma7_4h > ma25_4h:
        ma_trend_4h = "強勢上升"
    elif ma7_4h and ma25_4h and current_price < ma7_4h < ma25_4h:
        ma_trend_4h = "弱勢下跌"
    else:
        ma_trend_4h = "震盪整理"
    
    print(f"   均線趨勢: {ma_trend_4h}")
    print()
    
    # 技術指標分析 - 日線
    print("📅 **日線技術指標**")
    close_1d = [k['close'] for k in kline_1d]
    rsi_1d = calculate_rsi(close_1d)
    ma7_1d = calculate_ma(close_1d, 7)
    ma25_1d = calculate_ma(close_1d, 25)
    ma99_1d = calculate_ma(close_1d, 99)
    
    print(f"   RSI(14): {rsi_1d:.1f}", end="")
    if rsi_1d > 70:
        print(" (超買)")
    elif rsi_1d < 30:
        print(" (超賣)")
    else:
        print(" (中性)")
    
    if ma7_1d: print(f"   MA7: ${ma7_1d:,.2f}")
    if ma25_1d: print(f"   MA25: ${ma25_1d:,.2f}")
    if ma99_1d: print(f"   MA99: ${ma99_1d:,.2f}")
    # ATR 真實波動幅度 (1D)
    atr_1d = calculate_atr(kline_1d)
    if atr_1d:
        print(f"   ATR(14) 日均波動: ${atr_1d:,.0f} (約 {(atr_1d/current_price)*100:.1f}%)")

    print()
    
    # 支撐阻力位分析
    print("🎯 **關鍵價格水平**")
    high_4h_10 = [k['high'] for k in kline_4h[-10:]]
    low_4h_10 = [k['low'] for k in kline_4h[-10:]]
    
    resistance_1 = max(high_4h_10)
    high_4h_sorted = sorted(high_4h_10, reverse=True)
    resistance_2 = high_4h_sorted[1] if len(high_4h_sorted) > 1 else resistance_1
    
    support_1 = min(low_4h_10)
    low_4h_sorted = sorted(low_4h_10)
    support_2 = low_4h_sorted[1] if len(low_4h_sorted) > 1 else support_1
    
    print(f"   近期阻力位 1: ${resistance_1:,.2f}")
    print(f"   近期阻力位 2: ${resistance_2:,.2f}")
    print(f"   近期支撐位 1: ${support_1:,.2f}")
    print(f"   近期支撐位 2: ${support_2:,.2f}")
    
    # 資金費率
    print("💰 **資金費率**")
    current_funding = float(funding[0]['fundingRate']) * 100
    print(f"   當前費率: {current_funding:.4f}%", end="")
    if current_funding > 0.02:
        print(" (多頭擁擠)")
    elif current_funding < -0.02:
        print(" (空頭擁擠)")
    else:
        print(" (中性)")
    
    funding_trend = []
    for f in funding[:3]:
        funding_trend.append(float(f['fundingRate']) * 100)
    print(f"   趨勢: {funding_trend[0]:.4f}% → {funding_trend[1]:.4f}% → {funding_trend[2]:.4f}%")
    print()
    
    # 持倉量
    print("📊 **持倉量**")
    oi_value = float(oi['openInterest'])
    print(f"   當前持倉量: {oi_value:,.0f} BTC")
    print()
    
    # 成交量分析
    print("📦 **成交量分析 (動態預估修正版)**")
    
    # 計算上一根已收盤的 10 期平均，避免被未完成的 K 線干擾
    volumes_closed_4h = [k["volume"] for k in kline_4h[-11:-1]]
    if not volumes_closed_4h:
        volumes_closed_4h = [k["volume"] for k in kline_4h[-10:]]
    volume_avg_4h = sum(volumes_closed_4h) / len(volumes_closed_4h)
    
    # 計算當前 K 線進度與推算總量
    volume_current = kline_4h[-1]["volume"]
    candle_start_ms = kline_4h[-1]["timestamp"]
    
    now_ms = datetime.now(timezone.utc).timestamp() * 1000
    elapsed_hours = (now_ms - candle_start_ms) / 3600000.0
    
    if elapsed_hours <= 0.05:
        elapsed_hours = 0.05
    elif elapsed_hours > 4:
        elapsed_hours = 4
        
    projected_volume = volume_current * (4 / elapsed_hours)
    volume_ratio = projected_volume / volume_avg_4h
    
    print(f"   當前 K 線已走時間: {elapsed_hours:.1f} 小時 ({elapsed_hours/4*100:.0f}%)")
    print(f"   當前實際成交量: {volume_current:,.0f} BTC")
    print(f"   推算 4H 完整成交量: {projected_volume:,.0f} BTC")
    print(f"   10期平均(已收盤): {volume_avg_4h:,.0f} BTC")
    print(f"   預估比值: {volume_ratio:.2f}x", end="")
    
    # 如果 K 線剛開始不到 1 小時，警告推算可能不準確
    if elapsed_hours < 1.0:
        print(" (⚠️ 開盤不久，推算可能有誤差)")
    else:
        if volume_ratio > 1.5:
            print(" (放量 🟢)")
        elif volume_ratio < 0.7:
            print(" (縮量 🔴)")
        else:
            print(" (正常 🟡)")
    print()
    
    # 風險評估
    print("⚠️ **風險與機會評估**")
    
    # 市場情緒
    sentiment_score = 0
    if rsi_4h > 70: sentiment_score -= 1
    if rsi_4h < 30: sentiment_score += 1
    if current_funding > 0.02: sentiment_score -= 1
    if current_funding < -0.02: sentiment_score += 1
    if volume_ratio > 1.5: sentiment_score += 0.5
    
    if sentiment_score > 0.5:
        market_sentiment = "偏多"
    elif sentiment_score < -0.5:
        market_sentiment = "偏空"
    else:
        market_sentiment = "中性"
    
    print(f"   市場情緒: {market_sentiment}")
    print()
    
    return {
        'current_price': current_price,
        'rsi_4h': rsi_4h,
        'rsi_1d': rsi_1d,
        'funding_rate': current_funding,
        'market_sentiment': market_sentiment,
        'ma_trend_4h': ma_trend_4h
    }

if __name__ == "__main__":
    analyze_btc_market()
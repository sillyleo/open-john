#!/usr/bin/env python3
"""
Needle-stick Calculator v2.0 - Synthetic Liquidity Mapping
Based on professional "Counter-Trading Formula" without paid heatmaps.

Features:
- Long/Short Ratio analysis
- Funding Rate squeeze detection
- ATR-based liquidation extension (0.5x-1.0x ATR)
- Leverage-based LP calculation (50x/100x)
- Fair Value Gap (FVG) identification
- Psychological front-running ($69,980 not $70,000)

Usage:
    python3 needle_stick_v2.py BTC
    python3 needle_stick_v2.py ETH
    python3 needle_stick_v2.py SUI
"""

import sys
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta

BINANCE_BASE_URL = "https://api.binance.com/api/v3"
BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1"

def get_klines(symbol, interval, limit=500):
    """Get historical kline data from Binance"""
    url = f"{BINANCE_BASE_URL}/klines"
    params = {
        "symbol": f"{symbol}USDT",
        "interval": interval,
        "limit": limit
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None
    
    data = response.json()
    klines = []
    for k in data:
        klines.append({
            "timestamp": k[0],
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5])
        })
    return klines

def get_current_price(symbol):
    """Get current price"""
    url = f"{BINANCE_BASE_URL}/ticker/price"
    params = {"symbol": f"{symbol}USDT"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return float(response.json()["price"])
    return None

def get_long_short_ratio(symbol):
    """Get Long/Short Account Ratio from Binance Futures"""
    url = f"{BINANCE_FUTURES_URL}/globalLongShortAccountRatio"
    params = {
        "symbol": f"{symbol}USDT",
        "period": "5m",
        "limit": 1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data:
            ratio = float(data[0]["longShortRatio"])
            long_pct = ratio / (1 + ratio) * 100
            short_pct = 100 - long_pct
            return {
                "ratio": ratio,
                "long_pct": long_pct,
                "short_pct": short_pct
            }
    return None

def get_funding_rate(symbol):
    """Get current Funding Rate from Binance Futures"""
    url = f"{BINANCE_FUTURES_URL}/fundingRate"
    params = {
        "symbol": f"{symbol}USDT",
        "limit": 1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data:
            return float(data[0]["fundingRate"]) * 100  # Convert to %
    return None

def get_open_interest(symbol):
    """Get Open Interest from Binance Futures"""
    url = f"{BINANCE_FUTURES_URL}/openInterest"
    params = {"symbol": f"{symbol}USDT"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return float(data["openInterest"])
    return None

def calculate_atr(klines, period=14):
    """Calculate Average True Range"""
    if len(klines) < period:
        return 0
    
    true_ranges = []
    for i in range(1, len(klines)):
        high = klines[i]["high"]
        low = klines[i]["low"]
        prev_close = klines[i-1]["close"]
        
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        true_ranges.append(tr)
    
    return sum(true_ranges[-period:]) / period

def find_swing_highs_lows(klines, lookback=3):
    """Find recent swing highs and lows (last 3)"""
    swing_highs = []
    swing_lows = []
    
    for i in range(lookback, len(klines) - lookback):
        # Swing High: higher than neighbors
        is_high = all(klines[i]["high"] >= klines[j]["high"] 
                      for j in range(i-lookback, i+lookback+1) if j != i)
        if is_high:
            swing_highs.append(klines[i]["high"])
        
        # Swing Low: lower than neighbors
        is_low = all(klines[i]["low"] <= klines[j]["low"] 
                     for j in range(i-lookback, i+lookback+1) if j != i)
        if is_low:
            swing_lows.append(klines[i]["low"])
    
    return sorted(swing_highs[-3:], reverse=True), sorted(swing_lows[-3:])

def find_fair_value_gaps(klines, min_gap_pct=0.5):
    """
    Find Fair Value Gaps (FVG) - price gaps that act as magnets.
    FVG occurs when there's a gap between candle 1's high and candle 3's low (or vice versa).
    """
    fvgs = []
    
    for i in range(2, len(klines)):
        candle1 = klines[i-2]
        candle2 = klines[i-1]
        candle3 = klines[i]
        
        # Bullish FVG: gap between candle1 high and candle3 low
        if candle3["low"] > candle1["high"]:
            gap_size = candle3["low"] - candle1["high"]
            gap_pct = (gap_size / candle1["high"]) * 100
            
            if gap_pct >= min_gap_pct:
                fvgs.append({
                    "type": "bullish",
                    "top": candle3["low"],
                    "bottom": candle1["high"],
                    "mid": (candle3["low"] + candle1["high"]) / 2,
                    "size_pct": gap_pct,
                    "timestamp": candle3["timestamp"]
                })
        
        # Bearish FVG: gap between candle1 low and candle3 high
        if candle3["high"] < candle1["low"]:
            gap_size = candle1["low"] - candle3["high"]
            gap_pct = (gap_size / candle3["high"]) * 100
            
            if gap_pct >= min_gap_pct:
                fvgs.append({
                    "type": "bearish",
                    "top": candle1["low"],
                    "bottom": candle3["high"],
                    "mid": (candle1["low"] + candle3["high"]) / 2,
                    "size_pct": gap_pct,
                    "timestamp": candle3["timestamp"]
                })
    
    # Return most recent FVGs
    return sorted(fvgs, key=lambda x: x["timestamp"], reverse=True)[:3]

def calculate_liquidation_price(entry_price, leverage, direction="long"):
    """
    Calculate liquidation price for leveraged positions.
    LP ≈ Entry × (1 ± 1/Leverage)
    """
    if direction == "long":
        # Long liquidation: price drops
        lp = entry_price * (1 - 1/leverage)
    else:
        # Short liquidation: price rises
        lp = entry_price * (1 + 1/leverage)
    
    return lp

def calculate_psychological_frontrun(round_number, below=True):
    """
    Calculate psychological front-running levels.
    Large orders cluster $10-$50 ahead of major round numbers.
    """
    if below:
        # For support: $69,980 instead of $70,000
        if round_number >= 10000:
            return round_number - 20
        elif round_number >= 1000:
            return round_number - 10
        else:
            return round_number - 0.02
    else:
        # For resistance: $70,020 instead of $70,000
        if round_number >= 10000:
            return round_number + 20
        elif round_number >= 1000:
            return round_number + 10
        else:
            return round_number + 0.02

def detect_squeeze_condition(current_price, klines_4h, ls_ratio, funding_rate, open_interest):
    """
    Detect Long Squeeze or Short Squeeze conditions.
    
    Condition A (Long Squeeze):
    - Price hitting 4H High
    - Funding Rate highly positive (>0.03%)
    - Open Interest rising
    → Downward needle imminent
    
    Condition B (Short Squeeze):
    - Price at 4H Low
    - Long/Short Ratio < 0.8
    - Open Interest spiking
    → Upward needle imminent
    """
    recent_high = max(k["high"] for k in klines_4h[-6:])  # Last 24h
    recent_low = min(k["low"] for k in klines_4h[-6:])
    
    near_high = abs(current_price - recent_high) / recent_high < 0.01  # Within 1%
    near_low = abs(current_price - recent_low) / recent_low < 0.01
    
    squeeze_type = None
    confidence = 0
    
    # Long Squeeze Detection
    if near_high:
        if funding_rate and funding_rate > 0.03:
            confidence += 40
        if ls_ratio and ls_ratio["ratio"] > 1.2:  # More longs than shorts
            confidence += 30
        if open_interest:
            confidence += 30
        
        if confidence >= 60:
            squeeze_type = "long_squeeze"
    
    # Short Squeeze Detection
    if near_low:
        if ls_ratio and ls_ratio["ratio"] < 0.8:  # More shorts than longs
            confidence += 40
        if funding_rate and funding_rate < -0.01:
            confidence += 30
        if open_interest:
            confidence += 30
        
        if confidence >= 60:
            squeeze_type = "short_squeeze"
    
    return squeeze_type, confidence

def calculate_needle_targets(current_price, swing_lows, swing_highs, atr, ls_ratio, fvgs, klines_4h):
    """
    Calculate precise needle-stick targets using Counter-Trading Formula.
    
    Downward Needle:
    - Recent Long LP: Liquidation of longs opened at recent 4H high
    - Retail Stop Cluster: 0.3%-0.6% below swing low
    - ATR Extension: 0.5x-1.0x ATR beyond support
    - FVG Target: 50%-100% fill of nearest bearish FVG
    
    Upward Needle:
    - Recent Short LP: Liquidation of shorts opened at recent 4H low
    - Short Stop Cluster: 0.3%-0.6% above swing high
    - ATR Extension: 0.5x-1.0x ATR beyond resistance
    - FVG Target: 50%-100% fill of nearest bullish FVG
    """
    
    targets = {
        "downward": [],
        "upward": []
    }
    
    # Calculate liquidation prices for multiple recent entry points
    # Check last 48h (12 x 4H candles) for potential entry zones
    recent_candles = klines_4h[-12:]
    recent_highs_for_lp = sorted([k["high"] for k in recent_candles], reverse=True)[:3]
    recent_lows_for_lp = sorted([k["low"] for k in recent_candles])[:3]
    
    # Add recent LP targets (HIGH PRIORITY)
    for entry_high in recent_highs_for_lp:
        # Skip if entry is too close to current price
        if abs(entry_high - current_price) / current_price < 0.01:
            continue
        
        lp_50x = calculate_liquidation_price(entry_high, 50, "long")
        lp_100x = calculate_liquidation_price(entry_high, 100, "long")
        
        if lp_50x < current_price:
            targets["downward"].append({
                "price": lp_50x,
                "type": f"50x Long LP (Entry @ ${entry_high:,.2f})",
                "confidence": 90
            })
        
        if lp_100x < current_price:
            targets["downward"].append({
                "price": lp_100x,
                "type": f"100x Long LP (Entry @ ${entry_high:,.2f})",
                "confidence": 85
            })
    
    for entry_low in recent_lows_for_lp:
        # Skip if entry is too close to current price
        if abs(entry_low - current_price) / current_price < 0.01:
            continue
        
        lp_50x = calculate_liquidation_price(entry_low, 50, "short")
        lp_100x = calculate_liquidation_price(entry_low, 100, "short")
        
        if lp_50x > current_price:
            targets["upward"].append({
                "price": lp_50x,
                "type": f"50x Short LP (Entry @ ${entry_low:,.2f})",
                "confidence": 90
            })
        
        if lp_100x > current_price:
            targets["upward"].append({
                "price": lp_100x,
                "type": f"100x Short LP (Entry @ ${entry_low:,.2f})",
                "confidence": 85
            })
    
    # Downward Needle Targets
    for swing_low in swing_lows:
        # Retail stop cluster (0.3%-0.6% below)
        retail_stop = swing_low * 0.997  # 0.3% below
        deep_stop = swing_low * 0.994    # 0.6% below
        
        # ATR extension
        atr_target_05x = swing_low - (atr * 0.5)
        atr_target_10x = swing_low - (atr * 1.0)
        
        # Psychological front-running
        round_below = (swing_low // 1000) * 1000 if swing_low > 1000 else (swing_low // 100) * 100
        psych_frontrun = calculate_psychological_frontrun(round_below, below=True)
        
        targets["downward"].extend([
            {"price": retail_stop, "type": "Retail Stop Cluster (0.3%)", "confidence": 70},
            {"price": deep_stop, "type": "Deep Stop Cluster (0.6%)", "confidence": 80},
            {"price": atr_target_05x, "type": "ATR 0.5x Extension", "confidence": 75},
            {"price": atr_target_10x, "type": "ATR 1.0x Extension", "confidence": 85},
            {"price": psych_frontrun, "type": "Psychological Front-Run", "confidence": 65}
        ])
    
    # Upward Needle Targets
    for swing_high in swing_highs:
        # Short stop cluster (0.3%-0.6% above)
        short_stop = swing_high * 1.003
        deep_short = swing_high * 1.006
        
        # ATR extension
        atr_target_05x = swing_high + (atr * 0.5)
        atr_target_10x = swing_high + (atr * 1.0)
        
        # Psychological front-running
        round_above = ((swing_high // 1000) + 1) * 1000 if swing_high > 1000 else ((swing_high // 100) + 1) * 100
        psych_frontrun = calculate_psychological_frontrun(round_above, below=False)
        
        targets["upward"].extend([
            {"price": short_stop, "type": "Short Stop Cluster (0.3%)", "confidence": 70},
            {"price": deep_short, "type": "Deep Short Cluster (0.6%)", "confidence": 80},
            {"price": atr_target_05x, "type": "ATR 0.5x Extension", "confidence": 75},
            {"price": atr_target_10x, "type": "ATR 1.0x Extension", "confidence": 85},
            {"price": psych_frontrun, "type": "Psychological Front-Run", "confidence": 65}
        ])
    
    # Add FVG targets
    for fvg in fvgs:
        if fvg["type"] == "bearish":
            targets["downward"].append({
                "price": fvg["mid"],
                "type": f"FVG 50% Fill ({fvg['size_pct']:.2f}% gap)",
                "confidence": 80
            })
        else:
            targets["upward"].append({
                "price": fvg["mid"],
                "type": f"FVG 50% Fill ({fvg['size_pct']:.2f}% gap)",
                "confidence": 80
            })
    
    # Filter to only include targets near current price (within ±15%)
    targets["downward"] = [t for t in targets["downward"] 
                           if 0.85 * current_price <= t["price"] < current_price]
    targets["upward"] = [t for t in targets["upward"] 
                         if current_price < t["price"] <= 1.15 * current_price]
    
    # Sort by confidence
    targets["downward"].sort(key=lambda x: x["confidence"], reverse=True)
    targets["upward"].sort(key=lambda x: x["confidence"], reverse=True)
    
    return targets

def analyze_needle_stick_v2(symbol):
    """Main analysis function with Synthetic Liquidity Mapping"""
    print(f"\n{'='*75}")
    print(f"🎯 {symbol} Needle-stick v2.0 - Synthetic Liquidity Mapping")
    print(f"{'='*75}\n")
    
    # Get current price
    current_price = get_current_price(symbol)
    if not current_price:
        print("❌ 無法獲取當前價格")
        return
    
    print(f"💰 當前價格: ${current_price:,.2f}\n")
    
    # Fetch data
    print("📊 正在獲取市場數據...\n")
    klines_1h = get_klines(symbol, "1h", limit=100)
    klines_4h = get_klines(symbol, "4h", limit=168)
    klines_1d = get_klines(symbol, "1d", limit=90)
    
    if not all([klines_1h, klines_4h, klines_1d]):
        print("❌ K線數據獲取失敗")
        return
    
    # Get futures data
    ls_ratio = get_long_short_ratio(symbol)
    funding_rate = get_funding_rate(symbol)
    open_interest = get_open_interest(symbol)
    
    # Calculate indicators
    atr_4h = calculate_atr(klines_4h, 14)
    atr_1d = calculate_atr(klines_1d, 14)
    swing_highs, swing_lows = find_swing_highs_lows(klines_4h)
    fvgs = find_fair_value_gaps(klines_1h)
    
    # 1. Market Sentiment
    print("📈 市場情緒指標 (Market Sentiment):\n")
    
    if ls_ratio:
        print(f"  Long/Short Ratio: {ls_ratio['ratio']:.2f}")
        print(f"  └─ Long Accounts: {ls_ratio['long_pct']:.1f}%")
        print(f"  └─ Short Accounts: {ls_ratio['short_pct']:.1f}%")
        
        if ls_ratio['ratio'] > 1.5:
            print(f"  🔴 多頭過度擁擠 → 下插針風險高")
        elif ls_ratio['ratio'] < 0.7:
            print(f"  🟢 空頭過度擁擠 → 上插針風險高")
    else:
        print(f"  ⚠️ Long/Short Ratio: 數據不可用")
    
    print()
    
    if funding_rate is not None:
        print(f"  Funding Rate: {funding_rate:.4f}%")
        
        if funding_rate > 0.03:
            print(f"  🔴 資費率過高 → 多頭付費，下插針可能")
        elif funding_rate < -0.01:
            print(f"  🟢 資費率負值 → 空頭付費，上插針可能")
    else:
        print(f"  ⚠️ Funding Rate: 數據不可用")
    
    print()
    
    if open_interest:
        print(f"  Open Interest: {open_interest:,.0f} {symbol}")
    
    print()
    
    # 2. Squeeze Detection
    squeeze_type, confidence = detect_squeeze_condition(
        current_price, klines_4h, ls_ratio, funding_rate, open_interest
    )
    
    if squeeze_type:
        print(f"⚠️ 檢測到 {squeeze_type.upper().replace('_', ' ')} (信心度: {confidence}%)\n")
        if squeeze_type == "long_squeeze":
            print(f"  → 預期: 下插針以清算過度槓桿的多頭")
        else:
            print(f"  → 預期: 上插針以清算過度槓桿的空頭")
        print()
    
    # 3. ATR & Swing Levels
    print(f"{'='*75}")
    print("📏 技術指標 (Technical Indicators):\n")
    print(f"  ATR (4H): ${atr_4h:,.2f}")
    print(f"  ATR (1D): ${atr_1d:,.2f}\n")
    
    print(f"  Recent Swing Highs (4H):")
    for i, high in enumerate(swing_highs, 1):
        dist = ((high - current_price) / current_price * 100)
        print(f"    {i}. ${high:,.2f} ({dist:+.2f}%)")
    
    print(f"\n  Recent Swing Lows (4H):")
    for i, low in enumerate(swing_lows, 1):
        dist = ((low - current_price) / current_price * 100)
        print(f"    {i}. ${low:,.2f} ({dist:+.2f}%)")
    
    print()
    
    # 4. Fair Value Gaps
    if fvgs:
        print(f"🔍 Fair Value Gaps (FVG - 價格缺口磁吸):\n")
        for i, fvg in enumerate(fvgs, 1):
            fvg_type = "🟢 Bullish" if fvg["type"] == "bullish" else "🔴 Bearish"
            dist = ((fvg["mid"] - current_price) / current_price * 100)
            print(f"  {i}. {fvg_type} FVG: ${fvg['mid']:,.2f} ({dist:+.2f}%)")
            print(f"     └─ Range: ${fvg['bottom']:,.2f} - ${fvg['top']:,.2f} ({fvg['size_pct']:.2f}% gap)")
        print()
    
    # 5. Leverage Liquidation Prices
    print(f"{'='*75}")
    print("💥 槓桿清算價計算 (Leverage Liquidation Prices):\n")
    
    print(f"  如果在 ${current_price:,.2f} 開倉:")
    print(f"    50x Long LP:  ${calculate_liquidation_price(current_price, 50, 'long'):,.2f}")
    print(f"    100x Long LP: ${calculate_liquidation_price(current_price, 100, 'long'):,.2f}")
    print(f"    50x Short LP:  ${calculate_liquidation_price(current_price, 50, 'short'):,.2f}")
    print(f"    100x Short LP: ${calculate_liquidation_price(current_price, 100, 'short'):,.2f}")
    print()
    
    # 6. Needle-stick Targets
    print(f"{'='*75}")
    print("🎯 插針目標位 (Needle-stick Targets):\n")
    
    targets = calculate_needle_targets(
        current_price, swing_lows, swing_highs, atr_4h, ls_ratio, fvgs, klines_4h
    )
    
    print(f"⬇️ 下插針候選位 (Downward Needle):\n")
    if targets["downward"]:
        for i, target in enumerate(targets["downward"][:5], 1):
            dist = ((target["price"] - current_price) / current_price * 100)
            conf = "🔴" if target["confidence"] >= 80 else "🟡" if target["confidence"] >= 70 else "🟢"
            print(f"  {i}. ${target['price']:,.2f} ({dist:+.2f}%)")
            print(f"     {conf} {target['type']} [信心度: {target['confidence']}%]")
    else:
        print(f"  ⚠️ 無明顯下插針目標")
    
    print(f"\n⬆️ 上插針候選位 (Upward Needle):\n")
    if targets["upward"]:
        for i, target in enumerate(targets["upward"][:5], 1):
            dist = ((target["price"] - current_price) / current_price * 100)
            conf = "🔴" if target["confidence"] >= 80 else "🟡" if target["confidence"] >= 70 else "🟢"
            print(f"  {i}. ${target['price']:,.2f} ({dist:+.2f}%)")
            print(f"     {conf} {target['type']} [信心度: {target['confidence']}%]")
    else:
        print(f"  ⚠️ 無明顯上插針目標")
    
    print(f"\n{'='*75}\n")
    
    # 7. Final Recommendation
    print("💡 交易建議 (Trading Recommendation):\n")
    
    if squeeze_type == "long_squeeze" and targets["downward"]:
        top_target = targets["downward"][0]
        print(f"  🎯 主要關注: 下插針至 ${top_target['price']:,.2f}")
        print(f"     理由: {top_target['type']}")
        print(f"     建議: 在此價位掛限價買單 (Entry 2 或 Entry 3)")
    elif squeeze_type == "short_squeeze" and targets["upward"]:
        top_target = targets["upward"][0]
        print(f"  🎯 主要關注: 上插針至 ${top_target['price']:,.2f}")
        print(f"     理由: {top_target['type']}")
        print(f"     建議: 謹慎做多，或等待回測後進場")
    else:
        print(f"  ⚠️ 當前市場無明確擠壓信號")
        print(f"     建議: 觀望，或依據現有支撐/阻力位操作")
    
    print(f"\n{'='*75}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 needle_stick_v2.py [SYMBOL]")
        print("Example: python3 needle_stick_v2.py BTC")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    analyze_needle_stick_v2(symbol)

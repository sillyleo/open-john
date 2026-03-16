#!/usr/bin/env python3
"""
MTF Trend Master (多週期共振看盤大師)
專注於 1H, 4H, 1D, 3D 的技術面共振分析，提供中短線操作的最強指引。
"""

import ccxt
import pandas as pd
import pandas_ta as ta
import sys
import warnings
from datetime import datetime

# 忽略 pandas_ta 的一些警告
warnings.filterwarnings('ignore')

def get_mtf_data(symbol='BTC/USDT', timeframes=['1h', '4h', '1d', '3d'], limit=100):
    exchange = ccxt.binance()
    results = {}
    
    for tf in timeframes:
        try:
            bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=limit)
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # 計算指標
            df.ta.rsi(length=14, append=True)
            df.ta.macd(fast=12, slow=26, signal=9, append=True)
            df.ta.ema(length=7, append=True)
            df.ta.ema(length=25, append=True)
            df.ta.ema(length=99, append=True)
            df.ta.bbands(length=20, std=2, append=True)
            df.ta.atr(length=14, append=True)
            
            # 取最新的一根K線 (或上一根已收盤的，這裡取最新狀態以反映當下)
            latest = df.iloc[-1]
            
            # 解析 MACD 欄位名稱 (pandas_ta 自動生成的欄位名稱)
            macd_line = latest.get('MACD_12_26_9', 0)
            macd_hist = latest.get('MACDh_12_26_9', 0)
            
            # 解析 BBands 欄位
            bb_upper = latest.get('BBU_20_2.0', 0)
            bb_lower = latest.get('BBL_20_2.0', 0)
            bb_mid = latest.get('BBM_20_2.0', 0)
            
            bb_width = (bb_upper - bb_lower) / bb_mid * 100 if bb_mid > 0 else 0
            if bb_mid > 0:
                bb_width = (bb_upper - bb_lower) / bb_mid * 100
                
            trend_score = 0
            # 均線多空
            if latest['close'] > latest['EMA_25']: trend_score += 1
            else: trend_score -= 1
            if latest['EMA_7'] > latest['EMA_25']: trend_score += 1
            else: trend_score -= 1
            
            # MACD多空
            if macd_hist > 0: trend_score += 1
            else: trend_score -= 1
            
            # RSI 狀態
            rsi_status = "中性 🟡"
            if latest['RSI_14'] > 70: 
                rsi_status = "超買 🔴"
                trend_score -= 0.5 # 超買容易回調
            elif latest['RSI_14'] < 30: 
                rsi_status = "超賣 🟢"
                trend_score += 0.5 # 超賣容易反彈
                
            # 趨勢判定
            if trend_score >= 2: trend_str = "多頭排列 🟢"
            elif trend_score <= -2: trend_str = "空頭排列 🔴"
            else: trend_str = "震盪糾結 🟡"
            
            results[tf] = {
                'price': latest['close'],
                'rsi': latest['RSI_14'],
                'rsi_status': rsi_status,
                'macd_hist': macd_hist,
                'ema7': latest['EMA_7'],
                'ema25': latest['EMA_25'],
                'ema99': latest.get('EMA_99', 0),
                'trend': trend_str,
                'score': trend_score,
                'bb_width': bb_width
            }
        except Exception as e:
            results[tf] = {'error': str(e)}
            
    return results

def print_mtf_analysis(symbol):
    print(f"============================================================")
    print(f"🦅 MTF Trend Master (多週期共振分析) - {symbol}")
    print(f"🕒 掃描時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"============================================================\n")
    
    data = get_mtf_data(symbol)
    
    # 定義顯示層級
    levels = {
        '1h': '🔬 微觀戰術 (1H - 進出場精確點位)',
        '4h': '⚔️ 中線波段 (4H - 短線趨勢方向)',
        '1d': '🗺️ 宏觀戰略 (1D - 主力資金方向)',
        '3d': '⛰️ 長期結構 (3D - 大週期牛熊界線)'
    }
    
    total_score = 0
    valid_tfs = 0
    
    for tf, title in levels.items():
        if tf not in data or 'error' in data[tf]:
            print(f"{title}: 讀取失敗")
            continue
            
        d = data[tf]
        total_score += d['score']
        valid_tfs += 1
        
        print(f"{title}")
        print(f"  ├─ 趨勢狀態: {d['trend']} (評分: {d['score']})")
        print(f"  ├─ RSI(14) : {d['rsi']:.1f} [{d['rsi_status']}]")
        
        macd_icon = "📈 向上發散" if d['macd_hist'] > 0 else "📉 向下發散"
        print(f"  ├─ MACD動能: {macd_icon} (柱狀圖: {d['macd_hist']:.2f})")
        
        bb_status = "正常"
        if d['bb_width'] < 4: bb_status = "極度收斂 (即將變盤 ⚠️)"
        elif d['bb_width'] > 10: bb_status = "開口發散 (波動劇烈 🌊)"
        print(f"  ├─ 波動帶寬: {d['bb_width']:.2f}% [{bb_status}]")
        
        # 關鍵支撐/壓力 (EMA)
        print(f"  └─ 關鍵均線: EMA7=${d['ema7']:,.0f} | EMA25=${d['ema25']:,.0f} | EMA99=${d['ema99']:,.0f}\n")
        
    print(f"============================================================")
    print(f"🧠 看盤大師 綜合研判 (Master's Verdict)")
    print(f"============================================================")
    
    # 邏輯推演
    if valid_tfs == 0:
        print("數據讀取失敗。")
        return
        
    avg_score = total_score / valid_tfs
    
    if avg_score >= 2:
        verdict = "強勢共振上漲 🚀 (各級別多頭一致，逢回調做多，切勿摸頂做空)"
    elif avg_score >= 0.5:
        verdict = "偏多震盪 ↗️ (大方向偏多，但可能有短線回踩，尋找 1H/4H EMA25 支撐介入)"
    elif avg_score <= -2:
        verdict = "強勢共振下跌 🪂 (各級別空頭一致，逢反彈做空，切勿盲目抄底)"
    elif avg_score <= -0.5:
        verdict = "偏空震盪 ↘️ (大方向偏空，注意防守，等待 1D 級別企穩信號)"
    else:
        verdict = "多空激烈交戰 ⚔️ (各週期分歧嚴重，1H與1D方向可能相反，建議多看少做)"
        
    print(f"🎯 總體盤面定調: {verdict}")
    
    # 衝突檢測 (例如 1H 轉空，但 1D 仍是多)
    if '1h' in data and '1d' in data:
        if data['1h']['score'] < 0 and data['1d']['score'] > 0:
            print(f"⚠️ 異象警告: 日線(1D)偏多，但小時線(1H)正在轉弱，這通常是「多頭回檔洗盤」，適合在下方防禦位接針。")
        elif data['1h']['score'] > 0 and data['1d']['score'] < 0:
            print(f"⚠️ 異象警告: 日線(1D)偏空，但小時線(1H)正在轉強，這通常是「跌深反彈(死貓反彈)」，極具誘多欺騙性。")
            
    print(f"============================================================")

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'BTC/USDT'
    print_mtf_analysis(symbol)

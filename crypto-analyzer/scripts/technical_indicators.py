#!/usr/bin/env python3
"""
技術指標計算工具（使用 CCXT + Pandas-TA）
數據來源: Binance（免 API Key）
計算庫: Pandas-TA（專業金融技術分析庫）
"""

import ccxt
import pandas as pd
import pandas_ta as ta
import sys

def get_indicators(symbol='BTC/USDT', timeframe='4h', limit=100):
    """
    獲取完整技術指標
    
    Args:
        symbol: 交易對（默認 BTC/USDT）
        timeframe: 時間週期（默認 4h）
        limit: K線數量（默認 100）
    
    Returns:
        dict: 包含所有技術指標的字典
    """
    
    # 初始化交易所（免 Key）
    exchange = ccxt.binance()
    
    # 獲取 K線數據
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    current_price = df["close"].iloc[-1]
    
    # 計算各項指標
    indicators = {
        'price': current_price,
        'timestamp': df['timestamp'].iloc[-1],
    }
    
    # RSI
    rsi = df.ta.rsi(close='close', length=14)
    indicators['rsi_14'] = rsi.iloc[-1]
    
    # MACD
    macd = df.ta.macd(close='close', fast=12, slow=26, signal=9)
    indicators['macd_line'] = macd["MACD_12_26_9"].iloc[-1]
    indicators['macd_signal'] = macd["MACDs_12_26_9"].iloc[-1]
    indicators['macd_histogram'] = macd["MACDh_12_26_9"].iloc[-1]
    
    # Bollinger Bands
    bb = df.ta.bbands(close='close', length=20, std=2)
    if bb is not None:
        bb_cols = bb.columns.tolist()
        upper_col = [c for c in bb_cols if 'BBU' in c][0]
        middle_col = [c for c in bb_cols if 'BBM' in c][0]
        lower_col = [c for c in bb_cols if 'BBL' in c][0]
        
        indicators['bb_upper'] = bb[upper_col].iloc[-1]
        indicators['bb_middle'] = bb[middle_col].iloc[-1]
        indicators['bb_lower'] = bb[lower_col].iloc[-1]
    
    # ATR
    atr = df.ta.atr(high='high', low='low', close='close', length=14)
    indicators['atr_14'] = atr.iloc[-1]
    
    # EMA
    indicators['ema_7'] = df.ta.ema(close='close', length=7).iloc[-1]
    indicators['ema_25'] = df.ta.ema(close='close', length=25).iloc[-1]
    indicators['ema_99'] = df.ta.ema(close='close', length=99).iloc[-1]
    
    # SMA
    indicators['sma_7'] = df.ta.sma(close='close', length=7).iloc[-1]
    indicators['sma_25'] = df.ta.sma(close='close', length=25).iloc[-1]
    indicators['sma_99'] = df.ta.sma(close='close', length=99).iloc[-1]
    
    # Stochastic RSI
    stoch_rsi = df.ta.stochrsi(close='close', length=14, rsi_length=14, k=3, d=3)
    if stoch_rsi is not None:
        stoch_cols = stoch_rsi.columns.tolist()
        k_col = [c for c in stoch_cols if 'STOCHRSIk' in c][0]
        d_col = [c for c in stoch_cols if 'STOCHRSId' in c][0]
        indicators['stoch_rsi_k'] = stoch_rsi[k_col].iloc[-1]
        indicators['stoch_rsi_d'] = stoch_rsi[d_col].iloc[-1]
    
    # 成交量
    indicators['volume_current'] = df['volume'].iloc[-1]
    indicators['volume_ma20'] = df['volume'].rolling(20).mean().iloc[-1]
    
    return indicators


if __name__ == '__main__':
    # 命令行使用
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'BTC/USDT'
    timeframe = sys.argv[2] if len(sys.argv) > 2 else '4h'
    
    indicators = get_indicators(symbol, timeframe)
    
    print(f'=== {symbol} {timeframe} 技術指標 ===')
    print(f'價格: ${indicators["price"]:,.2f}')
    print()
    print(f'RSI(14): {indicators["rsi_14"]:.2f}')
    print()
    print(f'MACD (12, 26, 9):')
    print(f'  MACD Line: {indicators["macd_line"]:.2f}')
    print(f'  Signal: {indicators["macd_signal"]:.2f}')
    print(f'  Histogram: {indicators["macd_histogram"]:.2f}')
    print()
    print(f'Bollinger Bands:')
    print(f'  Upper: ${indicators["bb_upper"]:,.2f}')
    print(f'  Middle: ${indicators["bb_middle"]:,.2f}')
    print(f'  Lower: ${indicators["bb_lower"]:,.2f}')
    print()
    print(f'ATR(14): ${indicators["atr_14"]:,.2f}')
    print()
    print(f'EMA: 7=${indicators["ema_7"]:,.2f} | 25=${indicators["ema_25"]:,.2f} | 99=${indicators["ema_99"]:,.2f}')
    print(f'SMA: 7=${indicators["sma_7"]:,.2f} | 25=${indicators["sma_25"]:,.2f} | 99=${indicators["sma_99"]:,.2f}')

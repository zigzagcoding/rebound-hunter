import pandas as pd

def calculate_drawdown_from_52w_high(hist: pd.DataFrame) -> float:
    """52週高値からのドローダウン(%)"""
    current = hist["Close"].iloc[-1]
    high_52w = hist["High"].max()
    return (current - high_52w) / high_52w * 100

def calculate_ma(hist: pd.DataFrame, window: int) -> float:
    """単純移動平均(最新値)"""
    if len(hist) < window:
        return None
    return hist["Close"].rolling(window).mean().iloc[-1]

def calculate_rsi(hist: pd.DataFrame, window: int = 14) -> float:
    """RSI(最新値)"""
    if len(hist) < window + 1:
        return None
    close = hist["Close"]
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def calculate_all_indicators(hist: pd.DataFrame) -> dict:
    """全指標をまとめて計算"""
    return {
        "current_price": hist["Close"].iloc[-1],
        "high_52w": hist["High"].max(),
        "low_52w": hist["Low"].min(),
        "drawdown_pct": calculate_drawdown_from_52w_high(hist),
        "ma_25": calculate_ma(hist, 25),
        "ma_200": calculate_ma(hist, 200),
        "rsi_14": calculate_rsi(hist, 14),
        "volume_avg_25": hist["Volume"].rolling(25).mean().iloc[-1],
    }
import yfinance as yf
import pandas as pd
import time
import random
from pathlib import Path
from datetime import datetime
from indicators import calculate_all_indicators

def fetch_one(code: int) -> dict | None:
    """1銘柄のデータを取得して指標を計算"""
    try:
        ticker = yf.Ticker(f"{code}.T")
        hist = ticker.history(period="1y")
        
        if hist.empty:
            print(f"  [警告] {code}: データが空")
            return None
        
        indicators = calculate_all_indicators(hist)
        indicators["code"] = code
        return indicators
        
    except Exception as e:
        print(f"  [エラー] {code}: {e}")
        return None

def monitor_all():
    # ウォッチリスト読み込み
    watchlist = pd.read_csv("data/watchlist.csv")
    print(f"監視銘柄数: {len(watchlist)}")
    
    results = []
    for i, row in watchlist.iterrows():
        code = row["code"]
        print(f"[{i+1}/{len(watchlist)}] {code} {row['name']}...")
        
        data = fetch_one(code)
        if data:
            data["name"] = row["name"]
            results.append(data)
        
        # レート制限対策(最後の銘柄ではsleepしない)
        if i < len(watchlist) - 1:
            sleep_time = random.uniform(2.0, 4.0)
            time.sleep(sleep_time)
    
    # 保存
    today = datetime.now().strftime("%Y-%m-%d")
    Path("data/snapshots").mkdir(parents=True, exist_ok=True)
    output_path = f"data/snapshots/{today}.csv"
    
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    print(f"\n保存先: {output_path}")
    print(f"取得成功: {len(df)}/{len(watchlist)}銘柄")
    
    # 簡易サマリー
    print("\n=== 結果サマリー ===")
    print(df[["code", "name", "current_price", "drawdown_pct", "rsi_14"]].to_string(index=False))

if __name__ == "__main__":
    monitor_all()
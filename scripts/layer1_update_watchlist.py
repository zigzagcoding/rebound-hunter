import os
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("EDINET_DB_API_KEY")
BASE_URL = "https://edinetdb.jp/v1"

# スクリーニング条件
# 単位:時価総額は百万円(100,000 = 1000億円)
# 単位:率はパーセント(10 = 10%)
SCREENING_CONDITIONS = {
    "roe_gte": 15,                # ROE 15%以上
    "operating_margin_gte": 10,   # 営業利益率 10%以上
    "equity_ratio_gte": 50,       # 自己資本比率 50%以上
    "market_cap_gte": 200_000,    # 時価総額2000億円以上(=200,000百万円)
    "limit": 500,
}

def fetch_screening_results():
    """スクリーニングを実行して結果を取得"""
    headers = {"X-API-Key": API_KEY}
    
    response = requests.get(
        f"{BASE_URL}/screener",
        params=SCREENING_CONDITIONS,
        headers=headers,
    )
    
    if response.status_code != 200:
        print(f"[エラー] APIリクエスト失敗: {response.status_code}")
        print(f"  詳細: {response.text}")
        return None
    
    payload = response.json()
    return payload.get("data", {}).get("companies", [])

def update_watchlist():
    print("=== EDINET DB スクリーニング実行 ===")
    print(f"条件: {SCREENING_CONDITIONS}")
    
    results = fetch_screening_results()
    
    if results is None:
        print("[エラー] スクリーニング失敗。watchlist.csv は更新しない")
        return
    
    if not results:
        print("[警告] 該当銘柄ゼロ。条件を見直すこと")
        return
    
    print(f"取得銘柄数: {len(results)}")
    
    # 必要フィールドを抽出
    # ※ハイフン区切りフィールドは辞書アクセスで取得
    watchlist_records = []
    for record in results:
        sec_code = record.get("secCode")
        if not sec_code:
            continue
        
        watchlist_records.append({
            "code": sec_code,
            "name": record.get("filerName", ""),
            "edinet_code": record.get("edinetCode", ""),
            "industry": record.get("industry", ""),
            "roe": record.get("roe"),
            "operating_margin": record.get("operating-margin"),  # ハイフン形式
            "equity_ratio": record.get("equity-ratio"),          # ハイフン形式
            "market_cap": record.get("market-cap"),              # ハイフン形式(単位:百万円)
        })
    
    if not watchlist_records:
        print("[警告] secCode を持つ銘柄がゼロ")
        return
    
    df = pd.DataFrame(watchlist_records)
    df = df.drop_duplicates(subset=["code"])
    
    # 保存先
    Path("data").mkdir(exist_ok=True)
    output_path = "data/watchlist.csv"
    
    # 既存ファイルがあればバックアップ
    if Path(output_path).exists():
        today = datetime.now().strftime("%Y-%m-%d")
        backup_path = f"data/watchlist_backup_{today}.csv"
        # 既にバックアップがあれば上書き(同日複数回実行対応)
        if Path(backup_path).exists():
            Path(backup_path).unlink()
        Path(output_path).rename(backup_path)
        print(f"既存ファイルをバックアップ: {backup_path}")
    
    df.to_csv(output_path, index=False)
    print(f"\n保存完了: {output_path}")
    print(f"銘柄数: {len(df)}")
    
    print("\n=== 抽出銘柄サンプル(先頭10件) ===")
    print(df[["code", "name", "roe", "operating_margin", "market_cap"]].head(10).to_string(index=False))

if __name__ == "__main__":
    update_watchlist()
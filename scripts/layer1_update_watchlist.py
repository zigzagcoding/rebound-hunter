import os
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("EDINET_DB_API_KEY")
BASE_URL = "https://edinetdb.jp/v1"

SCREENING_CONDITIONS = {
    "roe_gte": 15,
    "operating_margin_gte": 10,
    "equity_ratio_gte": 50,
    "market_cap_gte": 200_000,
    "limit": 500,
}

def fetch_screening_results():
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

def convert_sec_code(sec_code: str) -> tuple[str, bool]:
    """
    新証券コード(5桁英数字)を旧コード(4桁数字)に変換
    
    Returns:
        (変換後コード, yfinance利用可能フラグ)
    """
    if not sec_code:
        return ("", False)
    
    sec_code = str(sec_code).strip()
    
    # 既に4桁数字ならそのまま
    if len(sec_code) == 4 and sec_code.isdigit():
        return (sec_code, True)
    
    # 5桁で末尾が0、前4桁が全て数字 → 末尾0を除く
    if len(sec_code) == 5 and sec_code.endswith("0") and sec_code[:4].isdigit():
        return (sec_code[:4], True)
    
    # 英字を含むコード → yfinanceでは扱えない可能性高い
    # 末尾英字を除いた4桁を試す(例:418A0 → 418A → 不可)
    # 一旦、変換不可として返す
    return (sec_code, False)

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
    watchlist_records = []
    skipped_records = []  # yfinanceで扱えない銘柄を記録
    
    for record in results:
        raw_sec_code = record.get("secCode")
        if not raw_sec_code:
            continue
        
        # 証券コード変換
        converted_code, is_usable = convert_sec_code(raw_sec_code)
        
        if not is_usable:
            skipped_records.append({
                "raw_code": raw_sec_code,
                "name": record.get("filerName", ""),
            })
            continue
        
        watchlist_records.append({
            "code": converted_code,
            "name": record.get("filerName", ""),
            "edinet_code": record.get("edinetCode", ""),
            "industry": record.get("industry", ""),
            "roe": record.get("roe"),
            "operating_margin": record.get("operating-margin"),
            "equity_ratio": record.get("equity-ratio"),
            "market_cap": record.get("market-cap"),
        })
    
    if not watchlist_records:
        print("[警告] yfinance で扱える銘柄がゼロ")
        return
    
    # スキップした銘柄を報告
    if skipped_records:
        print(f"\n[情報] yfinance非対応のためスキップ: {len(skipped_records)}件")
        for s in skipped_records[:5]:  # 先頭5件のみ表示
            print(f"  - {s['raw_code']}: {s['name']}")
        if len(skipped_records) > 5:
            print(f"  ... 他 {len(skipped_records) - 5} 件")
    
    df = pd.DataFrame(watchlist_records)
    df = df.drop_duplicates(subset=["code"])
    
    # 保存先
    Path("data").mkdir(exist_ok=True)
    output_path = "data/watchlist.csv"
    
    # 既存ファイルがあればバックアップ
    if Path(output_path).exists():
        today = datetime.now().strftime("%Y-%m-%d")
        backup_path = f"data/watchlist_backup_{today}.csv"
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
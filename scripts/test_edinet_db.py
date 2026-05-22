# スクリーニング条件:単位を百万円に修正
SCREENING_CONDITIONS = {
    "roe_gte": 10,
    "operating_margin_gte": 8,
    "equity_ratio_gte": 40,
    "market_cap_gte": 100_000,        # 1000億円 = 100,000百万円
    "limit": 500,
}

# レスポンスのフィールド名をキャメルケースに修正
def update_watchlist():
    # ...
    results = data.get("data", {}).get("companies", [])  # ← 修正:results ではなく data.companies
    
    for record in results:
        # sec_code が無い銘柄は除外
        if not record.get("secCode"):  # ← キャメルケース
            continue
        
        watchlist_records.append({
            "code": record["secCode"],
            "name": record.get("filerName", ""),        # ← キャメルケース
            "edinet_code": record.get("edinetCode", ""), # ← キャメルケース
            "industry": record.get("industry", ""),
            "roe": record.get("roe"),
            "operating_margin": record.get("operatingMargin"),  # 推定
            "equity_ratio": record.get("equityRatio"),          # 推定
            "market_cap": record.get("marketCap"),              # 推定
        })
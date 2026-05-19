import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

def detect_signals(row: pd.Series) -> list[str]:
    """1銘柄に対して、該当する検知パターンのリストを返す"""
    signals = []
    
    # パターン1: 大幅下落
    if row["drawdown_pct"] <= -25:
        signals.append("大幅下落")
    
    # パターン2: 売られすぎ
    if pd.notna(row["rsi_14"]) and row["rsi_14"] <= 30:
        signals.append("売られすぎ")
    
    # パターン3: 長期線割れ
    if pd.notna(row["ma_200"]):
        gap_from_ma200 = (row["current_price"] - row["ma_200"]) / row["ma_200"] * 100
        if row["current_price"] < row["ma_200"] and gap_from_ma200 <= -10:
            signals.append("長期線割れ")
    
    # パターン4: セリクラ候補
    if pd.notna(row["ma_25"]):
        gap_from_ma25 = (row["current_price"] - row["ma_25"]) / row["ma_25"] * 100
        # Note: 出来高比較は今回スナップショットに無いのでスキップ
        # 後で hist データから volume_today / volume_avg_25 を計算する版に拡張可能
        if gap_from_ma25 <= -15:
            signals.append("25日線大幅下方乖離")
    
    return signals

def detect_drops(snapshot_path: str = None):
    """スナップショットを読み込み、トリガー銘柄を抽出"""
    
    # スナップショット決定(指定がなければ最新)
    if snapshot_path is None:
        snapshots_dir = Path("data/snapshots")
        if not snapshots_dir.exists():
            print("[エラー] data/snapshots/ が存在しません")
            sys.exit(1)
        
        snapshot_files = sorted(snapshots_dir.glob("*.csv"))
        if not snapshot_files:
            print("[エラー] スナップショットファイルが見つかりません")
            sys.exit(1)
        
        snapshot_path = snapshot_files[-1]
        print(f"使用スナップショット: {snapshot_path.name}")
    
    df = pd.read_csv(snapshot_path)
    print(f"対象銘柄数: {len(df)}")
    
    # 各銘柄について検知
    triggers = []
    for _, row in df.iterrows():
        signals = detect_signals(row)
        if signals:
            trigger_record = {
                "code": row["code"],
                "name": row["name"],
                "current_price": row["current_price"],
                "drawdown_pct": row["drawdown_pct"],
                "rsi_14": row["rsi_14"],
                "ma_25": row["ma_25"],
                "ma_200": row["ma_200"],
                "signals": ",".join(signals),
                "signal_count": len(signals),
            }
            triggers.append(trigger_record)
    
    # 出力
    today = datetime.now().strftime("%Y-%m-%d")
    Path("data/triggers").mkdir(parents=True, exist_ok=True)
    output_path = f"data/triggers/{today}.csv"
    
    if triggers:
        triggers_df = pd.DataFrame(triggers).sort_values("signal_count", ascending=False)
        triggers_df.to_csv(output_path, index=False)
        
        print(f"\n=== 検知結果: {len(triggers_df)}銘柄 ===")
        print(f"保存先: {output_path}\n")
        
        for _, row in triggers_df.iterrows():
            print(f"[{row['signal_count']}個] {row['code']} {row['name']}")
            print(f"  現在値: ¥{row['current_price']:.0f}")
            print(f"  52週高値から: {row['drawdown_pct']:+.1f}%")
            print(f"  RSI(14): {row['rsi_14']:.1f}")
            print(f"  検知シグナル: {row['signals']}")
            print()
    else:
        print("\n検知された銘柄なし")
        # 空CSVも作成(後段の処理が「ファイル無し」と「該当0件」を区別するため)
        pd.DataFrame(columns=["code", "name", "current_price", "drawdown_pct", 
                              "rsi_14", "ma_25", "ma_200", "signals", "signal_count"]).to_csv(output_path, index=False)
        print(f"空ファイル作成: {output_path}")

if __name__ == "__main__":
    detect_drops()
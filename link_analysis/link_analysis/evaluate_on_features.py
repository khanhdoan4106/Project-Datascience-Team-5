"""Bước 3 – Đặc trưng đồ thị có cải thiện dự đoán không?

So sánh bộ đặc trưng của nhóm (features.csv: 85 cột số) CÓ và KHÔNG CÓ 5 đặc trưng đồ thị.
Chia theo thời gian, không xáo trộn: (1) rolling-origin – huấn luyện trên mọi mùa trước, kiểm thử từng mùa từ 2010/11;
(2) split của nhóm – huấn luyện đến 2023/24, kiểm thử từ 2024/25. Chỉ số: accuracy, log loss, Brier,
khoảng tin cậy 95% của chênh lệch log loss bằng bootstrap theo cặp (2.000 lần).

Chạy:  python evaluate_on_features.py --features features.csv --graph results/graph_features_matches.csv
"""
import argparse

import numpy as np
import pandas as pd

import evaluate_graph_features as E
from evaluate_graph_features import GRAPH, report

IDS = ["match_id", "season", "date", "kickoff_time", "gameweek", "home_club_id", "home_team", "away_club_id",
       "away_team", "status", "provisional", "postponed", "home_goals", "away_goals", "result"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--graph", required=True)
    a = ap.parse_args()
    f = pd.read_csv(a.features)
    g = pd.read_csv(a.graph)
    df = f.merge(g[["match_id"] + [c for c in g.columns if c.startswith("gr_")]], on="match_id", how="left", validate="1:1")
    df = df[(df.status == "played") & (df.season != "2000/01")].sort_values("date", kind="stable").reset_index(drop=True)
    num = [c for c in f.columns if c not in IDS and pd.api.types.is_numeric_dtype(f[c])]
    odds = [c for c in num if c.startswith("odds_")]
    no_odds = [c for c in num if c not in odds]
    print(f"{len(df)} tran da da | {len(num)} dac trung so (trong do {len(odds)} cot keo) | bo cot chuoi: "
          f"{[c for c in f.columns if c not in IDS and c not in num]}")
    sets = {
        "elo_diff": ["elo_diff"],
        "baseline khong keo": no_odds,
        "baseline khong keo + graph": no_odds + GRAPH,
        "baseline day du (co keo)": num,
        "baseline day du + graph": num + GRAPH,
    }
    rng = np.random.default_rng(0)
    seasons = sorted(df.season.unique())
    roll = [(df.season < s, df.season == s) for s in seasons if s >= "2010/11"]
    doc = [(df.season < "2024/25", df.season >= "2024/25")]
    for kind, label in [("logreg", "Logistic Regression"), ("hgb", "Gradient Boosting")]:
        for tag, splits in [("rolling 2010/11 -> 2026/27", roll), ("train <2024/25, test >=2024/25", doc)]:
            probs, y, s = E.evaluate(df, sets, kind, splits)
            report(f"{label} | {tag}", probs, y, s, "baseline day du (co keo)", rng)


if __name__ == "__main__":
    main()

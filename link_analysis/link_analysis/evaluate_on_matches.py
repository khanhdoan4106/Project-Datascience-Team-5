"""Bước 3c – Đánh giá gọn chỉ từ matches.csv: Elo tự tính, kèo nhà cái và đặc trưng đồ thị.

Dùng để trả lời hai câu hỏi phụ: (1) chỉ dùng đặc trưng đồ thị thì được bao nhiêu so với Elo;
(2) kèo nhà cái mạnh đến đâu. Elo tự tính: K = 20, lợi thế sân nhà +65, giữ 80% khi sang mùa, đội mới 1450.

Chạy:  python evaluate_on_matches.py --matches matches.csv --graph results/graph_features_matches.csv
"""
import argparse

import numpy as np
import pandas as pd

from evaluate_graph_features import GRAPH, report

import evaluate_graph_features as E


def add_elo(df, K=20, HOME=65, CARRY=0.8, NEW=1450):
    ratings, season, first = {}, None, df.season.iloc[0]
    eh = []
    for r in df.itertuples():
        if r.season != season:
            if season is not None:
                ratings = {t: CARRY * v + (1 - CARRY) * 1500 for t, v in ratings.items()}
            season = r.season
        d = 1500 if r.season == first else NEW
        rh, ra = ratings.get(r.home_club_id, d), ratings.get(r.away_club_id, d)
        eh.append(rh - ra)
        exp = 1 / (1 + 10 ** ((ra - rh - HOME) / 400))
        gd = abs(r.home_goals - r.away_goals)
        sc = 1.0 if r.result == "H" else 0.5 if r.result == "D" else 0.0
        mult = 1 if gd <= 1 else 1.5 if gd == 2 else (11 + gd) / 8
        delta = K * mult * (sc - exp)
        ratings[r.home_club_id], ratings[r.away_club_id] = rh + delta, ra - delta
    df["elo_diff"] = eh
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matches", required=True)
    ap.add_argument("--graph", required=True)
    a = ap.parse_args()
    m = pd.read_csv(a.matches)
    m = m[m.status == "played"].sort_values("date", kind="stable").reset_index(drop=True)
    m = add_elo(m)
    inv = 1 / m[["avg_home_odds", "avg_draw_odds", "avg_away_odds"]].values
    p = inv / inv.sum(1, keepdims=True)
    m["odds_logit_home_away"] = np.log(p[:, 0] / p[:, 2])
    m["odds_p_draw"] = p[:, 1]
    g = pd.read_csv(a.graph)
    df = m.merge(g[["match_id"] + [c for c in g.columns if c.startswith("gr_")]], on="match_id", how="left", validate="1:1")
    df = df[df.season != "2000/01"].reset_index(drop=True)
    ODDS = ["odds_logit_home_away", "odds_p_draw"]
    sets = {
        "elo_diff": ["elo_diff"],
        "elo_diff + graph": ["elo_diff"] + GRAPH,
        "graph only": GRAPH,
        "keo nha cai": ODDS,
        "keo + elo": ODDS + ["elo_diff"],
        "keo + elo + graph": ODDS + ["elo_diff"] + GRAPH,
    }
    print("n tran:", len(df), "| co keo:", int(df.odds_p_draw.notna().sum()))
    rng = np.random.default_rng(0)
    seasons = sorted(df.season.unique())
    roll = [(df.season < s, df.season == s) for s in seasons if s >= "2010/11"]
    doc = [(df.season < "2024/25", df.season >= "2024/25")]
    for kind, label in [("logreg", "Logistic Regression"), ("hgb", "Gradient Boosting")]:
        for tag, splits in [("rolling 2010/11 -> 2026/27", roll), ("train <2024/25, test >=2024/25", doc)]:
            probs, y, s = E.evaluate(df, sets, kind, splits)
            report(f"{label} | {tag}", probs, y, s, "elo_diff", rng)


if __name__ == "__main__":
    main()

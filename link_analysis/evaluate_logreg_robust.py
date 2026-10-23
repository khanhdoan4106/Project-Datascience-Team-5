"""Kiểm tra độ vững của kết luận với Logistic Regression khi chuẩn hóa đặc trưng bằng quantile (chống đuôi nặng).

Lý do: với StandardScaler, Logistic Regression trên 85 đặc trưng cho log loss ~1,16 (tệ hơn chỉ dùng Elo ~0,98) vì nhiều
biến có đuôi rất nặng (home_rest_days lệch tới 70 độ lệch chuẩn, các biến *_pg ở đầu mùa). Chuyển sang quantile-normal
đưa log loss về ~1,02. Kết luận về đặc trưng đồ thị được kiểm lại trên mô hình đã sửa.

Chạy:  python evaluate_logreg_robust.py --features features.csv --graph graph_features_matches.csv
"""
import argparse
import warnings

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import QuantileTransformer, StandardScaler

from evaluate_graph_features import CLASSES, GRAPH
from evaluate_on_features import IDS

warnings.filterwarnings("ignore")


def model(kind):
    scaler = QuantileTransformer(output_distribution="normal", n_quantiles=200) if kind == "quantile" else StandardScaler()
    return make_pipeline(SimpleImputer(strategy="median"), scaler, LogisticRegression(C=0.3, max_iter=2000))


def per_match_loss(df, cols, kind, first="2010/11", last="2025/26"):
    loss = []
    for s in sorted(df.season.unique()):
        if not first <= s <= last:
            continue
        tr, te = df[df.season < s], df[df.season == s]
        c = [k for k in cols if tr[k].notna().any()]
        m = model(kind).fit(tr[c], tr.result)
        p = m.predict_proba(te[c])
        loss.append(-np.log(np.clip(p[np.arange(len(te)), pd.Categorical(te.result, CLASSES).codes], 1e-12, 1)))
    return np.concatenate(loss)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--graph", required=True)
    a = ap.parse_args()
    f, g = pd.read_csv(a.features), pd.read_csv(a.graph)
    df = f.merge(g[["match_id"] + [c for c in g if c.startswith("gr_")]], on="match_id", validate="1:1")
    df = df[(df.status == "played") & (df.season != "2000/01")].sort_values("date", kind="stable")
    num = [c for c in f.columns if c not in IDS and pd.api.types.is_numeric_dtype(f[c])]
    rows = {
        "elo_diff (Standard)": per_match_loss(df, ["elo_diff"], "standard"),
        "85 đặc trưng (Standard)": per_match_loss(df, num, "standard"),
        "85 đặc trưng (Quantile)": per_match_loss(df, num, "quantile"),
        "85 + đồ thị (Quantile)": per_match_loss(df, num + GRAPH, "quantile"),
    }
    print(f"Logistic Regression, rolling 2010/11 -> 2025/26, n = {len(next(iter(rows.values())))} trận")
    for k, v in rows.items():
        print(f"  {k:28s} log loss {v.mean():.4f}")
    d = rows["85 + đồ thị (Quantile)"] - rows["85 đặc trưng (Quantile)"]
    rng = np.random.default_rng(0)
    lo, hi = np.percentile([d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)], [2.5, 97.5])
    print(f"  Chênh lệch (đồ thị - không): {d.mean():+.4f}, KTC 95% [{lo:+.4f}, {hi:+.4f}]")


if __name__ == "__main__":
    main()

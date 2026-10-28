"""Chẩn đoán vì sao Logistic Regression trên 85 đặc trưng kém hơn chỉ dùng Elo (tài liệu cá nhân, bước 8b).

So các cách xử lý trên các mùa kiểm thử 2018/19 – 2025/26 (huấn luyện trên mọi mùa trước):
StandardScaler; bỏ rest_days; bỏ cột trùng đại số (diff_*, elo_home_win_prob); QuantileTransformer;
cắt phân vị 1–99% rồi StandardScaler; và chỉ elo_diff để đối chiếu.

Chạy:  python chan_doan_logreg.py --features features.csv
"""
import argparse
import warnings

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import QuantileTransformer, StandardScaler

warnings.filterwarnings("ignore")
IDS = ["match_id", "season", "date", "kickoff_time", "gameweek", "home_club_id", "home_team", "away_club_id",
       "away_team", "status", "provisional", "postponed", "home_goals", "away_goals", "result"]


class ClipPercentile(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        X = np.asarray(X, float)
        self.lo_, self.hi_ = np.nanpercentile(X, 1, 0), np.nanpercentile(X, 99, 0)
        return self

    def transform(self, X):
        return np.clip(np.asarray(X, float), self.lo_, self.hi_)


def pipe(*steps):
    return lambda: make_pipeline(SimpleImputer(strategy="median"), *[s() for s in steps],
                                 LogisticRegression(C=0.3, max_iter=3000))


def score(df, cols, make):
    total, n = 0.0, 0
    for s in sorted(df.season.unique()):
        if not "2018/19" <= s <= "2025/26":
            continue
        tr, te = df[df.season < s], df[df.season == s]
        c = [k for k in cols if tr[k].notna().any()]
        m = make().fit(tr[c], tr.result)
        total += log_loss(te.result, m.predict_proba(te[c]), labels=m.classes_) * len(te)
        n += len(te)
    return total / n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    f = pd.read_csv(ap.parse_args().features)
    df = f[(f.status == "played") & (f.season != "2000/01")].sort_values("date", kind="stable")
    num = [c for c in f.columns if c not in IDS and pd.api.types.is_numeric_dtype(f[c])]
    no_rest = [c for c in num if "rest_days" not in c]
    no_dup = [c for c in num if not c.startswith("diff_") and c != "elo_home_win_prob"]
    no_both = [c for c in no_dup if "rest_days" not in c]
    quant = lambda: QuantileTransformer(output_distribution="normal", n_quantiles=200)
    rows = [
        ("StandardScaler, 85 đặc trưng", num, pipe(StandardScaler)),
        ("bỏ rest_days", no_rest, pipe(StandardScaler)),
        ("bỏ diff_* và elo_home_win_prob", no_dup, pipe(StandardScaler)),
        ("bỏ cả hai nhóm", no_both, pipe(StandardScaler)),
        ("QuantileTransformer", num, pipe(quant)),
        ("cắt phân vị 1–99% + StandardScaler", num, pipe(ClipPercentile, StandardScaler)),
        ("chỉ elo_diff", ["elo_diff"], pipe(StandardScaler)),
    ]
    print("Logistic Regression, kiểm thử 2018/19 – 2025/26")
    for name, cols, make in rows:
        print(f"  {name:38s} log loss {score(df, cols, make):.4f}", flush=True)


if __name__ == "__main__":
    main()

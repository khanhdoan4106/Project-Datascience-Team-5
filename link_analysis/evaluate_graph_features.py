"""Thư viện đánh giá dùng chung (mô hình, chia theo thời gian, log loss, Brier, bootstrap).

Được import bởi evaluate_on_features.py. Hàm main() ở cuối file là phiên bản thử nghiệm ban đầu trên bộ dữ liệu
tự làm (epl_dataset.csv), giữ lại để tham khảo; kết quả chính thức dùng evaluate_on_features.py.
"""
import argparse
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
KEY = ["season", "date", "home_team", "away_team"]
CLASSES = ["A", "D", "H"]
ID_TARGET = KEY + ["status", "home_goals", "away_goals", "result"]
GRAPH = ["gr_pagerank_log_ratio", "gr_common_opp_diff", "gr_trans2_diff", "gr_h2h_share", "gr_h2h_gd"]


def make_model(kind):
    if kind == "logreg":
        return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                             LogisticRegression(C=0.3, max_iter=2000))
    return HistGradientBoostingClassifier(max_depth=3, learning_rate=0.04, max_iter=150,
                                          min_samples_leaf=60, l2_regularization=5.0, random_state=0)


def brier(y, P):
    Y = np.eye(3)[pd.Categorical(y, CLASSES).codes]
    return float(((P - Y) ** 2).sum(1).mean())


def fit_predict(kind, cols, train, test):
    cols = [c for c in cols if train[c].notna().any()]  # xG chi co tu 2014/15 -> bo cot rong o cac mua dau
    m = make_model(kind).fit(train[cols], train.result)
    assert list(m.classes_) == CLASSES
    return m.predict_proba(test[cols])


def per_match_logloss(y, P):
    return -np.log(np.clip(P[np.arange(len(y)), pd.Categorical(y, CLASSES).codes], 1e-12, 1))


def evaluate(df, sets, kind, splits):
    """splits: list of (train_mask, test_mask). Tra ve proba gop cua tung tap dac trung va nhan that."""
    probs = {name: [] for name in sets}
    ys, seasons = [], []
    for tr, te in splits:
        train, test = df[tr], df[te]
        for name, cols in sets.items():
            probs[name].append(fit_predict(kind, cols, train, test))
        ys.append(test.result.values)
        seasons.append(test.season.values)
    return {k: np.vstack(v) for k, v in probs.items()}, np.concatenate(ys), np.concatenate(seasons)


def report(title, probs, y, seasons, ref, rng):
    print(f"\n=== {title}  (n = {len(y)} tran) ===")
    rows = []
    ll_ref = per_match_logloss(y, probs[ref])
    for name, P in probs.items():
        ll = per_match_logloss(y, P)
        d = ll - ll_ref
        boot = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
        lo, hi = np.percentile(boot, [2.5, 97.5])
        wins = sum(per_match_logloss(y[seasons == s], P[seasons == s]).mean() <
                   ll_ref[seasons == s].mean() for s in np.unique(seasons))
        rows.append({"tap dac trung": name, "accuracy": accuracy_score(y, np.array(CLASSES)[P.argmax(1)]),
                     "log loss": ll.mean(), "Brier": brier(y, P),
                     "d logloss vs ref": d.mean(), "95% CI": f"[{lo:+.4f}, {hi:+.4f}]",
                     "mua tot hon ref": f"{wins}/{len(np.unique(seasons))}" if name != ref else "-"})
    print(pd.DataFrame(rows).round(4).to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--graph", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.dataset).merge(pd.read_csv(args.graph), on=KEY, how="left", validate="1:1")
    df = df[(df.status == "played") & (df.season != "2000/01")].reset_index(drop=True)
    base_all = [c for c in df.columns if c not in ID_TARGET and not c.startswith("gr_")]
    sets = {
        "elo_diff": ["elo_diff"],
        "elo_diff + graph": ["elo_diff"] + GRAPH,
        "graph only": GRAPH,
        "baseline day du (23 dac trung cua nhom)": base_all,
        "baseline day du + graph": base_all + GRAPH,
    }
    print("Phan phoi nhan:", df.result.value_counts(normalize=True).round(3).to_dict())
    print("Dac trung baseline:", len(base_all), "| dac trung do thi:", GRAPH)
    rng = np.random.default_rng(0)

    seasons = sorted(df.season.unique())
    roll = [(df.season < s, df.season == s) for s in seasons if s >= "2010/11"]
    doc = [(df.season < "2024/25", df.season >= "2024/25")]
    for kind, label in [("logreg", "Logistic Regression"), ("hgb", "Gradient Boosting (HistGB)")]:
        for tag, splits in [("rolling 2010/11 -> 2026/27", roll), ("split cua nhom: train <2024/25, test >=2024/25", doc)]:
            probs, y, s = evaluate(df, sets, kind, splits)
            probs["__prior__"] = np.tile(df.result.value_counts(normalize=True).reindex(CLASSES).values, (len(y), 1))
            ref = "baseline day du (23 dac trung cua nhom)"
            report(f"{label} | {tag}", probs, y, s, ref, rng)


if __name__ == "__main__":
    main()

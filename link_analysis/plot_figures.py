"""Vẽ lại 3 hình của báo cáo Link Analysis từ các CSV trong results/.
Chạy:  python plot_figures.py --dir results      (cần pandas, numpy, matplotlib)"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BIG6 = ["Arsenal", "Chelsea", "Liverpool", "Manchester City", "Manchester United", "Tottenham"]
CAT = ["#2a6fdb", "#e0782b", "#2e9e6b"]
INK, MUTED, GRID = "#1f2430", "#8a93a3", "#e3e6ec"


def fig1(nodes, edges, out):
    """Mạng toàn thời gian: bố cục vòng tròn theo cộng đồng, chỉ vẽ 8% cặp gặp nhau nhiều nhất."""
    nodes = nodes.sort_values(["community", "mean_season_pagerank"], ascending=[True, False]).reset_index(drop=True)
    ang = np.pi / 2 - 2 * np.pi * np.arange(len(nodes)) / len(nodes)
    pos = {t: (np.cos(a), np.sin(a)) for t, a in zip(nodes.team, ang)}
    thr = np.percentile(edges.meetings, 92)
    fig, ax = plt.subplots(figsize=(10, 10))
    for _, r in edges[edges.meetings >= thr].iterrows():
        (x1, y1), (x2, y2) = pos[r.team_a], pos[r.team_b]
        ax.plot([x1, x2], [y1, y2], color=MUTED, alpha=0.5, lw=0.5 + 0.05 * (r.meetings - thr))
    pr = nodes.mean_season_pagerank.fillna(nodes.mean_season_pagerank.min())
    size = 60 + 900 * (pr - pr.min()) / (pr.max() - pr.min())
    for t, a, c, s in zip(nodes.team, ang, nodes.community, size):
        ax.scatter(*pos[t], s=s, color=CAT[c % 3], edgecolor="white", zorder=3)
        left = np.cos(a) < 0
        ax.text(1.09 * pos[t][0], 1.09 * pos[t][1], t, fontsize=8, va="center", ha="right" if left else "left",
                rotation=np.degrees(a) + (180 if left else 0), rotation_mode="anchor")
    ax.set(xlim=(-1.5, 1.5), ylim=(-1.5, 1.5), aspect="equal"); ax.axis("off")
    ax.set_title("Mạng lưới đối đầu Premier League 2000/01 – 2026/27", loc="left")
    fig.savefig(out / "fig1_network_alltime.png", dpi=170, bbox_inches="tight"); plt.close(fig)


def fig2(by_season, val, out):
    """PageRank theo mùa của 6 CLB lớn (xám: các CLB còn lại). Bỏ mùa chưa đủ trận."""
    ok = set(val[val.n_matches >= 335].season)
    d = by_season[by_season.season.isin(ok)]
    seasons = sorted(d.season.unique()); xs = {s: i for i, s in enumerate(seasons)}
    fig, axes = plt.subplots(2, 3, figsize=(12, 6), sharex=True, sharey=True)
    for ax, t in zip(axes.ravel(), BIG6):
        for o, g in d.groupby("team"):
            ax.plot(g.season.map(xs), g.pagerank, color=GRID, lw=1)
        g = d[d.team == t]
        ax.plot(g.season.map(xs), g.pagerank, color=CAT[0], lw=2)
        ax.axhline(1, color=MUTED, lw=0.8, ls="--"); ax.set_title(t, loc="left")
    ticks = [i for i, s in enumerate(seasons) if s[:4] in ("2000", "2005", "2010", "2015", "2020", "2025")]
    axes[0, 0].set_xticks(ticks); axes[0, 0].set_xticklabels([seasons[i][:4] for i in ticks])
    fig.suptitle("PageRank (TB = 1) của 6 CLB lớn qua các mùa", x=0.01, ha="left")
    fig.savefig(out / "fig2_pagerank_big6.png", dpi=170, bbox_inches="tight"); plt.close(fig)


def fig3(val, out):
    """Tương quan hạng Spearman giữa PageRank mùa và bảng xếp hạng cuối mùa (mùa đủ 380 trận)."""
    v = val[val.n_matches == 380]; m = v.spearman_pagerank_vs_points.mean()
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.plot(range(len(v)), v.spearman_pagerank_vs_points, "o", color=CAT[0])
    ax.axhline(m, color=MUTED, ls="--"); ax.text(len(v) - 0.5, m + 0.002, f"TB {m:.3f}", ha="right")
    ax.set_xticks(range(0, len(v), 3)); ax.set_xticklabels(v.season.values[::3], fontsize=8)
    ax.set_ylim(0.78, 1.0); ax.set_ylabel("Spearman")
    ax.set_title("PageRank mùa giải khớp bảng xếp hạng cuối mùa", loc="left")
    fig.savefig(out / "fig3_pagerank_vs_table.png", dpi=170, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--dir", default="results")
    d = Path(ap.parse_args().dir)
    nodes = pd.read_csv(d / "node_metrics_alltime.csv"); edges = pd.read_csv(d / "edges_alltime.csv")
    by_season = pd.read_csv(d / "node_metrics_by_season.csv"); val = pd.read_csv(d / "validation_by_season.csv")
    out = d / "replot"; out.mkdir(exist_ok=True)
    fig1(nodes, edges, out); fig2(by_season, val, out); fig3(val, out)
    print("Đã lưu 3 hình vào", out)

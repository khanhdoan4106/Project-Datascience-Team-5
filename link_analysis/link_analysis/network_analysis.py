"""Bước 2 – Phân tích mạng lưới đối đầu Premier League.

  * Đồ thị "ưu thế" (có hướng): bên thua/hòa "bầu" cho bên thắng theo phần điểm; PageRank = sức mạnh mạng lưới.
  * Đồ thị "số lần gặp" (vô hướng): trọng số = số trận giữa hai CLB; dùng cho cộng đồng (Louvain) và cặp đáng chú ý.

Đầu ra (thư mục --out): node_metrics_by_season.csv, node_metrics_alltime.csv, edges_alltime.csv, notable_pairs.csv,
validation_by_season.csv, network_summary.json và 3 hình PNG.

Chạy:  python network_analysis.py --matches matches.csv --out results
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from build_graph_features import MARGIN_CAP, PR_ALPHA, pagerank

# mau dinh tinh co dinh theo thu tu (bang mau goc cua skill dataviz; 3 mau dau hop le khi dung tat ca cac cap)
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK, INK2, GRID, SURFACE, MUTED = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb", "#b9b8b2"
BIG6 = ["Arsenal", "Chelsea", "Liverpool", "Manchester City", "Manchester United", "Tottenham"]


def share(hg, ag):
    return 0.5 + 0.5 * np.clip(hg - ag, -MARGIN_CAP, MARGIN_CAP) / MARGIN_CAP


def dominance_pagerank(df, teams):
    ix = {t: i for i, t in enumerate(teams)}
    n = len(teams)
    h, a = df.home_team.map(ix).values, df.away_team.map(ix).values
    s = share(df.home_goals.values.astype(float), df.away_goals.values.astype(float))
    V = np.zeros((n, n))
    np.add.at(V, (a, h), s)
    np.add.at(V, (h, a), 1 - s)
    active = np.where(V.sum(1) + V.sum(0) > 0)[0]
    return dict(zip(teams, pagerank(V, active, PR_ALPHA))), V


def season_table(d):
    rows = []
    for _, r in d.iterrows():
        rows.append((r.home_team, 3 if r.home_goals > r.away_goals else int(r.home_goals == r.away_goals), r.home_goals - r.away_goals))
        rows.append((r.away_team, 3 if r.away_goals > r.home_goals else int(r.home_goals == r.away_goals), r.away_goals - r.home_goals))
    t = pd.DataFrame(rows, columns=["team", "pts", "gd"]).groupby("team").agg(pts=("pts", "sum"), gd=("gd", "sum"), played=("pts", "size"))
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matches", required=True)
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(exist_ok=True)
    m = pd.read_csv(a.matches)
    m = m[m.status == "played"].copy()
    teams = sorted(set(m.home_team) | set(m.away_team))
    seasons = sorted(m.season.unique())

    # ---------------- 1. PageRank theo tung mua + doi chieu bang xep hang
    rows, val = [], []
    for s in seasons:
        d = m[m.season == s]
        pr, V = dominance_pagerank(d, teams)
        tab = season_table(d)
        tab["pagerank"] = pd.Series(pr)
        tab = tab.dropna(subset=["pagerank"])
        tab["rank_points"] = tab[["pts", "gd"]].apply(tuple, axis=1).rank(ascending=False, method="min")
        tab["rank_pagerank"] = tab.pagerank.rank(ascending=False, method="min")
        tab["season"] = s
        rows.append(tab.reset_index())
        # chi so hop le chi voi mua du tran (bo mua thieu tran)
        val.append({"season": s, "n_matches": len(d), "spearman_pagerank_vs_points":
                    spearmanr(tab.pagerank, tab.pts + tab.gd / 1000).statistic})
    by_season = pd.concat(rows, ignore_index=True)
    by_season["rank_gap"] = by_season.rank_points - by_season.rank_pagerank  # >0: PageRank xep cao hon bang diem
    by_season.round(4).to_csv(out / "node_metrics_by_season.csv", index=False)
    val = pd.DataFrame(val)
    val.round(4).to_csv(out / "validation_by_season.csv", index=False)

    # ---------------- 2. Mang luoi toan thoi gian
    pr_all, V_all = dominance_pagerank(m, teams)
    G = nx.Graph()
    G.add_nodes_from(teams)
    cnt = m.assign(a=np.where(m.home_team < m.away_team, m.home_team, m.away_team),
                   b=np.where(m.home_team < m.away_team, m.away_team, m.home_team)).groupby(["a", "b"]).size()
    for (x, y), w in cnt.items():
        G.add_edge(x, y, weight=int(w))
    comms = nx.community.louvain_communities(G, weight="weight", resolution=1.0, seed=7)
    comms = sorted(comms, key=lambda c: -len(c))
    cid = {t: i for i, c in enumerate(comms) for t in c}

    full_seasons = set(val[val.n_matches >= 335].season)
    n_seasons = by_season.groupby("team").size()
    first = by_season.groupby("team").season.min()
    last = by_season.groupby("team").season.max()
    nodes = pd.DataFrame({
        "team": teams,
        "community": [cid[t] for t in teams],
        "pagerank_alltime": [pr_all[t] for t in teams],
        "degree_opponents": [G.degree(t) for t in teams],
        "strength_matches": [G.degree(t, weight="weight") for t in teams],
        "seasons_in_league": [int(n_seasons.get(t, 0)) for t in teams],
        "first_season": [first.get(t) for t in teams], "last_season": [last.get(t) for t in teams],
        # TB PageRank cac mua du tran (bo mua dang dien ra): phan anh suc manh, khong bi thoi phong boi so mua choi
        "mean_season_pagerank": [by_season[(by_season.team == t) & by_season.season.isin(full_seasons)].pagerank.mean() for t in teams],
    }).sort_values("pagerank_alltime", ascending=False)
    nodes.round(4).to_csv(out / "node_metrics_alltime.csv", index=False)
    pd.DataFrame([{"team_a": x, "team_b": y, "meetings": d["weight"]} for x, y, d in G.edges(data=True)]
                 ).sort_values("meetings", ascending=False).to_csv(out / "edges_alltime.csv", index=False)

    # ---------------- 3. Cap doi dau dang chu y
    recs = []
    for (x, y), w in cnt.items():
        d = m[((m.home_team == x) & (m.away_team == y)) | ((m.home_team == y) & (m.away_team == x))]
        px = sum(3 if (r.home_team == x and r.home_goals > r.away_goals) or (r.away_team == x and r.away_goals > r.home_goals)
                 else int(r.home_goals == r.away_goals) for r in d.itertuples())
        py = sum(3 if (r.home_team == y and r.home_goals > r.away_goals) or (r.away_team == y and r.away_goals > r.home_goals)
                 else int(r.home_goals == r.away_goals) for r in d.itertuples())
        wins_x = sum((r.home_team == x and r.home_goals > r.away_goals) or (r.away_team == x and r.away_goals > r.home_goals) for r in d.itertuples())
        wins_y = sum((r.home_team == y and r.home_goals > r.away_goals) or (r.away_team == y and r.away_goals > r.home_goals) for r in d.itertuples())
        recs.append({"team_a": x, "team_b": y, "meetings": int(w), "wins_a": wins_x, "wins_b": wins_y,
                     "draws": int(w) - wins_x - wins_y, "points_share_a": px / max(px + py, 1)})
    pairs = pd.DataFrame(recs)
    pairs["lopsidedness"] = (pairs.points_share_a - 0.5).abs()
    pairs.round(4).to_csv(out / "notable_pairs.csv", index=False)

    summary = {
        "n_teams": len(teams), "n_matches": len(m), "n_edges_undirected": G.number_of_edges(),
        "density": round(nx.density(G), 4),
        "communities": [{"id": i, "size": len(c), "mean_seasons": round(float(nodes[nodes.team.isin(c)].seasons_in_league.mean()), 1),
                         "members": sorted(c, key=lambda t: -pr_all[t])} for i, c in enumerate(comms)],
        "modularity": round(nx.community.modularity(G, comms, weight="weight"), 4),
        "spearman_mean": round(val[val.n_matches == 380].spearman_pagerank_vs_points.mean(), 4),
        "spearman_min": round(val[val.n_matches == 380].spearman_pagerank_vs_points.min(), 4),
    }
    json.dump(summary, open(out / "network_summary.json", "w"), ensure_ascii=False, indent=1)

    figures(G, comms, cid, pr_all, nodes, by_season, val, out)
    print(json.dumps(summary, ensure_ascii=False, indent=1))


# ------------------------------------------------------------------ hinh
def style(ax):
    ax.set_facecolor(SURFACE)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def figures(G, comms, cid, pr_all, nodes, by_season, val, out):
    plt.rcParams["font.family"] = "DejaVu Sans"
    # ---- hinh 1: mang luoi toan thoi gian. Do thi gan day du (mat do ~0.77) nen layout luc dan thanh mot cum;
    # dung bo cuc vong tron: xep theo cong dong roi theo suc manh, chi ve 8% cap gap nhau nhieu nhat.
    fig, ax = plt.subplots(figsize=(11, 11), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    info = nodes.set_index("team")
    order = sorted(G.nodes, key=lambda t: (cid[t], -info.mean_season_pagerank.fillna(0)[t]))
    ang = {t: np.pi / 2 - 2 * np.pi * i / len(order) for i, t in enumerate(order)}
    pos = {t: (np.cos(ang[t]), np.sin(ang[t])) for t in order}
    ws = np.array([d["weight"] for _, _, d in G.edges(data=True)])
    thr = np.percentile(ws, 92)
    strong = [(u, v) for u, v, d in G.edges(data=True) if d["weight"] >= thr]
    for u, v in strong:
        ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], color=MUTED, alpha=0.5,
                lw=0.4 + 2.2 * (G[u][v]["weight"] - thr) / (ws.max() - thr + 1e-9), zorder=1)
    sz = info.mean_season_pagerank.fillna(info.mean_season_pagerank.min())
    for t in order:
        ax.scatter(*pos[t], s=60 + 900 * (sz[t] - sz.min()) / (sz.max() - sz.min()), color=CAT[cid[t] % len(CAT)],
                   edgecolor=SURFACE, linewidth=1.5, zorder=3)
        deg = np.degrees(ang[t])
        left = np.cos(ang[t]) < 0
        ax.text(1.09 * pos[t][0], 1.09 * pos[t][1], t, fontsize=8.5, color=INK, va="center",
                ha="right" if left else "left", rotation=deg + 180 if left else deg, rotation_mode="anchor")
    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-1.45, 1.45)
    ax.set_aspect("equal")
    ax.set_axis_off()
    handles = [plt.Line2D([], [], marker="o", ls="", ms=10, color=CAT[i % len(CAT)],
                          label=f"Nhóm {i + 1}: {len(c)} CLB, TB {nodes[nodes.team.isin(c)].seasons_in_league.mean():.0f} mùa")
               for i, c in enumerate(comms)]
    ax.legend(handles=handles, loc="lower left", frameon=False, fontsize=9.5, labelcolor=INK2)
    ax.set_title("Mạng lưới đối đầu Premier League 2000/01 – 2026/27", loc="left", fontsize=14, color=INK, pad=6)
    fig.text(0.02, 0.06, "Nút: kích thước ∝ PageRank trung bình theo mùa; màu: cộng đồng (Louvain trên số lần gặp, modularity thấp).\n"
             "Cạnh: 8% cặp gặp nhau nhiều nhất, độ dày ∝ số lần gặp. Mạng gần như đầy đủ (mật độ 0,77).", fontsize=8.5, color=INK2)
    fig.savefig(out / "fig1_network_alltime.png", dpi=170, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)

    # ---- hinh 2: PageRank theo mua cua 6 CLB lon (small multiples)
    by_season = by_season[by_season.season.isin(set(val[val.n_matches >= 335].season))]  # bo mua dang dien ra (it tran)
    seasons = sorted(by_season.season.unique())
    xs = {s: i for i, s in enumerate(seasons)}
    fig, axes = plt.subplots(2, 3, figsize=(12, 6.2), sharex=True, sharey=True, facecolor=SURFACE)
    for ax, t in zip(axes.ravel(), BIG6):
        style(ax)
        for o in by_season.team.unique():
            d = by_season[by_season.team == o]
            ax.plot([xs[s] for s in d.season], d.pagerank, color=GRID, lw=1, zorder=1)
        d = by_season[by_season.team == t]
        ax.plot([xs[s] for s in d.season], d.pagerank, color=CAT[0], lw=2, zorder=3)
        ax.axhline(1, color=MUTED, lw=0.8, ls=(0, (3, 3)))
        ax.set_title(t, loc="left", fontsize=10.5, color=INK)
    ticks = [i for i, s in enumerate(seasons) if s[:4] in ("2000", "2005", "2010", "2015", "2020", "2025")]
    axes[0, 0].set_xticks(ticks)
    axes[0, 0].set_xticklabels([seasons[i][:4] for i in ticks])
    for ax in axes[:, 0]:
        ax.set_ylabel("PageRank (TB = 1)", fontsize=9, color=INK2)
    fig.suptitle("Sức mạnh mạng lưới của 6 CLB lớn qua các mùa (xám: các CLB còn lại)", x=0.01, ha="left", fontsize=13, color=INK)
    fig.savefig(out / "fig2_pagerank_big6.png", dpi=170, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)

    # ---- hinh 3: PageRank co khop bang xep hang?
    v = val[val.n_matches == 380]
    fig, ax = plt.subplots(figsize=(10, 3.8), facecolor=SURFACE)
    style(ax)
    x = np.arange(len(v))
    ax.plot(x, v.spearman_pagerank_vs_points, "o", color=CAT[0], ms=7, mec=SURFACE, mew=1.5)
    ax.axhline(v.spearman_pagerank_vs_points.mean(), color=MUTED, lw=1, ls=(0, (3, 3)))
    ax.text(len(v) - 0.5, v.spearman_pagerank_vs_points.mean() + 0.002, f"TB {v.spearman_pagerank_vs_points.mean():.3f}",
            ha="right", va="bottom", fontsize=9, color=INK2)
    ax.set_xticks(x[::3])
    ax.set_xticklabels(v.season.values[::3], fontsize=8.5)
    ax.set_ylim(0.78, 1.0)
    ax.set_ylabel("Tương quan hạng Spearman", fontsize=9, color=INK2)
    ax.set_title("PageRank mùa giải khớp bảng xếp hạng cuối mùa đến mức nào (mỗi chấm một mùa 380 trận)", loc="left", fontsize=12.5, color=INK, pad=10)
    fig.savefig(out / "fig3_pagerank_vs_table.png", dpi=170, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    main()

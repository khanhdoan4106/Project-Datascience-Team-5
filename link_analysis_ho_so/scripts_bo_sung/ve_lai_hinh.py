"""Vẽ lại 5 hình của Link Analysis chỉ từ các CSV trong results/ (không cần matches.csv, không chạy lại đánh giá).

Dùng khi cần chỉnh hình cho slide: sửa src/figures.py rồi chạy lại script này.
Chạy từ thư mục link_analysis/:
    python <đường dẫn>/ve_lai_hinh.py --results results --out figures/replot
"""
import argparse
import sys
from pathlib import Path

import networkx as nx
import pandas as pd

sys.path.insert(0, "src")
import figures as fg  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--results", default="results")
ap.add_argument("--out", default="figures/replot")
a = ap.parse_args()
R, out = Path(a.results), Path(a.out)
out.mkdir(parents=True, exist_ok=True)

# hình 1, 1b: dựng lại đồ thị số lần gặp và cộng đồng từ file cạnh / nút
nodes = pd.read_csv(R / "node_metrics_alltime.csv").set_index("team")
edges = pd.read_csv(R / "edges_alltime.csv")
G = nx.Graph()
G.add_nodes_from(nodes.index)
G.add_weighted_edges_from(edges[["team_a", "team_b", "meetings"]].itertuples(index=False))
comms = [set(g.index) for _, g in nodes.groupby("community")]
comms = sorted(comms, key=len, reverse=True)
strength = nodes.mean_season_pagerank.fillna(nodes.mean_season_pagerank.min())
pairs = pd.read_csv(R / "notable_pairs.csv")
fg.network(G, comms, strength, nodes.seasons_in_league, pairs, highlight=False, path=out / "1_mang_luoi.png")
fg.network(G, comms, strength, nodes.seasons_in_league, pairs, highlight=True, path=out / "1b_mang_luoi_noi_bat.png")

# hình 2: PageRank so với bảng xếp hạng
val = pd.read_csv(R / "validation_by_season.csv").rename(columns={"spearman_pagerank_vs_points": "spearman"})
val = val[val.n_matches == 380]
bs = pd.read_csv(R / "node_metrics_by_season.csv")
bs = bs[bs.season.isin(val.season)]
champ_rank = bs[bs.rank_points == 1].set_index("season").rank_pagerank
low = val.loc[val.spearman.idxmin()]
d = bs[bs.season == low.season]
gaps = d[d.rank_gap.abs() == d.rank_gap.abs().max()].sort_values("rank_points")
note = f"{low.season}: {fg.vn(low.spearman, 3)}, thấp nhất\n" + "\n".join(
    f"{g.team}: hạng {int(g.rank_points)} theo điểm, hạng {int(g.rank_pagerank)} theo PageRank" for g in gaps.itertuples())
fg.spearman_by_season(val[["season", "spearman"]], champ_rank, note_text=note, path=out / "2_pagerank_vs_bxh.png")

# hình 3: ví dụ mùa 2015/16
ex = bs[bs.season == "2015/16"].set_index("team")
fg.season_example(ex[["pts", "pagerank"]], "2015/16",
                  {"Leicester": "vô địch, 81 điểm, hạng 2 PageRank,\nthắng cách biệt từ 3 bàn 4 trận",
                   "Tottenham": "hạng 3 theo điểm (70) nhưng đứng đầu PageRank,\nthắng cách biệt từ 3 bàn 9 trận"},
                  path=out / "3_vi_du_mua_2015_16.png")

# hình 4: kết quả đánh giá
rows = pd.read_csv(R / "evaluation_summary.csv")
fg.evaluation(rows, "85 đặc trưng", path=out / "4_danh_gia.png")
print("Đã lưu 5 hình vào", out)

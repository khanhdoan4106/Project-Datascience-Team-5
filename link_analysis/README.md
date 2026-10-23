# Link Analysis – Đồ thị đội bóng và đặc trưng mạng lưới

Phần Link Analysis của dự án **Football Match Outcome Prediction** (Nhóm 5). Phần này biểu diễn các CLB Premier League thành đồ thị và phân tích mạng lưới đối đầu. Từ đồ thị, nó tạo ra đặc trưng chỉ dùng thông tin có trước trận đấu, rồi kiểm tra xem các đặc trưng đó có giúp dự đoán kết quả tốt hơn không.

**Kết luận chính:** PageRank là thước đo sức mạnh hợp lý: tương quan hạng Spearman với bảng xếp hạng cuối mùa trung bình 0,937. Tuy vậy, thêm đặc trưng đồ thị vào bộ 85 đặc trưng của nhóm **không cải thiện dự đoán**. Chênh lệch log loss là +0,0011 với khoảng tin cậy 95% [−0,0008, +0,0029], chứa 0. Nguyên nhân là các đặc trưng này trùng thông tin với Elo. Khâu Xây dựng mô hình không bắt buộc phải dùng chúng.

## Cấu trúc thư mục

```
link_analysis/
├── README.md                    tài liệu này
├── requirements.txt
├── run_all.sh                   chạy lại toàn bộ từ đầu
├── build_graph_features.py      Bước 1: dựng đồ thị, tính 9 đặc trưng gr_*, tự kiểm tra rò rỉ
├── network_analysis.py          Bước 2: phân tích mạng lưới, cộng đồng, cặp đối đầu, 3 hình
├── plot_figures.py              vẽ lại 3 hình chỉ từ các CSV kết quả
├── evaluate_graph_features.py   thư viện đánh giá dùng chung
├── evaluate_on_features.py      Bước 3: có / không có đặc trưng đồ thị (Gradient Boosting, Logistic Regression)
├── evaluate_logreg_robust.py    Bước 3b: kiểm lại kết luận với Logistic Regression đã sửa chuẩn hóa
├── evaluate_on_matches.py       Bước 3c: so với Elo tự tính và kèo nhà cái, chỉ cần matches.csv
├── test_graph_features.py       kiểm thử công thức, rò rỉ dữ liệu, toàn vẹn đầu ra
├── docs/
│   ├── METHODOLOGY.md           giải thích từng bước kèm mã
│   ├── FEATURES_DICTIONARY.md   ý nghĩa 9 cột gr_* (cho khâu Xây dựng mô hình, Tích hợp & báo cáo)
│   └── DATA_ISSUES.md           vấn đề dữ liệu cần báo khâu Thu thập, Tích hợp dữ liệu
└── results/
    ├── graph_features_matches.csv   SẢN PHẨM CHÍNH: 9.850 dòng, khóa match_id
    ├── node_metrics_by_season.csv   PageRank, điểm, hạng của từng CLB theo mùa
    ├── node_metrics_alltime.csv     cộng đồng, số đối thủ, số mùa, PageRank TB
    ├── edges_alltime.csv            cạnh: số lần gặp giữa hai CLB
    ├── notable_pairs.csv            cặp gặp nhiều, cặp chênh lệch lớn
    ├── validation_by_season.csv     Spearman PageRank và bảng xếp hạng theo mùa
    ├── network_summary.json         mật độ, cộng đồng, modularity
    ├── eval_features.txt            kết quả Bước 3
    ├── eval_logreg_robust.txt       kết quả Bước 3b
    ├── eval_matches.txt             kết quả Bước 3c
    └── fig1/2/3_*.png               3 hình của báo cáo
```

## Chạy lại

```bash
pip install -r requirements.txt
# matches.csv và features.csv lấy từ khâu Tích hợp & chuẩn bị dữ liệu (data/clean/, sinh bởi run_prepare.py trên nhánh Data_itegration)
bash run_all.sh path/to/matches.csv path/to/features.csv
```

Từng bước riêng:

| Lệnh | Thời gian | Đầu ra |
|---|---|---|
| `python build_graph_features.py --dataset matches.csv --out results/graph_features_matches.csv --selftest` | ~10 giây | đặc trưng + kết quả tự kiểm tra |
| `python network_analysis.py --matches matches.csv --out results` | ~10 giây | CSV mạng lưới + 3 hình |
| `python plot_figures.py --dir results` | vài giây | 3 hình trong `results/replot/` |
| `python evaluate_on_features.py --features features.csv --graph results/graph_features_matches.csv` | 5–10 phút | bảng so sánh mô hình |
| `python evaluate_logreg_robust.py --features features.csv --graph results/graph_features_matches.csv` | 2–3 phút | kiểm lại với Logistic Regression |
| `python evaluate_on_matches.py --matches matches.csv --graph results/graph_features_matches.csv` | 3–5 phút | so với Elo, kèo nhà cái |
| `python test_graph_features.py` (hoặc `pytest`) | ~1 phút | 5 kiểm thử, cần `matches.csv` trong thư mục |

## Dùng đặc trưng đồ thị (khâu Xây dựng mô hình, Tích hợp & báo cáo)

```python
import pandas as pd
features = pd.read_csv("features.csv")
graph = pd.read_csv("link_analysis/results/graph_features_matches.csv")
df = features.merge(graph.filter(regex="^(match_id|gr_)"), on="match_id", how="left", validate="1:1")
```

Năm cột nên thử là `gr_pagerank_log_ratio`, `gr_common_opp_diff`, `gr_trans2_diff`, `gr_h2h_share` và `gr_h2h_gd`. Ý nghĩa từng cột có trong `docs/FEATURES_DICTIONARY.md`. Khi khâu Tích hợp & chuẩn bị dữ liệu cập nhật dữ liệu, cần chạy lại Bước 1.

## Kết quả đã kiểm chứng (23/10/2026)

- **Chạy lại từ bản sao sạch:** cho ra `graph_features_matches.csv` và các CSV mạng lưới giống hệt từng giá trị.
- **Kiểm tra rò rỉ dữ liệu:** đạt 2 cách kiểm tra.
  - Cắt mọi trận từ ngày D trở đi, tính lại đặc trưng ngày D: không đổi, thử trên 6 ngày ngẫu nhiên.
  - Đảo ngẫu nhiên kết quả mọi trận từ ngày D trở đi: đặc trưng ngày D không đổi, thử trên 8 ngày ngẫu nhiên.
- **Số liệu trong báo cáo:** đều được tính lại và khớp.

Báo cáo đầy đủ (Docs): https://claude.ai/code/artifact/04d68d8c-62eb-42c4-bc07-15dfa7c74bab

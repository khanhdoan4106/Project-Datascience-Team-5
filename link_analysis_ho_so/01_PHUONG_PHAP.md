# Phương pháp Link Analysis: giải thích từng bước kèm mã

Tài liệu cá nhân, đi kèm gói `link_analysis/` trên nhánh nhóm. Mã nguồn được trích nằm trong `link_analysis/src/`; kết quả số trích từ `link_analysis/results/evaluation.txt`.

Tài liệu đi theo đúng thứ tự chạy của pipeline. Mỗi bước có ba phần: **làm gì**, **vì sao làm như vậy** và **mã thực hiện** (trích từ file nguồn trong `src/`).

```
clean/matches.csv ──► [1] build_graph_features.py ──► results/graph_features_matches.csv
        │                                                        │
        └──────────► [2] network_analysis.py ──► results/node_*.csv, edges_alltime.csv, notable_pairs.csv, hình 1–3
                                                                 │
clean/features.csv ────────────────────────────────► [3] evaluate.py ──► results/evaluation.txt, evaluation_summary.csv,
                                                                          feature_candidates_link_analysis.csv, hình 4
                     [T] tests/test_graph_features.py: công thức, đối chiếu networkx, rò rỉ, toàn vẹn đầu ra
                     figures.py: mọi hình (dùng chung cho script và notebook)
                     link_analysis_tung_buoc.ipynb: đi lại bước 0–8 trong Jupyter, khoảng 2 phút
```

---

## Bước 0. Dữ liệu đầu vào

**Làm gì.** Bước này đọc `matches.csv` của khâu Tích hợp & chuẩn bị dữ liệu (9.850 trận, 2000/01–2026/27, 46 CLB) và chỉ giữ các trận đã đá (`status == "played"`).

**Vì sao.** File đã gộp nhiều nguồn, chuẩn hóa tên CLB và có `match_id`, nên đặc trưng đồ thị ghép được 1-1 với `features.csv`. Dữ liệu thô của khâu Thu thập có tên CLB chưa thống nhất giữa các nguồn, nên không dùng.

**Cột cần:** `match_id, season, date, home_team, away_team, status, home_goals, away_goals`.

---

## Bước 1. Phần điểm của một trận

**Làm gì.** Mỗi trận được quy về một số s ∈ [0, 1], là phần điểm của đội nhà:

s = 0,5 + 0,5 × clip(bàn nhà − bàn khách, −3, 3) / 3

Ví dụ: hòa cho s = 0,5; thắng 1-0 cho s = 0,67; thắng từ 3 bàn trở lên cho s = 1.

**Vì sao.**
- Chỉ dùng thắng/hòa/thua thì mất thông tin về mức độ thắng.
- Dùng hiệu số thô thì một trận 7-0 sẽ chi phối cả mạng lưới.
- Chặn ở 3 bàn giữ được mức độ thắng mà vẫn chống được nhiễu.

```python
MARGIN_CAP = 3

def share_of_home(hg, ag):
    return 0.5 + 0.5 * np.clip(hg - ag, -MARGIN_CAP, MARGIN_CAP) / MARGIN_CAP
```

---

## Bước 2. Hai đồ thị

**Làm gì.**
- **Đồ thị ưu thế (có hướng).** Trong mỗi trận, bên thua hoặc hòa "bầu" cho bên thắng. Đội khách bầu cho đội nhà với trọng số s, đội nhà bầu cho đội khách với trọng số 1 − s. `V[i, j]` là tổng phiếu i bầu cho j.
- **Đồ thị số lần gặp (vô hướng).** Trọng số cạnh là số trận giữa hai CLB.

**Vì sao.** PageRank cần hướng để biểu diễn "ai mạnh hơn ai". Theo ý tưởng của bài giảng, phiếu bầu từ một nút mạnh có giá trị hơn phiếu từ nút yếu, nên thắng đội mạnh được tính nhiều hơn thắng đội yếu. Đồ thị vô hướng chỉ cho biết ai hay gặp ai, nên được dùng để phát hiện cộng đồng.

```python
V = np.zeros((n, n))                     # V[i, j]: i "bầu" cho j
np.add.at(V, (a, h), w * s)              # đội khách bầu cho đội nhà theo phần điểm của đội nhà
np.add.at(V, (h, a), w * (1 - s))        # đội nhà bầu cho đội khách theo phần còn lại
```

---

## Bước 3. PageRank

**Làm gì.** Bước này tính PageRank bằng phương pháp lặp lũy thừa, với hệ số 0,85. Nút không có cạnh ra (đội chưa thua hoặc hòa ai trong cửa sổ) nhảy đều sang mọi nút. Kết quả được chuẩn hóa để trung bình bằng 1.

**Vì sao.**
- 0,85 là giá trị chuẩn trong bài giảng. Bước này không dò tham số này trên tập kiểm thử, để tránh làm đẹp kết quả.
- Xử lý nút kết (dangling node) bảo đảm ma trận chuyển là ngẫu nhiên, nên phép lặp hội tụ.
- Chuẩn hóa trung bình bằng 1 giúp so sánh được giữa các mùa có số đội khác nhau.

```python
def pagerank(V, active, alpha=0.85, iters=200, tol=1e-10):
    k = len(active)
    sub = V[np.ix_(active, active)]
    out = sub.sum(1, keepdims=True)
    P = np.where(out > 0, sub / np.where(out > 0, out, 1), 1.0 / k)   # dangling -> nhảy đều
    r = np.full(k, 1.0 / k)
    for _ in range(iters):
        new = alpha * (r @ P) + (1 - alpha) / k                      # teleport 15%
        if np.abs(new - r).sum() < tol:
            r = new
            break
        r = new
    res = np.full(V.shape[0], np.nan)
    res[active] = r * k                                              # trung bình = 1
    return res
```

---

## Bước 4. Không dùng thông tin tương lai: cửa sổ và trọng số thời gian

**Làm gì.** Với mỗi ngày thi đấu D, đồ thị chỉ được dựng từ các trận có ngày **nhỏ hơn D** trong 3 năm gần nhất. Mỗi trận có trọng số w = 0,5^(số ngày trước D / 365). Các trận cùng một ngày dùng chung một đồ thị.

**Vì sao.**
- Đặc trưng của một trận chỉ được phép dùng thông tin có trước trận đó; đây là yêu cầu bắt buộc của đề bài.
- Sức mạnh đội bóng thay đổi nhanh, nên trận cách đây một năm chỉ được tính một nửa.
- Dùng ngày < D (chứ không phải ≤ D) loại luôn các trận cùng ngày, vì kết quả của chúng chưa biết lúc trận khác bắt đầu.

```python
for day, grp in t.groupby("_day", sort=True):
    end = np.searchsorted(pd_days, day, side="left")                  # chỉ các trận có ngày < day
    start = np.searchsorted(pd_days, day - WINDOW_DAYS, side="left")  # cửa sổ 3 năm
    sl = slice(start, end)
    w = 0.5 ** ((day - pd_days[sl]) / HALF_LIFE_DAYS)                 # nửa đời 365 ngày
```

---

## Bước 5. Các đặc trưng còn lại

**Làm gì.** Bước này tính ba nhóm đặc trưng cho mỗi trận (h, a). `A[i, j]` là phần điểm trung bình có trọng số của i trước j, trừ 0,5.

1. **Đối thủ chung:** trung bình của `A[h, c] − A[a, c]` trên các đối thủ c mà cả hai đội đã gặp.
2. **Bắc cầu 2 bước:** `(T @ T)[h, a] − (T @ T)[a, h]`, với T là phần dương của A. Nếu h thắng c và c thắng a, thì h có ưu thế gián tiếp trước a.
3. **Đối đầu có trọng số:** dùng các lần gặp trực tiếp trong 10 năm gần nhất, nửa đời 3 năm, và co về trung tính bằng 1 trận ảo.

**Vì sao.**
- Hai nhóm đầu cho thông tin về các cặp ít hoặc chưa gặp nhau, đúng ý tưởng liên kết gián tiếp của Link Analysis.
- Việc co về trung tính tránh tỷ lệ cực đoan khi hai đội chỉ gặp nhau 1 trận. Ví dụ thắng 1 trận 3-0 thì `h2h_share` chỉ là 0,25 chứ không phải 0,5.

```python
co = float(np.average(A[hi][mask] - A[ai][mask], weights=wt))          # đối thủ chung
T2 = T @ T;  trans2 = T2[hi, ai] - T2[ai, hi]                           # bắc cầu 2 bước
h2h_share = ((hw * sh).sum() + 0.5 * H2H_SHRINK) / (wsum + H2H_SHRINK) - 0.5
```

Kết quả: `results/graph_features_matches.csv`, gồm 9 cột `gr_*` (xem `03_TU_DIEN_DAC_TRUNG.md`).

---

## Bước 6. Kiểm chứng không rò rỉ

**Làm gì.** Có hai cách kiểm tra độc lập.
- `--selftest` cắt bỏ mọi trận từ ngày D trở đi, tính lại đặc trưng ngày D và so với lần tính đầy đủ.
- `test_future_results_do_not_change_features` đảo ngẫu nhiên tỷ số của mọi trận từ ngày D trở đi; đặc trưng của ngày D phải y hệt.

**Vì sao.** Hai cách này là bằng chứng kiểm chứng được, thay cho một lời cam đoan. Cách thứ hai mạnh hơn: nếu đặc trưng có dùng bất kỳ kết quả nào từ ngày D trở đi, giá trị chắc chắn sẽ thay đổi.

```python
shaken = played.copy()
fut = shaken.date >= D
shaken.loc[fut, "home_goals"] = rng.integers(0, 6, fut.sum())
shaken.loc[fut, "away_goals"] = rng.integers(0, 6, fut.sum())
assert np.allclose(build(played, targets)[FEATURES], build(shaken, targets)[FEATURES], equal_nan=True)
```

Kết quả: sai lệch tối đa 0 trên 6 + 8 ngày ngẫu nhiên.

---

## Bước 7. Phân tích mạng lưới (`network_analysis.py`)

**Làm gì.** Bước này phân tích mạng lưới trên toàn bộ các trận và trên từng mùa.
- Mật độ đồ thị.
- Phát hiện cộng đồng bằng Louvain trên đồ thị số lần gặp.
- Cặp đối đầu gặp nhiều nhất và chênh lệch nhất (tính các cặp gặp từ 20 trận).
- PageRank theo mùa, so với bảng xếp hạng cuối mùa bằng tương quan hạng Spearman.

**Vì sao.** Đề bài yêu cầu phân tích mạng lưới đối đầu. Bước so với bảng xếp hạng là kiểm tra tính hợp lý trước khi dùng PageRank làm đặc trưng. Đây không phải kiểm chứng độc lập, vì PageRank và điểm số đều tính từ cùng các kết quả.

```python
G = nx.Graph()                                   # đồ thị số lần gặp
for (x, y), w in cnt.items():         # cnt: số trận của từng cặp
    G.add_edge(x, y, weight=int(w))
comms = nx.community.louvain_communities(G, weight="weight", resolution=1.0, seed=7)
modularity = nx.community.modularity(G, comms, weight="weight")
# hạng theo điểm, phá hòa bằng hiệu số
rho = spearmanr(tab.pagerank, tab.pts + tab.gd / 1000).statistic
```

Kết quả: mật độ 0,77; 3 cộng đồng với modularity 0,04 (cấu trúc nhóm rất yếu); Spearman trung bình 0,937 (thấp nhất 0,806 ở 2002/03). Bước này sinh hình 1, 1b, 2, 3; cách đọc từng hình ở `06_DOC_HINH.md`.

Các file nút và cạnh có thêm cột `club_id` (`club_id_a`, `club_id_b` với cạnh), lấy từ `home_club_id`/`away_club_id` của `matches.csv`. Đây là mã CLB chuẩn của khâu Tích hợp dữ liệu (ví dụ `ARS`, `MCI`), nên khâu Trực quan hóa và các khâu khác ghép thẳng được với dữ liệu của nhóm mà không phải đối chiếu tên đội.

---

## Bước 8. Đặc trưng có cải thiện dự đoán không (`evaluate.py`, mục A)

**Làm gì.** So 85 đặc trưng số của `features.csv` khi có và khi không có 5 đặc trưng đồ thị (`gr_pagerank_log_ratio`, `gr_common_opp_diff`, `gr_trans2_diff`, `gr_h2h_share`, `gr_h2h_gd`).
- **Chia theo thời gian:** rolling-origin (huấn luyện trên mọi mùa trước, kiểm thử từng mùa từ 2010/11, tổng 6.140 trận) và split của nhóm (huấn luyện đến 2023/24, kiểm thử từ 2024/25, 820 trận).
- **Hai mô hình:** Gradient Boosting (`HistGradientBoostingClassifier`, độ sâu 3, 150 vòng) và Logistic Regression đa lớp có cắt phân vị 1–99% trước khi chuẩn hóa.
- **Chỉ số:** log loss (chính), Brier, accuracy; số mùa mà cấu hình tốt hơn tham chiếu.
- **Kiểm định:** khoảng tin cậy 95% của chênh lệch log loss theo từng trận, bootstrap theo cặp 2.000 lần; mọi so sánh dùng cùng một chuỗi mẫu.
- **Đối chứng:** dùng thẳng cột của khâu Tích hợp dữ liệu: `elo_diff` (chỉ Elo), `odds_*_prob` (chỉ kèo).

**Vì sao.**
- Chia ngẫu nhiên sẽ cho mô hình "nhìn thấy" tương lai.
- So với bộ đặc trưng mạnh nhất của nhóm mới cho kết luận đáng tin; thêm đặc trưng vào một mô hình yếu thì gần như luôn trông có ích.
- Log loss đo chất lượng xác suất, mà xác suất là thứ dashboard của khâu Trực quan hóa hiển thị. Accuracy chỉ nhìn lớp có xác suất cao nhất và gần như không bao giờ chọn "hòa".
- Bootstrap theo cặp: hai cấu hình dự đoán trên cùng các trận, nên so chênh lệch theo từng trận loại được biến động do độ khó của trận.

```python
rolling = [(df.season < s, df.season == s) for s in seasons if s >= "2010/11"]
d = per_match_logloss(y, probs["85 đặc trưng + đồ thị"]) - per_match_logloss(y, probs["85 đặc trưng"])
rng = np.random.default_rng(0)
lo, hi = np.percentile([d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)], [2.5, 97.5])
```

**Kết quả (rolling, 6.140 trận)**

| Bộ đặc trưng | Gradient Boosting | Logistic Regression |
|---|---|---|
| 85 đặc trưng (tham chiếu) | 0,9835 | 0,9885 |
| 85 đặc trưng + đồ thị | 0,9845: +0,0011, KTC [−0,0009, +0,0029] | 0,9894: +0,0009, KTC [+0,0002, +0,0016] |
| Không kèo → không kèo + đồ thị | 0,9945 → 0,9952: +0,0007, KTC [−0,0016, +0,0031] | 0,9972 → 0,9977: +0,0005, KTC [−0,0005, +0,0014] |
| Chỉ Elo | 0,9887 | 0,9815 |
| Chỉ đồ thị (5 cột) | 0,9914 | 0,9830 |
| Chỉ kèo | 0,9755 | 0,9664 |

Split của nhóm (820 trận): Gradient Boosting 1,0094 → 1,0116 (KTC [−0,0017, +0,0060]); Logistic Regression 1,0202 → 1,0197 (KTC [−0,0021, +0,0011]).

**Đọc kết quả.**
- Không cấu hình nào có KTC nằm hẳn dưới 0, nên đặc trưng đồ thị không cải thiện. Với Logistic Regression, KTC còn nằm hẳn trên 0: thêm vào làm kết quả hơi tệ đi.
- Chỉ dùng 5 đặc trưng đồ thị cho kết quả gần bằng chỉ dùng Elo, nghĩa là đồ thị "học lại" được sức mạnh đội, nhưng không hơn.
- Nguyên nhân: tương quan với `elo_diff` là 0,94 (đối thủ chung), 0,86 (bắc cầu), 0,69 (đối đầu), 0,65 (PageRank); đối đầu có trọng số tương quan 0,85 với `h2h_home_points` (`evaluate.py`, mục C).
- Kèo nhà cái là tín hiệu mạnh nhất, nhưng thời điểm thu thập kèo chưa được xác minh (báo cáo EDA, H9); kết luận về đồ thị đúng cả khi bỏ kèo.
- Với Logistic Regression, chỉ dùng Elo (0,9815) còn tốt hơn cả 85 đặc trưng (0,9885): bộ đặc trưng của nhóm có nhiều biến trùng thông tin.

### Bước 8b. Chẩn đoán Logistic Regression (`scripts_bo_sung/chan_doan_logreg.py`)

Logistic Regression dùng `StandardScaler` thông thường trên 85 đặc trưng cho log loss 1,156, tệ hơn chỉ dùng `elo_diff` (0,981) (rolling 6.140 trận; `ket_qua_bo_sung/danh_gia_logreg_standardscaler.txt`). Trên các mùa kiểm thử 2018/19 – 2025/26, các cách xử lý cho kết quả:

| Cách xử lý | Log loss |
|---|---|
| StandardScaler, 85 đặc trưng | 1,2654 |
| Bỏ `home_rest_days`, `away_rest_days` | 1,2646 |
| Bỏ 14 cột `diff_*` và `elo_home_win_prob` (trùng đại số, EDA đã nêu) | 1,2705 |
| Bỏ cả hai nhóm trên | 1,2654 |
| QuantileTransformer (normal) | 0,9995 |
| Cắt phân vị 1–99% rồi StandardScaler | 0,9801 |
| Chỉ `elo_diff` (đối chiếu) | 0,9780 |

Kết quả gốc: `ket_qua_bo_sung/chan_doan_logreg.txt`.

Nguyên nhân là giá trị ngoại lai đuôi nặng ở nhiều biến (ví dụ các biến trung bình mỗi trận ở đầu mùa tính từ rất ít trận; `rest_days` lệch tới 70 độ lệch chuẩn), không phải đa cộng tuyến. Vì vậy `evaluate.py` dùng cắt phân vị cho Logistic Regression.

```python
class ClipPercentile(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        X = np.asarray(X, float)
        self.lo_, self.hi_ = np.nanpercentile(X, 1, 0), np.nanpercentile(X, 99, 0)   # chỉ học từ tập huấn luyện
        return self

    def transform(self, X):
        return np.clip(np.asarray(X, float), self.lo_, self.hi_)
```

### Bước 8c. Kiểm định giả thuyết H4 của báo cáo EDA (`evaluate.py`, mục B)

**Làm gì.** Báo cáo EDA đề xuất H4: đối đầu (H2H) có bổ sung thông tin sau Elo và phong độ không. Cấu hình đúng như EDA mô tả trong `hypotheses.csv`:
- **Nền:** `elo_diff`, `diff_points5`, `diff_goals_for5`, `diff_goals_against5`.
- **So sánh:** thêm H2H của nhóm (`h2h_home_points`, `h2h_home_goal_diff`, `h2h_matches`), hoặc thêm H2H có trọng số thời gian của Link Analysis (`gr_h2h_share`, `gr_h2h_gd`).
- **Mẫu:** cùng một tập trận; lặp lại trên nhóm trận có `h2h_matches ≥ 3`.

**Vì sao.** "Thành tích đối đầu có trọng số" nằm trong phạm vi Link Analysis, nên đây là chỗ trả lời trực tiếp một giả thuyết của nhóm.

| Mô hình | Mẫu | Elo + phong độ | + H2H của nhóm | + H2H có trọng số |
|---|---|---|---|---|
| Gradient Boosting | 6.140 trận | 0,9911 | 0,9911 (KTC [−0,0026, +0,0026]) | 0,9919 (KTC [−0,0015, +0,0031]) |
| Gradient Boosting | `h2h_matches ≥ 3`, 5.260 trận | 0,9890 | 0,9888 (KTC [−0,0028, +0,0026]) | 0,9899 (KTC [−0,0014, +0,0033]) |
| Logistic Regression | 6.140 trận | 0,9810 | 0,9815 (KTC [−0,0007, +0,0016]) | 0,9812 (KTC [−0,0005, +0,0008]) |
| Logistic Regression | `h2h_matches ≥ 3`, 5.260 trận | 0,9781 | 0,9786 (KTC [−0,0007, +0,0017]) | 0,9783 (KTC [−0,0005, +0,0009]) |

**Kết luận.** H4 không được ủng hộ: mọi KTC đều chứa 0, kể cả trên nhóm trận có nhiều lần gặp. Kết quả khớp nhận xét của EDA rằng khác biệt theo H2H thu hẹp khi xét các trận có Elo gần nhau.

### Bước 9. Bàn giao theo khuôn của nhóm (`evaluate.py`, mục D)

- `results/feature_candidates_link_analysis.csv`: 9 cột `gr_*` theo đúng 13 cột của `feature_candidates.csv` (EDA). Cách tính Spearman giống EDA; đã tái lập đúng giá trị EDA công bố cho `elo_diff` (0,353875), `h2h_home_points` (0,20165), `odds_home_prob` (0,38257). Nối thẳng được với danh mục 87 đặc trưng.
- `results/hypotheses_link_analysis.csv`: kết quả H4 và giả thuyết mới H10 theo khuôn `hypotheses.csv`, thêm cột `result_vi`.
- Các file nút và cạnh có cột `club_id` của khâu Tích hợp dữ liệu.

### Bước 10. Hình và notebook

- **Hình.** Toàn bộ hình được vẽ bằng `src/figures.py` (một nguồn duy nhất): mạng lưới bản thường và bản nổi bật, PageRank so với bảng xếp hạng, ví dụ mùa 2015/16, kết quả đánh giá. Quy ước màu thống nhất: xanh là dữ liệu chính, đỏ là điểm cần chú ý, xám là nền. Giải thích chi tiết: `06_DOC_HINH.md`. Vẽ lại chỉ từ CSV kết quả: `scripts_bo_sung/ve_lai_hinh.py`.
- **Notebook.** `link_analysis_tung_buoc.ipynb` đi lại toàn bộ luồng trong khoảng 2 phút bằng chính các hàm trong `src/`: ví dụ PageRank 3 đội, mùa 2015/16, tính đặc trưng, kiểm tra rò rỉ, mạng lưới, đánh giá rút gọn (Gradient Boosting) và tương quan. Notebook lưu sẵn kết quả, nên xem trên GitHub không cần chạy. Kết quả của notebook trùng với `results/` (log loss 0,9835 → 0,9845, KTC [−0,0009; +0,0029]).

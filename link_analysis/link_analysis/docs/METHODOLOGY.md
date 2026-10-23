# Phương pháp Link Analysis: giải thích từng bước kèm mã

Tài liệu đi theo đúng thứ tự chạy của pipeline. Mỗi bước có ba phần: **làm gì**, **vì sao làm như vậy** và **mã thực hiện** (trích từ file nguồn trong thư mục này).

```
matches.csv ──► [1] build_graph_features.py ──► results/graph_features_matches.csv ─┐
     │                                                                             ├─► [3] evaluate_on_features.py
     └────────► [2] network_analysis.py ──► results/*.csv, fig1-3.png               │     evaluate_logreg_robust.py
features.csv ──────────────────────────────────────────────────────────────────────┘
                [T] test_graph_features.py kiểm tra công thức, rò rỉ, toàn vẹn đầu ra
```

---

## Bước 0. Dữ liệu đầu vào

**Làm gì.** Bước này đọc `matches.csv` của Người 2 (9.850 trận, 2000/01–2026/27, 46 CLB) và chỉ giữ các trận đã đá (`status == "played"`).

**Vì sao.** File đã gộp nhiều nguồn, chuẩn hóa tên CLB và có `match_id`, nên đặc trưng đồ thị ghép được 1-1 với `features.csv`. Dữ liệu thô của Người 1 có tên CLB chưa thống nhất giữa các nguồn, nên không dùng.

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

Kết quả: `results/graph_features_matches.csv`, gồm 9 cột `gr_*` (xem `FEATURES_DICTIONARY.md`).

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

Kết quả: mật độ 0,77; 3 cộng đồng với modularity 0,04 (cấu trúc nhóm rất yếu); Spearman trung bình 0,937. Ba hình được vẽ lại được từ CSV bằng `plot_figures.py`.

---

## Bước 8. Đặc trưng có cải thiện dự đoán không (`evaluate_on_features.py`)

**Làm gì.** Bước này so bộ 85 đặc trưng số của nhóm khi có và khi không có 5 đặc trưng đồ thị.
- **Chia theo thời gian:** rolling-origin (huấn luyện trên mọi mùa trước, kiểm thử từng mùa từ 2010/11, tổng 6.140 trận) và split của nhóm (huấn luyện đến 2023/24, kiểm thử từ 2024/25).
- **Chỉ số:** log loss, Brier, accuracy.
- **Kiểm định:** khoảng tin cậy 95% của chênh lệch log loss bằng bootstrap theo cặp (2.000 lần).

**Vì sao.**
- Chia ngẫu nhiên sẽ cho mô hình "nhìn thấy" tương lai.
- So với baseline mạnh nhất của nhóm mới cho kết luận đáng tin. Thêm đặc trưng vào một mô hình yếu thì gần như luôn trông có ích.
- Log loss đo chất lượng xác suất, mà xác suất là thứ dashboard của Người 6 sẽ hiển thị.

```python
roll = [(df.season < s, df.season == s) for s in seasons if s >= "2010/11"]
sets = {"baseline day du (co keo)": num, "baseline day du + graph": num + GRAPH}
d = ll_graph - ll_base                                                  # theo từng trận
boot = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
lo, hi = np.percentile(boot, [2.5, 97.5])
```

**Kết quả (Gradient Boosting, rolling, 6.140 trận)**

| Bộ đặc trưng | Log loss | Accuracy |
|---|---|---|
| Baseline 85 đặc trưng | 0,9835 | 0,532 |
| Baseline + đồ thị | 0,9845 | 0,527 |
| Chênh lệch | +0,0011, KTC 95% [−0,0008, +0,0029] | – |

Trên split của nhóm (820 trận), log loss là 1,0094 so với 1,0116, cũng không có ý nghĩa thống kê.

### Bước 8b. Kiểm lại bằng Logistic Regression (`evaluate_logreg_robust.py`)

Logistic Regression với `StandardScaler` trên 85 đặc trưng cho kết quả bất thường: log loss 1,156, tệ hơn chỉ dùng `elo_diff` (0,981). Bỏ riêng `rest_days` không sửa được. Đổi sang `QuantileTransformer(output_distribution="normal")` đưa log loss về 1,020, nên nguyên nhân là nhiều biến có phân phối đuôi nặng. Trên mô hình đã sửa, thêm đặc trưng đồ thị thay đổi log loss +0,0005, KTC 95% [−0,0003, +0,0013], tức vẫn không cải thiện.

**Kết luận.** Hai họ mô hình cho cùng một kết luận: đặc trưng đồ thị không thêm giá trị dự đoán vì trùng thông tin với Elo (tương quan 0,65–0,94).

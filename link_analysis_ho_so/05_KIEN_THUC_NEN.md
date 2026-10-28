# Kiến thức nền cho Link Analysis

Tài liệu này gom các khái niệm lý thuyết đứng sau từng bước, kèm cách chúng được áp dụng vào dữ liệu Premier League. Mục đích là trả lời được câu hỏi "vì sao" ở mức nguyên lý, không chỉ ở mức "đã làm gì".

Thứ tự đọc gợi ý: mục 1 → 2 → 3 (phần đồ thị), rồi 6 → 7 (phần đánh giá). Các mục còn lại dùng khi bị hỏi sâu.

---

## 1. Đồ thị: các khái niệm dùng trong bài

| Khái niệm | Định nghĩa | Trong bài |
|---|---|---|
| Nút (node, vertex) | Một thực thể | Một CLB; tổng 46 CLB từng đá Premier League từ 2000/01 |
| Cạnh (edge) | Quan hệ giữa hai nút | Một trận, hoặc tổng hợp các trận giữa hai CLB |
| Đồ thị vô hướng | Cạnh không có chiều: (u, v) = (v, u) | Đồ thị **số lần gặp**: trọng số = số trận giữa hai CLB |
| Đồ thị có hướng | Cạnh có chiều u → v | Đồ thị **ưu thế**: bên thua "bầu" cho bên thắng |
| Trọng số | Số gắn với cạnh | Số trận (vô hướng); phần điểm × trọng số thời gian (có hướng) |
| Bậc (degree) | Số cạnh nối vào một nút | Số đối thủ khác nhau đã gặp |
| Độ mạnh (strength) | Tổng trọng số các cạnh của nút | Tổng số trận đã đá |
| Ma trận kề | A[i, j] = trọng số cạnh i–j (hoặc i → j) | `V` (ưu thế), `W` (số trận có trọng số thời gian) trong `build_graph_features.py` |

**Mật độ** của đồ thị vô hướng đơn có n nút và m cạnh:

```latex
\text{density} = \frac{m}{\binom{n}{2}} = \frac{2m}{n(n-1)}
```

Trong bài: n = 46, m = 800, nên mật độ = 800 / 1.035 = 0,773. Mật độ cao là hệ quả trực tiếp của thể thức vòng tròn: trong một mùa, 20 đội gặp nhau đủ 190 cặp. 235 cặp còn lại chưa gặp lần nào: 226 cặp chưa từng cùng đá một mùa (ví dụ Bradford chỉ đá 2000/01, Luton chỉ đá 2023/24), và 9 cặp cùng ở mùa 2026/27 nhưng chưa đến lượt gặp (dữ liệu dừng ở 12/10/2026).

**Hệ quả quan trọng:** khi gần như mọi cặp đều nối với nhau, các chỉ số dựa trên **cấu trúc** (bậc, khoảng cách, cộng đồng) phân biệt các đội rất kém. Thông tin hữu ích nằm ở **trọng số và hướng** của cạnh, tức kết quả trận. Đây là lý do bài tập trung vào PageRank trên đồ thị ưu thế.

---

## 2. PageRank

### 2.1. Ý tưởng gốc

PageRank (Brin và Page, 1998) xếp hạng trang web theo nguyên tắc: một trang quan trọng nếu được nhiều trang quan trọng trỏ tới. Định nghĩa mang tính đệ quy, và được giải bằng mô hình **người lướt web ngẫu nhiên** (random surfer):

- Ở mỗi bước, với xác suất α (hệ số giảm chấn, thường 0,85), người lướt đi theo một liên kết ngẫu nhiên của trang hiện tại, chọn theo trọng số.
- Với xác suất 1 − α, người lướt "nhảy" (teleport) tới một trang bất kỳ.
- PageRank của một trang là tỷ lệ thời gian người lướt ở trang đó về lâu dài.

### 2.2. Áp dụng cho bóng đá

| Web | Bóng đá |
|---|---|
| Trang web | CLB |
| Trang A trỏ tới trang B | A thua (hoặc hòa) B, nên A "bầu" cho B |
| Được trang quan trọng trỏ tới | Thắng được đội mạnh |

Người lướt ngẫu nhiên đi theo các cạnh "tôi đã thua đội này", nên sẽ dồn về các đội ít khi thua, nhất là ít thua đội mạnh. Thắng một đội mạnh có giá trị hơn thắng một đội yếu, vì phiếu bầu từ đội mạnh mang nhiều "trọng lượng" hơn. Đây là khác biệt cốt lõi so với bảng điểm, nơi mọi trận thắng đều được 3 điểm.

Ý tưởng xếp hạng đội thể thao bằng vectơ riêng của ma trận kết quả đã có từ trước: Keener (1993, *SIAM Review*) dùng định lý Perron–Frobenius để xếp hạng các đội bóng bầu dục Mỹ. PageRank trong bài là một biến thể của họ phương pháp này.

### 2.3. Công thức

Gọi V là ma trận "bầu" (V[i, j] = tổng phiếu i bầu cho j), n là số đội. Ma trận chuyển P chuẩn hóa từng hàng của V thành xác suất:

```latex
P_{ij} = \frac{V_{ij}}{\sum_k V_{ik}}
```

Nếu một hàng toàn số 0 (đội chưa thua hay hòa ai trong cửa sổ, gọi là **nút kết** – dangling node) thì hàng đó được thay bằng phân bố đều 1/n. Vectơ PageRank r (một vectơ hàng, tổng bằng 1) thỏa:

```latex
r = \alpha \, r P + \frac{1-\alpha}{n} \mathbf{1}
```

Trong bài, kết quả được nhân với n để **trung bình bằng 1**: PageRank 1,2 nghĩa là mạnh hơn mức trung bình 20%.

### 2.4. Vì sao phép lặp hội tụ và nghiệm duy nhất

- Ma trận Google `G = αP + (1 − α)/n · 11ᵀ` có mọi phần tử dương (nhờ phần teleport) và là ma trận ngẫu nhiên theo hàng (nhờ xử lý nút kết).
- Theo định lý Perron–Frobenius, ma trận dương có trị riêng lớn nhất bằng 1, đơn bội, ứng với một vectơ riêng dương duy nhất. Đó chính là PageRank.
- Phép lặp lũy thừa `r ← rG` hội tụ với tốc độ cỡ α^k. Với α = 0,85 và ngưỡng dừng 10⁻¹⁰ (tổng sai lệch tuyệt đối), cần khoảng 140 vòng; mã đặt tối đa 200 vòng.

**Nếu bỏ teleport (α = 1):** đồ thị có thể không liên thông mạnh (ví dụ một đội chỉ thắng, không thua ai), khi đó toàn bộ xác suất bị "hút" vào vài nút và nghiệm không duy nhất.

### 2.5. Các lựa chọn và lý do

| Lựa chọn | Lý do |
|---|---|
| α = 0,85 | Giá trị chuẩn trong tài liệu gốc và bài giảng. Không dò trên tập kiểm thử, để tránh làm đẹp kết quả. |
| Phần điểm s thay vì thắng/hòa/thua | Giữ thông tin mức độ thắng; hòa = hai đội bầu cho nhau như nhau. |
| Chặn hiệu số ở 3 bàn | Một trận 7-0 không chi phối cả mạng. |
| Tự cài bằng numpy thay vì `networkx.pagerank` | Phải dựng lại đồ thị cho khoảng 2.740 ngày thi đấu; ma trận numpy chạy toàn bộ trong vài giây. Đã đối chiếu với networkx: sai lệch tối đa 3,5·10⁻¹¹ trên dữ liệu thật. |

### 2.6. Các chỉ số trung tâm khác và vì sao không dùng

| Chỉ số | Đo gì | Vì sao không dùng trong bài |
|---|---|---|
| Degree centrality | Số đối thủ đã gặp | Phản ánh số mùa trụ hạng, không phải sức mạnh |
| Closeness | Khoảng cách trung bình tới các nút khác | Mạng gần đầy đủ, khoảng cách gần như bằng 1 với mọi cặp |
| Betweenness | Số đường đi ngắn nhất đi qua nút | Như trên: gần như không có "cầu nối" |
| HITS (hub, authority) | Hai vai trò trỏ đi / được trỏ tới | Authority trên đồ thị ưu thế gần như trùng PageRank; không có teleport nên kém ổn định hơn |
| Eigenvector centrality | Như PageRank nhưng không có teleport | Không bảo đảm duy nhất khi đồ thị không liên thông mạnh |

---

## 3. Phát hiện cộng đồng: modularity và Louvain

### 3.1. Modularity

Modularity (Newman và Girvan, 2004) đo mức cạnh **bên trong các nhóm** nhiều hơn mức kỳ vọng nếu cạnh được nối ngẫu nhiên nhưng giữ nguyên bậc của từng nút:

```latex
Q = \frac{1}{2m} \sum_{i,j} \left( A_{ij} - \frac{k_i k_j}{2m} \right) \delta(c_i, c_j)
```

- A_ij: trọng số cạnh i–j; k_i: độ mạnh của nút i; m: tổng trọng số; δ(c_i, c_j) = 1 nếu i và j cùng nhóm.
- Q nằm trong khoảng [−0,5; 1]. Thực nghiệm thường coi **Q từ khoảng 0,3 trở lên** là có cấu trúc nhóm rõ.

**Trong bài: Q = 0,04.** Gần như không có cụm thật. Ba nhóm Louvain tìm được chủ yếu phản ánh **thời gian trụ hạng** (trung bình 14, 9 và 2 mùa ở Premier League): các đội đá nhiều mùa gặp nhau nhiều hơn chỉ vì cùng có mặt lâu, không phải vì tạo thành "cụm đối thủ".

### 3.2. Thuật toán Louvain

Louvain (Blondel và cộng sự, 2008) tối đa hóa Q theo hai pha lặp lại:

1. **Di chuyển cục bộ:** lần lượt thử chuyển từng nút sang nhóm của hàng xóm; giữ lại bước chuyển làm Q tăng nhiều nhất.
2. **Gộp:** mỗi nhóm thành một siêu nút, rồi lặp lại pha 1 trên đồ thị mới.

Thuật toán dừng khi Q không tăng thêm. Kết quả phụ thuộc thứ tự duyệt, nên mã đặt `seed=7` để tái lập được. Tham số `resolution = 1` là định nghĩa chuẩn của modularity.

---

## 4. Tương quan hạng Spearman

Spearman là tương quan Pearson giữa **thứ hạng** của hai biến. Khi không có hạng bằng nhau:

```latex
\rho = 1 - \frac{6 \sum d_i^2}{n(n^2 - 1)}
```

với d_i là chênh lệch hạng của đội i. ρ = 1 khi hai cách xếp trùng hoàn toàn.

**Vì sao dùng Spearman mà không dùng Pearson:** câu hỏi là "PageRank có xếp các đội theo cùng **thứ tự** với bảng điểm không", không phải "có quan hệ tuyến tính không". Điểm số được phá hòa bằng hiệu số (`pts + gd/1000`), giống luật xếp hạng của giải.

**Trong bài:** trung bình 0,937 trên 24 mùa đủ 380 trận, thấp nhất 0,806 (2002/03). Đây chỉ là **kiểm tra tính hợp lý**: PageRank và điểm đều tính từ cùng các kết quả, nên tương quan cao là điều mong đợi, không phải bằng chứng độc lập. Thông tin đáng giá nằm ở các mùa lệch (2002/03: Leeds và Aston Villa giành nhiều điểm trước 6 đội đầu bảng hơn các đội cùng nhóm điểm, nên PageRank xếp cao hơn hẳn bảng điểm; 2015/16: Tottenham đứng đầu PageRank dù Leicester vô địch, vì PageRank tính cả cách biệt tỷ số và Tottenham thắng cách biệt từ 3 bàn 9 trận so với 4 của Leicester).

---

## 5. Thời gian: cửa sổ trượt, nửa đời, co về trung tính

### 5.1. Trọng số theo nửa đời

```latex
w = 0{,}5^{\,\Delta t / T_{1/2}}
```

Δt là số ngày từ trận cũ tới ngày dự đoán; T½ là nửa đời. Với T½ = 365 ngày: trận cách 1 năm có trọng số 0,5; cách 2 năm 0,25; cách 3 năm 0,125 (sau đó bị cắt bởi cửa sổ 3 năm). Đây là cách làm phổ biến khi sức mạnh thay đổi theo thời gian (chuyển nhượng, đổi HLV, lên xuống hạng).

### 5.2. Co về trung tính (shrinkage)

Đối đầu trực tiếp rất thưa: mỗi mùa tối đa 2 trận giữa hai đội. Nếu hai đội mới gặp 1 lần và đội nhà thắng 3-0, tỷ lệ thô là 100%, một kết luận cực đoan từ 1 trận. Bài cộng thêm **1 trận ảo có kết quả hòa**:

```latex
\text{h2h\_share} = \frac{\sum w_k s_k + 0{,}5 \cdot 1}{\sum w_k + 1} - 0{,}5
```

Với ví dụ trên: (1 · 1 + 0,5) / (1 + 1) − 0,5 = 0,25 thay vì 0,5. Khi số trận tăng, ảnh hưởng của trận ảo nhỏ dần. Đây chính là ước lượng Bayes với tiên nghiệm Beta đối xứng (thêm "giả quan sát"), cùng ý tưởng với làm trơn Laplace.

---

## 6. Rò rỉ dữ liệu (data leakage)

**Định nghĩa.** Rò rỉ xảy ra khi đặc trưng dùng để dự đoán chứa thông tin không có được tại thời điểm dự đoán. Mô hình khi đó trông rất tốt khi đánh giá nhưng thất bại khi dùng thật.

**Các dạng thường gặp với dữ liệu trận đấu:**

| Dạng | Ví dụ | Cách bài xử lý |
|---|---|---|
| Dùng kết quả của chính trận đó | Đưa tỷ số vào đặc trưng | Đặc trưng ngày D chỉ dùng trận có ngày **< D** |
| Dùng trận cùng ngày | Hai trận cùng thứ Bảy | Điều kiện "<" (không phải "≤") loại luôn trận cùng ngày |
| Thống kê tính trên toàn bộ dữ liệu | PageRank cả 26 mùa đưa vào mô hình | Phân tích toàn thời gian chỉ để mô tả, không vào mô hình |
| Chia tập ngẫu nhiên | k-fold xáo trộn | Chia theo thời gian (rolling-origin) |
| Tiền xử lý học trên cả tập kiểm thử | Phân vị cắt tính trên toàn bộ dữ liệu | `ClipPercentile` chỉ học phân vị từ tập huấn luyện |

**Kiểm chứng.** Hai phép thử độc lập: (1) xóa mọi trận từ D trở đi rồi tính lại; (2) đảo ngẫu nhiên tỷ số mọi trận từ D trở đi. Cả hai đều cho đặc trưng ngày D không đổi (sai lệch 0). Đây là bằng chứng kiểm chứng được, thay cho lời cam đoan.

---

## 7. Đánh giá mô hình

### 7.1. Log loss (cross-entropy)

Với 3 lớp (H, D, A) và xác suất dự đoán p:

```latex
\text{log loss} = -\frac{1}{N} \sum_{i=1}^{N} \ln p_{i, y_i}
```

- Chỉ phụ thuộc xác suất gán cho **kết quả thật**. Tự tin sai (gán 5% cho kết quả xảy ra) bị phạt rất nặng: −ln 0,05 ≈ 3.
- Là quy tắc chấm điểm **đúng đắn** (proper scoring rule): kỳ vọng tốt nhất khi dự đoán đúng xác suất thật, nên khuyến khích xác suất trung thực.
- **Mốc tham chiếu:** đoán theo tần suất nhãn (H 45%, D 24%, A 31% từ 2010/11) cho log loss ≈ 1,06, bằng entropy của phân bố nhãn. Elo đạt 0,98–0,99; kèo nhà cái 0,966–0,976. Khoảng cách giữa các mô hình tốt thường chỉ vài phần nghìn, nên cần kiểm định thống kê.

### 7.2. Brier score (đa lớp)

```latex
\text{Brier} = \frac{1}{N} \sum_{i} \sum_{c \in \{H,D,A\}} (p_{i,c} - o_{i,c})^2
```

o là mã hóa one-hot của kết quả thật. Cũng là quy tắc đúng đắn, nhưng phạt nhẹ hơn log loss với dự đoán tự tin sai. Dùng để kiểm tra kết luận không phụ thuộc vào việc chọn log loss.

### 7.3. Accuracy và vì sao không dùng làm chỉ số chính

Accuracy chỉ xét lớp có xác suất cao nhất. Hòa hiếm khi là lớp cao nhất (tỷ lệ 24%), nên mô hình gần như không bao giờ dự đoán hòa, và accuracy của các mô hình khác nhau chỉ quanh 0,52–0,54. Hai mô hình có cùng accuracy có thể có chất lượng xác suất rất khác nhau, mà xác suất mới là thứ dashboard hiển thị.

### 7.4. Rolling-origin (đánh giá theo nguồn gốc trượt)

```
Mùa kiểm thử 2010/11: huấn luyện 2001/02 – 2009/10
Mùa kiểm thử 2011/12: huấn luyện 2001/02 – 2010/11
...
Mùa kiểm thử 2026/27: huấn luyện 2001/02 – 2025/26
```

Tổng 17 mùa kiểm thử, 6.140 trận. Mỗi dự đoán chỉ dùng mô hình học từ quá khứ, đúng như khi dùng thật. Mùa 2000/01 bị bỏ khỏi huấn luyện vì đặc trưng lịch sử (phong độ, đồ thị) chưa đủ dữ liệu.

Bài cũng báo cáo **split của nhóm** (huấn luyện đến 2023/24, kiểm thử 2024/25 trở đi, 820 trận) để so được với các khâu khác. Kết quả trên split này dao động hơn vì ít trận.

### 7.5. Bootstrap theo cặp

Câu hỏi: chênh lệch log loss 0,0011 giữa hai cấu hình là thật hay do may rủi?

1. Với mỗi trận i, tính d_i = log loss(cấu hình B) − log loss(cấu hình A). Cả hai cấu hình dự đoán **cùng các trận**.
2. Lấy mẫu có hoàn lại N trận từ {d_i}, tính trung bình; lặp 2.000 lần.
3. Phân vị 2,5% và 97,5% của 2.000 trung bình là khoảng tin cậy 95%.

**"Theo cặp" quan trọng vì:** độ khó của trận (trận cân bằng hay chênh lệch) ảnh hưởng mạnh tới log loss của cả hai cấu hình. Lấy hiệu theo từng trận khử được nguồn biến động này, nên khoảng tin cậy hẹp hơn nhiều so với so hai trung bình độc lập.

**Đọc kết quả:**
- Khoảng nằm hẳn dưới 0: B tốt hơn A có ý nghĩa.
- Khoảng chứa 0: không phân biệt được.
- Khoảng nằm hẳn trên 0: B kém hơn A có ý nghĩa.

Mỗi so sánh dùng bộ sinh số ngẫu nhiên riêng với cùng hạt giống (`default_rng(0)`), nên kết quả không phụ thuộc thứ tự chạy.

**Hạn chế cần biết:** các trận trong cùng mùa không hoàn toàn độc lập; bootstrap từng trận có thể cho khoảng hơi hẹp. Bài bổ sung chỉ số "số mùa tốt hơn" (ví dụ 6/17) như một kiểm tra theo mùa.

---

## 8. Hai mô hình

### 8.1. Gradient Boosting (`HistGradientBoostingClassifier`)

- Cộng dồn nhiều cây quyết định nông; mỗi cây sửa sai số của các cây trước theo hướng gradient của log loss.
- "Hist": chia giá trị liên tục vào tối đa 255 ngăn, nhanh với dữ liệu lớn; xử lý giá trị thiếu (NaN) trực tiếp.
- Bất biến với phép biến đổi đơn điệu của đặc trưng, nên **không nhạy với ngoại lai và thang đo**.
- Tham số trong bài (độ sâu 3, tốc độ học 0,04, 150 vòng, tối thiểu 60 mẫu mỗi lá, phạt L2 = 5) được chọn bảo thủ để tránh quá khớp với khoảng 6.000–9.000 trận huấn luyện; không dò trên tập kiểm thử.

### 8.2. Logistic Regression đa lớp

- Mô hình tuyến tính: log tỷ số xác suất giữa các lớp là hàm tuyến tính của đặc trưng; xác suất qua hàm softmax.
- Hệ số C = 0,3 là nghịch đảo độ mạnh của phạt L2: C nhỏ thì phạt mạnh, hệ số nhỏ.
- **Nhạy với thang đo và ngoại lai:** một giá trị lệch 70 độ lệch chuẩn (như `rest_days`) làm hệ số và xác suất cực đoan, dẫn tới log loss rất xấu.

### 8.3. Cắt phân vị (winsorization)

Thay mọi giá trị dưới phân vị 1% bằng phân vị 1%, trên phân vị 99% bằng phân vị 99%. Phân vị **chỉ học từ tập huấn luyện** để không rò rỉ. Sau đó mới chuẩn hóa (`StandardScaler`).

Trong bài: Logistic Regression trên 85 đặc trưng từ log loss 1,156 xuống 0,989 (rolling 6.140 trận). Các giả thuyết khác đã thử và loại: bỏ `rest_days`, bỏ 14 cột `diff_*` trùng đại số, bỏ cả hai. `QuantileTransformer` cũng sửa được nhưng kém hơn cắt phân vị.

---

## 9. Vì sao đặc trưng trùng thông tin không giúp mô hình

- Khi đặc trưng mới X tương quan cao với đặc trưng sẵn có E (ở đây Elo), phần thông tin **mới** của X là phần dư sau khi đã biết E. Tương quan 0,94 nghĩa là E giải thích khoảng 88% phương sai của X (0,94² ≈ 0,88).
- Phần còn lại phải vừa có liên quan tới kết quả, vừa đủ lớn để vượt qua nhiễu ước lượng của mô hình. Với khoảng 6.000 trận và kết quả bóng đá vốn nhiều ngẫu nhiên, lợi ích nhỏ dễ bị chìm, thậm chí âm (thêm biến làm tăng phương sai ước lượng).
- Điều này giải thích cả kết quả "chỉ đồ thị ≈ chỉ Elo" (đồ thị nắm được sức mạnh) lẫn "85 đặc trưng + đồ thị ≈ 85 đặc trưng" (không có gì mới).

**Liên hệ Elo và PageRank.** Elo cập nhật sức mạnh sau mỗi trận theo chênh lệch giữa kết quả thật và kết quả kỳ vọng (dựa trên sức mạnh đối thủ). Như vậy Elo cũng "thưởng nhiều hơn khi thắng đội mạnh", giống tinh thần PageRank. Hai phương pháp là hai cách khác nhau để lan truyền sức mạnh qua cùng một mạng kết quả.

---

## 10. Tài liệu tham khảo chính

- Brin, S., Page, L. (1998). *The anatomy of a large-scale hypertextual Web search engine*. Computer Networks and ISDN Systems.
- Keener, J. P. (1993). *The Perron–Frobenius theorem and the ranking of football teams*. SIAM Review, 35(1).
- Newman, M. E. J., Girvan, M. (2004). *Finding and evaluating community structure in networks*. Physical Review E, 69.
- Blondel, V. D., Guillaume, J.-L., Lambiotte, R., Lefebvre, E. (2008). *Fast unfolding of communities in large networks*. Journal of Statistical Mechanics.
- Gneiting, T., Raftery, A. E. (2007). *Strictly proper scoring rules, prediction, and estimation*. Journal of the American Statistical Association.
- Efron, B., Tibshirani, R. (1993). *An Introduction to the Bootstrap*. Chapman & Hall.

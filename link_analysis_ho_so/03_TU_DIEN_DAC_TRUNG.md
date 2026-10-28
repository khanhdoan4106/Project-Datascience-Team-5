# Từ điển đặc trưng đồ thị (`results/graph_features_matches.csv`)

Bản dạng bảng theo đúng khuôn `feature_candidates.csv` của khâu EDA (13 cột: định nghĩa, nguồn, thời điểm có, tỷ lệ thiếu, tương quan Spearman với kết quả, quyết định) nằm ở `results/feature_candidates_link_analysis.csv`, có thể ghép thẳng với danh mục 87 đặc trưng của nhóm.

Mỗi dòng ứng với một trận trong `matches.csv` và được ghép bằng `match_id`. Mọi giá trị chỉ tính từ các trận có ngày **trước** ngày diễn ra trận đó. Quy ước dấu: giá trị dương nghĩa là đội nhà có lợi.

| Cột | Ý nghĩa | Cách tính | Miền giá trị thực tế | Thiếu |
|---|---|---|---|---|
| `match_id` | Khóa trận, trùng với `matches.csv` và `features.csv` | – | – | 0 |
| `season`, `date`, `home_team`, `away_team` | Thông tin tham chiếu | sao chép từ `matches.csv` | – | 0 |
| `gr_pagerank_home` | Sức mạnh mạng lưới của đội nhà | PageRank (d = 0,85) trên đồ thị ưu thế 3 năm gần nhất, nửa đời 365 ngày; trung bình các đội có trong cửa sổ = 1 | 0,15 – 2,83 | 0,3% |
| `gr_pagerank_away` | Như trên, cho đội khách | – | 0,15 – 2,56 | 0,4% |
| `gr_pagerank_log_ratio` | Chênh lệch sức mạnh mạng lưới | ln(PR nhà / PR khách) | −2,41 – 2,40 | 0,6% |
| `gr_common_opp_diff` | Kết quả gián tiếp qua đối thủ chung | trung bình có trọng số của (phần điểm của đội nhà − phần điểm của đội khách) trước cùng một đối thủ | −0,67 – 0,70 | 1,1% |
| `gr_common_opp_n` | Số đối thủ chung dùng để tính cột trên | đếm | 0 – 27 | 0 |
| `gr_trans2_diff` | Ưu thế bắc cầu 2 bước | Σ ưu thế(nhà→C)·ưu thế(C→khách) − chiều ngược lại | −1,08 – 1,25 | 0 |
| `gr_h2h_share` | Đối đầu trực tiếp theo phần điểm | trung bình phần điểm của đội nhà trong các lần gặp 10 năm gần nhất (nửa đời 3 năm), co về 0,5 bằng 1 trận ảo, trừ 0,5 | −0,36 – 0,34 | 0 |
| `gr_h2h_gd` | Đối đầu trực tiếp theo hiệu số | trung bình hiệu số có trọng số, co về 0 | −2,92 – 2,92 | 0 |
| `gr_h2h_weight` | Tổng trọng số các lần gặp (độ tin cậy của hai cột trên) | Σ trọng số thời gian | 0 – 7,88 | 0 |

**Ghi chú**
- Giá trị thiếu (NaN) xuất hiện khi một trong hai đội chưa đá trận nào trong cửa sổ 3 năm, ví dụ đội mới lên hạng sau thời gian dài vắng mặt, hoặc khi hai đội chưa có đối thủ chung. Mô hình cây xử lý được NaN trực tiếp; với mô hình tuyến tính, nên điền trung vị.
- PageRank trung bình trong file khoảng 1,17 chứ không phải 1. Lý do là chuẩn hóa tính trên mọi đội có trong cửa sổ 3 năm, gồm cả các đội đã xuống hạng và thường yếu hơn.
- Các cột `gr_pagerank_home`, `gr_pagerank_away`, `gr_common_opp_n` và `gr_h2h_weight` dùng để tham chiếu. Phần đánh giá chỉ dùng 5 cột: `gr_pagerank_log_ratio`, `gr_common_opp_diff`, `gr_trans2_diff`, `gr_h2h_share` và `gr_h2h_gd`.
- Tương quan với `elo_diff`: đối thủ chung 0,94, bắc cầu 0,86, đối đầu 0,69, PageRank 0,65. `gr_h2h_share` tương quan 0,85 với `h2h_home_points` trong `features.csv`.

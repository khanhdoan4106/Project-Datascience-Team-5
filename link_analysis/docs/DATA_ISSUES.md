# Vấn đề dữ liệu phát hiện trong quá trình làm Link Analysis

Kiểm tra trên `matches.csv` và `features.csv` (9.850 trận, bản ngày 13/10/2026, trùng với bản Người 2 gửi lại ngày 18/10/2026).

## Đã ổn
- Không có `match_id` trùng, không có trận trùng theo (mùa, đội nhà, đội khách), không có trận nào đội nhà trùng đội khách.
- Không thiếu ngày, tên đội hay tỷ số. Có 46 CLB, tên đã chuẩn hóa thống nhất.
- `mismatches.csv` rỗng: các nguồn không lệch nhau.

## Cần xử lý

| # | Vấn đề | Bằng chứng | Ảnh hưởng | Đề nghị | Người |
|---|---|---|---|---|---|
| 1 | `home_rest_days` và `away_rest_days` có giá trị phi lý | 252 và 245 dòng trên 60 ngày, tối đa 8.134 và 9.225 ngày. Trận đầu mùa bị tính khoảng nghỉ hè (~100 ngày); đội mới lên hạng bị tính từ lần cuối đá ở giải (Derby 2007/08: 1.918 ngày) | Hai cột lệch tới 70 độ lệch chuẩn; là một trong các biến đuôi nặng làm Logistic Regression kém (xem ghi chú cuối) | Chặn trên (ví dụ 14 ngày) hoặc để trống kèm cột đánh dấu `is_season_opener` | Người 2 |
| 2 | Mùa 2003/04 và 2004/05 thiếu 45 trận mỗi mùa (335/380) | Cả 20 đội mỗi mùa đều chỉ có 32–35 trận | Thống kê theo mùa và PageRank hai mùa này kém chính xác (đã loại khỏi hệ số Spearman) | Bổ sung từ nguồn khác (Transfermarkt, FBref, openfootball) | Người 1 |
| 3 | `gameweek` trống 99%, `kickoff_time` trống 72% | – | Không ảnh hưởng Link Analysis; ảnh hưởng nếu mô hình cần vòng đấu hay giờ đá | Bổ sung nếu Người 7 cần | Người 1, 2 |
| 4 | Chưa có lịch trận sắp đá mùa 2026/27 | `status` toàn là `played` | Chưa dự đoán được trận tương lai | Khi có lịch, chạy lại `build_graph_features.py` để có đặc trưng cho các trận đó | Người 2, 9 |

## Ghi chú cho Người 7 (mô hình)
Logistic Regression dùng `StandardScaler` trên toàn bộ 85 đặc trưng cho log loss 1,156, tệ hơn chỉ dùng `elo_diff` (0,981). Bỏ riêng `rest_days` không sửa được. Đổi sang `QuantileTransformer(output_distribution="normal")` đưa log loss về 1,020. Nguyên nhân là nhiều biến có phân phối đuôi nặng, không chỉ riêng `rest_days`. Xem `evaluate_logreg_robust.py`.

# Vấn đề dữ liệu liên quan đến Link Analysis

Kiểm tra chất lượng chung của `matches.csv` và `features.csv` đã do khâu EDA thực hiện. Xem nhánh `EDA`, thư mục `reports/eda_matches_features/`:
- `data_quality_checks.csv`: 243 kiểm tra đạt, 7 cảnh báo (khóa trận, trùng trận, tỷ số khớp nhãn, đối chiếu hai bảng…).
- `data_issues.csv`: 1.158 dòng cần lưu ý.

Link Analysis dùng đúng bản dữ liệu đó: SHA-256 của hai file trùng với `analysis_metadata.json` của EDA. Tài liệu này chỉ ghi những điểm ảnh hưởng trực tiếp đến Link Analysis.

## Vấn đề đã có trong báo cáo EDA, ảnh hưởng tới Link Analysis

| Vấn đề | Trong báo cáo EDA | Ảnh hưởng tới Link Analysis | Xử lý trong Link Analysis |
|---|---|---|---|
| Mùa 2003/04 và 2004/05 chỉ có 335/380 trận | Mục 2, bảng phạm vi theo mùa | PageRank hai mùa này dựng trên đồ thị thiếu cạnh | Loại khỏi hệ số Spearman; vẫn giữ trong đặc trưng `gr_*` vì cửa sổ trượt 3 năm |
| `home_rest_days`, `away_rest_days` đo khoảng cách tới trận EPL trước, không phải thời gian nghỉ (534 dòng `observed_epl_gap`) | `data_issues.csv`, giả thuyết H7 | Là một trong các biến đuôi nặng làm Logistic Regression kém (xem dưới) | Không dùng làm đặc trưng riêng |
| Xác suất từ kèo chưa có thời điểm thu thập | Mục 8, giả thuyết H9 | Không ảnh hưởng kết luận | Đánh giá cả kịch bản có và không có kèo |
| Mùa 2026/27 đang diễn ra; chưa có trận sắp đá trong dữ liệu (trận cuối 12/10/2026) | Mục 2 | Chưa có đặc trưng cho trận tương lai | Khi khâu Tích hợp dữ liệu xuất bản `clean/` mới, chạy lại `run_all.sh` |

## Phát hiện riêng của Link Analysis (đề nghị khâu Xây dựng mô hình lưu ý)

Logistic Regression dùng `StandardScaler` trên toàn bộ 85 đặc trưng cho log loss 1,156, tệ hơn chỉ dùng `elo_diff` (0,981).

- Bỏ riêng `rest_days` không sửa được.
- Bỏ các cột trùng đại số mà EDA nêu (14 cột `diff_*`, `elo_home_win_prob`) cũng không sửa được.
- Cắt mỗi cột về phân vị 1–99% học từ tập huấn luyện, rồi mới chuẩn hóa, đưa log loss về 0,989 (rolling 6.140 trận). Dùng `QuantileTransformer` cho kết quả kém hơn.

Nguyên nhân là giá trị ngoại lai đuôi nặng ở nhiều biến, ví dụ các biến trung bình mỗi trận ở đầu mùa vốn tính từ rất ít trận. Với mô hình tuyến tính, nên cắt phân vị trước khi chuẩn hóa. Mã: `link_analysis/src/evaluate.py` (lớp `ClipPercentile`); chẩn đoán đầy đủ: `scripts_bo_sung/chan_doan_logreg.py`.

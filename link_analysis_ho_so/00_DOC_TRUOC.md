# Hồ sơ cá nhân – Link Analysis

Bộ tài liệu riêng để ôn và trả lời giảng viên, **không push lên repo nhóm**. Gói nộp cho nhóm là thư mục `link_analysis/` (README theo luồng, notebook chạy từng bước, 4 script trong `src/`, kiểm thử, kết quả, 5 hình).

## Nội dung

| File | Nội dung | Dùng khi |
|---|---|---|
| `01_PHUONG_PHAP.md` | Từng bước: làm gì, vì sao, mã; toàn bộ số liệu đánh giá; chẩn đoán Logistic Regression; kiểm định H4 | Viết báo cáo cuối, ôn chi tiết |
| `02_VAN_DE_DU_LIEU.md` | Vấn đề dữ liệu, đối chiếu với báo cáo EDA | Trao đổi với khâu Thu thập, Tích hợp dữ liệu |
| `03_TU_DIEN_DAC_TRUNG.md` | Ý nghĩa, cách tính, miền giá trị 9 cột `gr_*` | Câu hỏi về từng đặc trưng |
| `04_CHUAN_BI_VAN_DAP.md` | Kịch bản trình bày 3 phút; câu hỏi – trả lời theo 10 chủ đề, gồm câu hỏi "bẫy" | Trước buổi vấn đáp |
| `05_KIEN_THUC_NEN.md` | Lý thuyết: đồ thị, PageRank (Perron–Frobenius, hội tụ), modularity và Louvain, Spearman, nửa đời và co về trung tính, rò rỉ, log loss, Brier, rolling-origin, bootstrap theo cặp, hai mô hình, cắt phân vị | Khi bị hỏi sâu "vì sao" ở mức nguyên lý |
| `06_DOC_HINH.md` | Cách đọc từng hình, điểm chính, câu hỏi có thể gặp | Làm slide, trình bày hình |
| `hinh/` | Bản sao 5 hình | Chèn slide, báo cáo |
| `scripts_bo_sung/chan_doan_logreg.py` | Chẩn đoán vì sao Logistic Regression kém | Câu hỏi về Logistic Regression |
| `scripts_bo_sung/ve_lai_hinh.py` | Vẽ lại 5 hình chỉ từ CSV kết quả (sau khi sửa `src/figures.py`) | Chỉnh hình cho slide |
| `ket_qua_bo_sung/` | Kết quả gốc của chẩn đoán, và bản đánh giá cũ dùng StandardScaler | Đối chiếu số liệu |

## Lộ trình ôn (khoảng 2 giờ)

1. Mở `link_analysis_tung_buoc.ipynb` và đọc lướt từ đầu đến cuối: nắm luồng (15 phút).
2. `04_CHUAN_BI_VAN_DAP.md`, mục 1: tập nói bài trình bày 3 phút thành tiếng (15 phút).
3. `05_KIEN_THUC_NEN.md`, mục 1, 2, 3, 7: lý thuyết hay bị hỏi nhất (40 phút).
4. `06_DOC_HINH.md`: tập giải thích từng hình trong 30 giây (15 phút).
5. `04_CHUAN_BI_VAN_DAP.md`, mục 2–10: tự trả lời trước rồi mới đọc đáp án (30 phút).

## Các con số cần nhớ

| Nội dung | Giá trị |
|---|---|
| Dữ liệu | 9.850 trận, 2000/01 – 12/10/2026, 46 CLB |
| Mạng lưới | 800 trên 1.035 cặp đã gặp, mật độ 0,77; Louvain 3 nhóm, modularity 0,04 |
| Cặp chưa gặp | 235 = 226 cặp chưa từng cùng đá một mùa + 9 cặp cùng ở 2026/27 nhưng chưa đến lượt (dữ liệu đến 12/10/2026). Trên hình, mọi cặp đã gặp đều có đường nối |
| Nhóm C (Louvain) | Bradford, Coventry, Ipswich: 1, 2, 4 mùa ở Premier League, cùng đá 2000/01 |
| Ví dụ 2015/16 | Tottenham đứng đầu PageRank dù Leicester vô địch: PageRank tính cách biệt tỷ số, Tottenham thắng cách biệt từ 3 bàn 9 trận (Leicester 4); xét điểm thuần trước 8 đội đầu bảng, Leicester vẫn hơn (21 so với 20) |
| PageRank so với bảng xếp hạng | Spearman trung bình 0,937, thấp nhất 0,806 (2002/03); đội vô địch đứng đầu 19/24 mùa, luôn trong top 3 |
| Tham số đồ thị | α = 0,85; cửa sổ 3 năm, nửa đời 365 ngày; đối đầu 10 năm, nửa đời 3 năm, co về trung tính 1 trận ảo; chặn hiệu số 3 bàn |
| Kiểm tra cài đặt | Khớp networkx, sai lệch tối đa 3,5·10⁻¹¹; 6 kiểm thử tự động; 2 phép thử rò rỉ đều đạt |
| Đánh giá | Rolling 2010/11 trở đi, 17 mùa, 6.140 trận; bootstrap theo cặp 2.000 lần |
| Kết quả chính (Gradient Boosting) | 85 đặc trưng 0,9835 → thêm đồ thị 0,9845; chênh lệch +0,0011, KTC [−0,0009; +0,0029] |
| Kết quả chính (Logistic Regression) | 0,9885 → 0,9894; +0,0009, KTC [+0,0002; +0,0016] |
| Mốc so sánh (Gradient Boosting) | Chỉ Elo 0,9887; chỉ đồ thị 0,9914; chỉ kèo 0,9755; đoán theo tần suất ≈ 1,06 |
| Vì sao | Tương quan với `elo_diff`: đối thủ chung 0,94, bắc cầu 0,86, đối đầu 0,69, PageRank 0,65 |
| H4 (EDA) | Không được ủng hộ: mọi KTC chứa 0 |
| Logistic Regression | StandardScaler 1,156 → cắt phân vị 1–99% 0,989 |

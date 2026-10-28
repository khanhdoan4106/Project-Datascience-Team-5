# Chuẩn bị vấn đáp – Link Analysis

Mọi số liệu dưới đây lấy từ `link_analysis/results/` (dữ liệu 9.850 trận, 2000/01 – 12/10/2026).

## 1. Trình bày trong 3 phút

1. **Bài toán.** Xem mỗi CLB là một nút, mỗi trận là một cạnh. Câu hỏi đặt ra: vị trí của một đội trong mạng đối đầu có giúp dự đoán trận tiếp theo không?
2. **Dựng đồ thị.** Mỗi trận cho đội nhà một phần điểm s (hòa 0,5; thắng từ 3 bàn được 1). Bên thua bầu cho bên thắng, nên PageRank cao khi thắng được đội mạnh. Đồ thị chỉ dùng các trận trước ngày dự đoán, trong 3 năm, trận cũ nhẹ dần.
3. **Phân tích mạng.** 46 CLB, mật độ 0,77, nên mạng gần như đầy đủ. Cộng đồng yếu (modularity 0,04). PageRank khớp bảng xếp hạng (Spearman 0,937; đội vô địch luôn trong top 3).
4. **Đánh giá.** Thêm 5 đặc trưng đồ thị vào 85 đặc trưng của nhóm, kiểm thử theo thời gian trên 6.140 trận. Log loss 0,9835 → 0,9845, khoảng tin cậy chứa 0: không cải thiện.
5. **Vì sao.** Đặc trưng đồ thị trùng thông tin với Elo (tương quan tới 0,94). Kiểm định thêm giả thuyết H4 của EDA: đối đầu không bổ sung gì sau Elo và phong độ.
6. **Giá trị.** Đồ thị cho một thước đo sức mạnh giải thích được, và cho nhóm câu trả lời có kiểm chứng rằng không cần thêm nhóm biến này. Phần đánh giá còn phát hiện Logistic Regression bị hỏng do ngoại lai và chỉ ra cách sửa.

## 2. Câu hỏi về cách dựng đồ thị

**Nút, cạnh, trọng số là gì?** Nút là 46 CLB từng đá Premier League từ 2000/01. Có hai đồ thị:
- **Đồ thị ưu thế (có hướng):** mỗi trận tạo hai cạnh, đội khách → đội nhà với trọng số s và đội nhà → đội khách với trọng số 1 − s, nhân thêm trọng số thời gian.
- **Đồ thị số lần gặp (vô hướng):** trọng số là số trận giữa hai đội, dùng cho phát hiện cộng đồng.

**Vì sao bên thua "bầu" cho bên thắng, mà không làm ngược lại?** Để giữ đúng nghĩa PageRank: một trang được trỏ tới bởi nhiều trang quan trọng thì quan trọng. Một "người dạo ngẫu nhiên" đi theo cạnh "tôi đã thua ai" sẽ dừng lại nhiều ở các đội mạnh. Làm ngược lại thì PageRank đo "độ yếu".

**Vì sao dùng phần điểm theo hiệu số mà không chỉ thắng/hòa/thua? Vì sao chặn ở 3 bàn?** Thắng 3-0 nói lên nhiều hơn thắng 1-0, nhưng một trận 7-0 không nên chi phối cả mạng. Chặn ở 3 bàn giữ thông tin về mức độ thắng mà vẫn hạn chế ngoại lai. Trận hòa cho mỗi bên 0,5, tức hai đội bầu cho nhau như nhau.

**Vì sao cửa sổ 3 năm, nửa đời 365 ngày; đối đầu 10 năm, nửa đời 3 năm?** Sức mạnh đội bóng thay đổi nhanh: chuyển nhượng, đổi HLV, lên xuống hạng. Trận cách đây một năm chỉ được tính một nửa. Đối đầu trực tiếp rất thưa (mỗi mùa tối đa 2 trận), nên phải dùng cửa sổ dài hơn mới có đủ dữ liệu. Các tham số này được chọn theo lý lẽ, **không dò trên tập kiểm thử**, để tránh làm đẹp kết quả. Đây là một hạn chế đã nêu trong báo cáo.

**"Co về trung tính bằng 1 trận ảo" là gì?** Khi tính đối đầu, cộng thêm một trận giả có kết quả hòa. Hai đội mới gặp 1 lần, đội nhà thắng 3-0, thì `gr_h2h_share` chỉ là 0,25 thay vì 0,5. Cách này tránh kết luận cực đoan từ 1–2 trận; đây là ý tưởng của ước lượng Bayes với tiên nghiệm.

## 3. Câu hỏi về PageRank

**Công thức?** r = α·rP + (1 − α)/n, với α = 0,85. P là ma trận chuyển, mỗi hàng là trọng số "bầu" chuẩn hóa thành xác suất. Tính bằng lặp lũy thừa đến khi tổng thay đổi nhỏ hơn 10⁻¹⁰. Kết quả được nhân với n để trung bình bằng 1.

**Ý nghĩa của 0,85 và nút không có cạnh ra?** 15% xác suất người dạo nhảy ngẫu nhiên sang một đội bất kỳ (teleport). Điều này bảo đảm chuỗi Markov liên thông và hội tụ về một nghiệm duy nhất. Nút không có cạnh ra (đội chưa thua hay hòa ai trong cửa sổ) được cho nhảy đều sang mọi nút, để ma trận vẫn ngẫu nhiên theo hàng. 0,85 là giá trị chuẩn trong bài giảng và bài báo gốc của PageRank.

**Làm sao biết cài đặt đúng?** Có ba kiểm tra:
- Kiểm thử trên đồ thị nhỏ có đáp án biết trước: chuỗi A > B > C cho thứ tự đúng; chu trình đối xứng cho các giá trị bằng nhau.
- Đối chiếu với `networkx.pagerank` trên đồ thị ngẫu nhiên có nút kết: khớp tới 10⁻⁸ trong kiểm thử. Trên dữ liệu thật các mùa 2005/06, 2015/16, 2024/25, sai lệch tối đa là 3,5·10⁻¹¹.
- PageRank theo mùa khớp bảng xếp hạng cuối mùa.

**Vì sao không dùng thẳng `networkx.pagerank`?** Mỗi ngày thi đấu (2.740 ngày) phải dựng lại đồ thị với trọng số thời gian khác nhau. Cài đặt bằng ma trận numpy chạy toàn bộ 9.850 trận trong khoảng 3 giây, và được kiểm chứng là cho cùng kết quả với networkx.

**Vì sao PageRank trung bình trong file đặc trưng là 1,17 chứ không phải 1?** Chuẩn hóa tính trên mọi đội có mặt trong cửa sổ 3 năm, kể cả các đội đã xuống hạng và thường yếu hơn. Các đội đang đá Premier League vì vậy có trung bình trên 1.

## 4. Câu hỏi về rò rỉ dữ liệu

**Làm sao bảo đảm không dùng thông tin tương lai?** Đặc trưng của trận ngày D chỉ dùng các trận có ngày **nhỏ hơn** D, nên các trận cùng ngày cũng bị loại. Điều này được kiểm chứng bằng hai cách:
- `--selftest`: cắt bỏ mọi trận từ D trở đi rồi tính lại. Kết quả trùng khớp trên 6 ngày ngẫu nhiên.
- Kiểm thử đảo ngẫu nhiên tỷ số của **mọi** trận từ D trở đi: đặc trưng ngày D không đổi trên 8 ngày ngẫu nhiên. Nếu có bất kỳ thông tin tương lai nào lọt vào, giá trị chắc chắn sẽ đổi.

**Còn phân tích mạng toàn thời gian thì sao?** Phần đó là mô tả, dùng toàn bộ dữ liệu và không đưa vào mô hình. Chỉ các cột `gr_*` (tính theo cửa sổ trượt) mới được dùng để dự đoán.

**Đánh giá có rò rỉ không?** Không. Mỗi mùa kiểm thử chỉ huấn luyện trên các mùa trước nó (rolling-origin), không xáo trộn ngẫu nhiên. Riêng kèo nhà cái chưa có thời điểm thu thập (EDA đã nêu), nên kết quả được báo cáo cả khi không dùng kèo.

## 5. Câu hỏi về phân tích mạng lưới

**Mật độ 0,77 nghĩa là gì?** Có 800 trên 1.035 cặp CLB có thể có đã từng gặp nhau. Mỗi mùa, mọi cặp trong 20 đội đều đá với nhau hai lượt, nên mạng gần như đầy đủ. Hệ quả là các chỉ số dựa trên cấu trúc (bậc, cộng đồng, closeness, betweenness) ít phân biệt giữa các đội.

**Louvain và modularity là gì? Vì sao 0,04 lại thấp?** Louvain gom các nút sao cho cạnh bên trong nhóm dày hơn mức kỳ vọng ngẫu nhiên. Modularity đo mức chênh đó; thường từ khoảng 0,3 trở lên mới coi là có cấu trúc nhóm rõ. Giá trị 0,04 cho thấy gần như không có cụm thật. Ba nhóm tìm được chủ yếu phản ánh thời gian trụ hạng (trung bình 14, 9 và 2 mùa), không phải "các nhóm đội hay gặp nhau".

**PageRank khớp bảng xếp hạng có chứng minh PageRank tốt không?** Không hẳn. Đây chỉ là kiểm tra tính hợp lý, vì cả hai đều tính từ cùng các kết quả. Điểm đáng chú ý là chỗ hai bên lệch nhau:
- Tính trên 24 mùa đủ 380 trận: đội vô địch xếp hạng 1 theo PageRank ở 19 mùa và luôn nằm trong top 3.
- Năm mùa đội vô địch đứng thứ 2 theo PageRank: 2008/09, 2015/16, 2016/17, 2021/22, 2025/26.
- Ví dụ mùa 2015/16: Leicester vô địch với 81 điểm. Tottenham đứng đầu PageRank (1,232 so với 1,218 của Leicester) dù kém 11 điểm. Lý do: bảng điểm chỉ tính thắng/hòa/thua, còn PageRank tính thêm cách biệt tỷ số (tối đa 3 bàn) và sức mạnh đối thủ. Tottenham thắng cách biệt từ 3 bàn 9 trận (Leicester 4), và phần điểm trung bình trước 8 đội đầu bảng cao hơn (0,60 so với 0,52). Cần nói rõ: xét điểm số thuần, Leicester vẫn giành nhiều điểm hơn trước 8 đội đầu bảng (21 so với 20); khác biệt nằm ở cách biệt tỷ số.
- Mùa 2002/03 (Spearman thấp nhất, 0,806): Leeds hạng 15 theo điểm nhưng hạng 8 theo PageRank; Aston Villa hạng 16 nhưng hạng 9. Leeds (hạng 15) giành 12 điểm và Aston Villa (hạng 16) giành 11 điểm trước 6 đội đầu bảng, nhiều hơn các đội cùng nhóm điểm như Fulham (9) và Charlton (6), nhưng mất nhiều điểm trước các đội còn lại. PageRank coi trọng kết quả trước đội mạnh nên xếp hai đội này cao hơn bảng điểm.

**Sao không tính closeness, betweenness, HITS?** Với đồ thị gần như đầy đủ, khoảng cách giữa mọi cặp gần như bằng 1, nên closeness và betweenness gần như không phân biệt được các đội. HITS (hub và authority) trên đồ thị ưu thế cho authority gần giống PageRank. Có thể bổ sung nếu được yêu cầu, nhưng khó mang thêm thông tin.

## 6. Câu hỏi về đánh giá

**Vì sao dùng log loss mà không chỉ accuracy?** Đầu ra cần là xác suất thắng, hòa, thua (dashboard hiển thị xác suất). Log loss phạt nặng việc tự tin sai. Accuracy chỉ khoảng 0,53 và gần như không bao giờ chọn hòa (24% số trận), nên khó phân biệt các mô hình. Mốc tham chiếu: dự đoán theo tần suất nhãn cho log loss 1,067; Elo cho 0,98–0,99; kèo nhà cái cho 0,966–0,976.

**Bootstrap theo cặp là gì?** Hai mô hình dự đoán cùng 6.140 trận; lấy chênh lệch log loss theo từng trận rồi lấy mẫu lặp có hoàn lại 2.000 lần để có khoảng tin cậy 95% của trung bình chênh lệch. "Theo cặp" loại được biến động do trận dễ hay khó. Khoảng chứa 0 nghĩa là không phân biệt được hai mô hình.

**Vì sao rolling-origin mà không dùng k-fold?** K-fold xáo trộn làm mô hình học từ các mùa tương lai để đoán quá khứ. Rolling-origin mô phỏng đúng việc dự đoán thật: mỗi mùa chỉ biết các mùa trước. Báo cáo dùng thêm cách chia thống nhất của nhóm (huấn luyện đến 2023/24, kiểm thử từ 2024/25) để các khâu so sánh được với nhau.

**Vì sao hai mô hình?** Gradient Boosting tự xử lý tương tác và giá trị thiếu. Logistic Regression dễ giải thích và nhạy với biến trùng hay ngoại lai. Kết luận đúng trên cả hai thì mới vững.

**Vì sao Logistic Regression ban đầu kém hơn chỉ dùng Elo?** Có ba giả thuyết đã thử và đều bị loại: do `rest_days`, do 14 cột `diff_*` trùng đại số, và do cả hai cùng lúc. Nguyên nhân thật là ngoại lai đuôi nặng ở nhiều biến. Cắt phân vị 1–99% sửa được (1,265 → 0,980 trên các mùa 2018/19 – 2025/26). Ngay cả khi đã sửa, chỉ dùng Elo vẫn tốt hơn 85 đặc trưng; đây là gợi ý cho khâu Xây dựng mô hình nên chọn lọc biến.

## 7. Câu hỏi về kết quả âm tính

**Đặc trưng không cải thiện, vậy làm Link Analysis để làm gì?**
- **Trả lời đúng câu hỏi đề bài đặt ra.** Đề bài yêu cầu khai thác đặc trưng "nếu chúng thực sự hỗ trợ mô hình" và "so sánh xem có cải thiện không". Câu trả lời "không", kèm bằng chứng, giúp nhóm không đưa thêm 9 biến thừa vào mô hình cuối.
- **Hiểu vì sao.** Đồ thị đo cùng một thứ với Elo: Elo cũng là cách lan truyền sức mạnh qua kết quả đối đầu. Chỉ dùng đồ thị cho kết quả gần bằng chỉ dùng Elo, nghĩa là đồ thị đã nắm được sức mạnh đội.
- **Sản phẩm phụ có ích.** Có thước đo sức mạnh giải thích được, kiểm định H4 cho EDA, và chẩn đoán lỗi Logistic Regression cho khâu mô hình.

**Có thể làm gì để đồ thị có ích hơn?** Dùng xG thay cho bàn thắng làm trọng số cạnh (từ 2014/15), dùng đồ thị cầu thủ hoặc HLV, hoặc kết hợp nhiều giải đấu, nơi các đội không gặp nhau trực tiếp và liên kết gián tiếp mới có giá trị. Trong một giải mà mọi đội đều gặp nhau, thông tin gián tiếp gần như trùng với thông tin trực tiếp.

## 8. Câu hỏi về phối hợp nhóm

**Link Analysis khác gì EDA và Tích hợp dữ liệu?**
- **Tích hợp dữ liệu và EDA** làm việc trên bảng: mỗi dòng một trận, mỗi cột một đặc điểm của đội.
- **Link Analysis** làm việc trên quan hệ: một đội được đánh giá qua việc nó thắng ai, và đối thủ đó mạnh hay yếu.
- **Phần dùng lại:** Link Analysis dùng `matches.csv` và `features.csv` của khâu Tích hợp dữ liệu, các cột `elo_diff`, `odds_*_prob`, `h2h_*` làm đối chứng, và mã `club_id` chuẩn.
- **Phần giao lại:** kết quả xuất theo đúng khuôn file của EDA (danh mục đặc trưng, giả thuyết).

**Dữ liệu có vấn đề gì?** Hai mùa 2003/04 và 2004/05 thiếu 45 trận mỗi mùa; `rest_days` đo khoảng cách tới trận Premier League trước chứ không phải thời gian nghỉ. Cả hai đều được EDA ghi nhận độc lập. Link Analysis loại hai mùa thiếu trận khỏi thống kê Spearman.

**Làm sao tái lập?** Chạy `bash run_all.sh matches.csv features.csv`, mất khoảng 25 phút. Dựng lại từ một bản sao sạch cho kết quả giống hệt từng giá trị; có 6 kiểm thử tự động.

## 9. Câu hỏi về hình và cách trình bày

**Vì sao vẽ mạng theo vòng tròn mà không dùng bố cục lực đẩy?** Mạng gần như đầy đủ (mật độ 0,77): bố cục lực đẩy kéo mọi nút vào một khối, không đọc được. Vòng tròn xếp theo nhóm rồi theo sức mạnh cho thấy ngay hai thông tin chính: nhóm Louvain và ai mạnh.

**Hai CLB không có đường nối trên hình là chưa từng gặp nhau?** Đúng. Mọi cặp đã gặp đều được vẽ: 736 cặp gặp từ 1 đến 30 trận là đường mảnh, 64 cặp gặp từ 31 trận trở lên là đường dày. 235 cặp không có đường là chưa gặp lần nào tính đến 12/10/2026: 226 cặp chưa từng cùng đá một mùa (ví dụ Bradford chỉ đá 2000/01, Luton chỉ đá 2023/24), và 9 cặp cùng ở mùa 2026/27 nhưng chưa đến lượt gặp.

**Vì sao chia đường mảnh và đường dày?** Vẽ 800 đường cùng độ đậm sẽ thành một khối rối. Đường mảnh vẫn thể hiện đủ mọi cặp đã gặp (mật độ 0,77 nhìn thấy được), còn đường dày làm nổi các cặp gặp nhiều nhất, chủ yếu giữa các CLB đá gần như mọi mùa.

**Vì sao có hai bản hình mạng lưới?** Bản thường cho toàn cảnh và tra cứu; bản nổi bật làm mờ nền, chỉ tô 6 CLB mạnh nhất, nhóm C và cặp chênh lệch nhất, kèm chú thích, để người xem thấy ngay kết luận. Hai bản dùng cùng dữ liệu, cùng bố cục và cùng cách vẽ đường.

**Hình đánh giá đọc thế nào?** Mỗi dòng là chênh lệch log loss so với 85 đặc trưng, vạch là khoảng tin cậy 95%. Bên trái 0 là tốt hơn. Hai dòng có đồ thị: một vạch cắt qua 0 (Gradient Boosting), một vạch nằm hẳn bên phải (Logistic Regression), nên không cải thiện. Dòng "chỉ kèo" nằm hẳn bên trái, cho thấy cách đánh giá đủ nhạy để phát hiện tín hiệu thật.

**Notebook dùng để làm gì?** Để người xem đi lại toàn bộ luồng trong khoảng 2 phút, bằng chính các hàm trong `src/`. Kết quả trùng với `results/`, nên notebook vừa là tài liệu hướng dẫn vừa là bằng chứng tái lập.

## 10. Câu hỏi "bẫy" thường gặp

**"Spearman 0,937 cao vậy thì PageRank có gì mới so với bảng điểm?"** Bảng điểm coi mọi trận thắng như nhau; PageRank cân theo sức mạnh đối thủ. Phần khác biệt nằm ở các mùa lệch (2002/03, 2015/16). Nhưng cái mới đó đã có trong Elo, nên không giúp mô hình.

**"Kết quả âm tính có phải do cài sai?"** Có ba lớp kiểm tra: PageRank khớp networkx (sai lệch 3,5·10⁻¹¹), khớp bảng xếp hạng, và chỉ dùng 5 đặc trưng đồ thị cho log loss gần bằng chỉ dùng Elo (đồ thị "học" được sức mạnh). Nếu cài sai, đặc trưng đồ thị một mình sẽ kém xa Elo.

**"Sao không dò tham số (α, nửa đời, cửa sổ) để đồ thị tốt hơn?"** Dò trên chính tập kiểm thử sẽ làm đẹp kết quả một cách giả tạo. Muốn dò đúng phải có tập kiểm định riêng (validation) tách khỏi tập kiểm thử; với tương quan 0,94 với Elo, khả năng dò ra cải thiện thật là thấp. Đây là hướng mở rộng đã ghi nhận.

**"Accuracy chỉ 53%, mô hình có tệ không?"** Bóng đá nhiều ngẫu nhiên; kèo nhà cái, thứ tốt nhất hiện có, cũng chỉ khoảng 54%. Mô hình đoán luôn đội nhà thắng được khoảng 45%. Vì vậy log loss mới là thước đo phù hợp.

**"Logistic Regression +0,0009 với KTC dương: vậy đồ thị làm mô hình tệ đi?"** Có, nhưng rất ít: thêm 5 biến gần như trùng thông tin làm tăng phương sai ước lượng của mô hình tuyến tính. Đây là thêm một lý do không đưa nhóm biến này vào mô hình cuối.

**"Kèo nhà cái tốt nhất, có rò rỉ không?"** Thời điểm thu thập kèo chưa được xác minh (EDA, giả thuyết H9). Vì vậy kết luận về đồ thị được kiểm tra cả trong kịch bản không có kèo: kết quả không đổi (Gradient Boosting +0,0007, KTC [−0,0016; +0,0031]).

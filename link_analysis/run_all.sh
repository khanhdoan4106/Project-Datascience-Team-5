#!/usr/bin/env bash
# Chạy lại toàn bộ phần Link Analysis từ đầu.
# Cần matches.csv và features.csv (khâu Tích hợp dữ liệu, data/clean/) đặt cùng thư mục này, hoặc truyền đường dẫn:
#   bash run_all.sh path/to/matches.csv path/to/features.csv
set -euo pipefail
MATCHES=${1:-matches.csv}
FEATURES=${2:-features.csv}
mkdir -p results

echo "== Bước 1: đặc trưng đồ thị + tự kiểm tra rò rỉ"
python build_graph_features.py --dataset "$MATCHES" --out results/graph_features_matches.csv --selftest

echo "== Bước 2: phân tích mạng lưới + 3 hình"
python network_analysis.py --matches "$MATCHES" --out results > results/network_log.txt

echo "== Bước 3: đánh giá có / không có đặc trưng đồ thị (khoảng 5-10 phút)"
python evaluate_on_features.py --features "$FEATURES" --graph results/graph_features_matches.csv | tee results/eval_features.txt
python evaluate_logreg_robust.py --features "$FEATURES" --graph results/graph_features_matches.csv | tee results/eval_logreg_robust.txt

python evaluate_on_matches.py --matches "$MATCHES" --graph results/graph_features_matches.csv | tee results/eval_matches.txt

echo "== Kiểm thử"
cp "$MATCHES" matches.csv 2>/dev/null || true
python test_graph_features.py

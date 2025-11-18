import os  # thao tác đường dẫn và kiểm tra file/thu muc
import uuid  # tạo token unique cho mỗi ứng viên
import pandas as pd  # đọc/ghi CSV
from typing import List, Dict  # chú thích kiểu dữ liệu
from pathlib import Path  # thao tác đường dẫn theo pathlib


# Sử dụng thư mục backend/results (theo đường dẫn bạn cung cấp)
BASE_RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"
INPUT_FILE = str(BASE_RESULTS_DIR / "demo_data.csv")  # d:\Cap 1\HireSmart\backend\results\demo_data.csv
OUTPUT_FILE = str(BASE_RESULTS_DIR / "candidate_with_token.csv")  # sẽ tạo tại d:\Cap 1\HireSmart\backend\results\candidate_with_token.csv


def parse_raw_cv_file(input_path: str) -> List[Dict]:
    """
    Đọc file demo_data.csv dạng văn bản thô, tách các block ứng viên
    theo delimiter -----....----- và trả về danh sách dict mỗi ứng viên.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read().strip()  # đọc toàn bộ nội dung file

    delimiter = "-" * 40  # chuỗi phân cách giữa các bản ghi trong file mẫu
    blocks = [b.strip() for b in content.split(delimiter) if b.strip()]  # tách các block không rỗng
    records = []

    for idx, block in enumerate(blocks, start=1):
        # mỗi dòng chứa cặp key:value — lọc các dòng có ":" để tránh dòng rác
        lines = [ln.strip() for ln in block.splitlines() if ":" in ln]
        record = {"id": idx}  # gán id tăng dần cho mỗi ứng viên
        for line in lines:
            key, value = line.split(":", 1)  # chỉ tách 1 lần (tránh : trong giá trị)
            record[key.strip()] = value.strip()  # lưu key/value đã loại bỏ khoảng trắng thừa
        records.append(record)  # thêm bản ghi vào danh sách
    return records  # trả về danh sách dict ứng viên


def generate_tokens(records: List[Dict]) -> List[Dict]:
    """
    Nếu ứng viên chưa có trường 'token' thì tạo token UUID v4 cho họ.
    Trả về danh sách record đã cập nhật.
    """
    for r in records:
        if not r.get("token"):
            r["token"] = str(uuid.uuid4())  # tạo token duy nhất dưới dạng chuỗi
    return records


def save_to_csv(records: List[Dict], output_path: str):
    """
    Lưu danh sách dict thành file CSV.
    Tạo thư mục chứa nếu chưa tồn tại.
    """
    out_dir = os.path.dirname(output_path)
    os.makedirs(out_dir, exist_ok=True)  # đảm bảo thư mục tồn tại
    df = pd.DataFrame(records)  # chuyển sang DataFrame
    df.to_csv(output_path, index=False, encoding="utf-8-sig")  # ghi CSV với BOM cho Excel


def main():
    # Kiểm tra file input tồn tại
    if not os.path.exists(INPUT_FILE):
        print(f"[❌] Không tìm thấy file: {INPUT_FILE}")
        return

    # Parse file thô, tạo token và lưu kết quả
    records = parse_raw_cv_file(INPUT_FILE)
    tokenized_records = generate_tokens(records)
    save_to_csv(tokenized_records, OUTPUT_FILE)
    print(f"[✅] Đã tạo token cho {len(tokenized_records)} ứng viên.")
    print(f"[📄] File output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()


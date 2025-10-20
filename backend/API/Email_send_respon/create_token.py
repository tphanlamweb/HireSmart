import os
import uuid
import pandas as pd

# 📝 Đường dẫn file gốc (do Scan_CV.py ghi ra)
INPUT_FILE = os.path.join(os.path.dirname(__file__), "results", "demo_data.csv")

# 📝 File mới sau khi sinh token (chuẩn bảng)
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "results", "candidate_with_token.csv")

def parse_raw_cv_file(input_path: str):
    """
    Đọc file demo_data.csv (key: value), chuyển từng ứng viên thành dict.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        
    # tách thành từng ứng viên bằng dòng '-----'
    blocks = [b.strip() for b in  content.split("-" * 40) if b.strip()]
    records=[]
    
    for idx, blocks in enumerate(blocks, start=1):
        lines=[ln.strip() for ln in blocks.splitline() if ":" in ln]
        record= {"id": idx}
        for line in lines:
            key, value=line.splip(":",1)
            record[(key.strip())] = value.strip()
        records.append(record)
    return records
def generate_tokens(records: list[dict]):
    """
    sinh token cho từng ứng viên chưa có
    """
    for r in records:
        if "token" not in r or not r ["token"]:
            r["token"] = str(uuid.uuid4())
    return records
def save_to_csv(records:list[dict], output_path: str) :
    """
    Ghi dữ liệu ứng viên + token ra file CSV chuẩn bảng.
    """
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")


def main():
    # Kiểm tra file đầu vào
    if not os.path.exists(INPUT_FILE):
        print(f"[❌] Không tìm thấy file: {INPUT_FILE}")
        return

    # Bước 1: Đọc dữ liệu thô từ file gốc
    records = parse_raw_cv_file(INPUT_FILE)

    # Bước 2: Sinh token
    tokenized_records = generate_tokens(records)

    # Bước 3: Ghi ra file mới
    save_to_csv(tokenized_records, OUTPUT_FILE)

    print(f"[✅] Đã tạo token cho {len(tokenized_records)} ứng viên.")
    print(f"[📄] File output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

    
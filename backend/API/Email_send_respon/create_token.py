import csv
import os  # thao tác đường dẫn và kiểm tra file/thu muc
import re
import uuid  # tạo token unique cho mỗi ứng viên
from pathlib import Path  # thao tác đường dẫn theo pathlib
from typing import Dict, List  # chú thích kiểu dữ liệu

from sqlalchemy import MetaData, create_engine, select
from backend.dataAndModels.config import DATABASE_URL

# ==============================
# Cấu hình database
# ==============================


engine = create_engine(DATABASE_URL)
metadata = MetaData()
metadata.reflect(bind=engine)


# ==============================
# Đầu ra CSV
# ==============================
BASE_RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"
OUTPUT_FILE = str(BASE_RESULTS_DIR / "candidate_with_token.csv")


EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def generate_tokens(records: List[Dict]) -> List[Dict]:
    """
    Nếu ứng viên chưa có trường 'token' thì tạo token UUID v4 cho họ.
    Trả về danh sách record đã cập nhật.
    """
    for r in records:
        if not r.get("token"):
            r["token"] = str(uuid.uuid4())  # tạo token duy nhất dưới dạng chuỗi
    return records


def extract_full_name(record: Dict) -> str:
    value = record.get("full_name") or record.get("name")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "Không rõ"


def extract_email(record: Dict) -> str:
    email = record.get("email")
    if not isinstance(email, str):
        return ""

    normalized = email.replace(" ", "").strip()
    if EMAIL_PATTERN.fullmatch(normalized):
        return normalized
    return ""


def build_candidate_rows(records: List[Dict]) -> List[Dict]:
    """
    Lọc dữ liệu đầu vào và chỉ giữ lại các cột: id, full_name, email, token.
    Bỏ qua những bản ghi thiếu email (không gửi mail được).
    """
    candidate_rows = []
    next_id = 1

    for record in records:
        email = extract_email(record)
        if not email:
            continue  # không có email thì bỏ qua

        full_name = extract_full_name(record) or "Không rõ"
        candidate_id = record.get("id") or next_id

        candidate_rows.append(
            {
                "id": candidate_id,
                "full_name": full_name,
                "email": email,
                "token": record["token"],
            }
        )
        next_id += 1

    return candidate_rows


def fetch_candidates_from_db(candidate_ids: List[int]) -> List[Dict]:
    """
    Lấy danh sách ứng viên theo danh sách ID từ bảng candidates.
    """
    candidates = metadata.tables.get("candidates")
    if candidates is None:
        raise RuntimeError("Không tìm thấy bảng 'candidates' trong cơ sở dữ liệu.")

    if not candidate_ids:
        return []

    stmt = (
        select(
            candidates.c.id,
            candidates.c.full_name,
            candidates.c.email,
        )
        .where(candidates.c.id.in_(candidate_ids))
    )

    with engine.connect() as conn:
        result = conn.execute(stmt).fetchall()

    return [dict(row._mapping) for row in result]


def create_tokens_for_ids(candidate_ids: List[int]) -> List[Dict]:
    """
    Tạo token CHỈ CHO các ứng viên có id nằm trong candidate_ids.
    Trả về danh sách dict gồm: id, full_name, email, token.
    """
    records = fetch_candidates_from_db(candidate_ids)
    if not records:
        return []

    tokenized_records = generate_tokens(records)
    candidate_rows = build_candidate_rows(tokenized_records)
    return candidate_rows


def save_to_csv(records: List[Dict], output_path: str):
    """
    Lưu danh sách dict thành file CSV (UTF-8 BOM để mở bằng Excel).
    """
    out_dir = os.path.dirname(output_path)
    os.makedirs(out_dir, exist_ok=True)  # đảm bảo thư mục tồn tại

    fieldnames = ["id", "full_name", "email", "token"]
    with open(output_path, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in records:
            writer.writerow({
                "id": row.get("id", ""),
                "full_name": row.get("full_name", ""),
                "email": row.get("email", ""),
                "token": row.get("token", ""),
            })

    print(f"[CSV] Đã lưu {len(records)} bản ghi vào {output_path}")


def main():
    """
    Hàm main phục vụ chạy thử nhanh bằng tay.
    Ở môi trường thực tế, bạn nên gọi create_tokens_for_ids() từ API.
    """
    # Ví dụ test: tạo token cho id 1, 2, 3
    test_ids = [1, 2, 3]
    candidate_rows = create_tokens_for_ids(test_ids)

    if not candidate_rows:
        print("[⚠️] Không tìm thấy ứng viên nào hợp lệ với danh sách ID test.")
        return

    save_to_csv(candidate_rows, OUTPUT_FILE)
    print(f"[✅] Đã tạo token cho {len(candidate_rows)} ứng viên (test).")
    print(f"[📄] File output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()


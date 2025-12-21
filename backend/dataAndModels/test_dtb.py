import pymysql

conn = pymysql.connect(
    host="127.0.0.1",
    user="root",
    password="Lovecode@05",
    database="HireSmart",
    ssl_disabled=True,
)

print("Kết nối thành công!")
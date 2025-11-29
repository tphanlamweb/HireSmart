#   mysql+pymysql://<username>:<password>@<host>:<port>/<database_name>
DB_USER = "root"                # 🧑‍💻 Tên user MySQL
DB_PASSWORD = "Lovecode@05"          # 🔑 Mật khẩu MySQL
DB_HOST = "localhost"           # 🖥️  Địa chỉ server (hoặc IP)
DB_PORT = "3306"                # 🌐 Cổng mặc định của MySQL
DB_NAME = "HireSmart"  # 📂 Tên cơ sở dữ liệu bạn đã có

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


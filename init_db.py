import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pork.db")

def init_database():
    """创建数据库表并预填猪肉部位数据"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 创建猪肉部位表
    c.execute("""
        CREATE TABLE IF NOT EXISTS pork_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            image TEXT DEFAULT ''
        )
    """)

    # 创建预约表
    c.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            pork_part_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            appoint_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY (pork_part_id) REFERENCES pork_parts(id)
        )
    """)

    # 创建管理员表
    c.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    """)

    # 预填猪肉部位数据（如果表是空的）
    c.execute("SELECT COUNT(*) FROM pork_parts")
    if c.fetchone()[0] == 0:
        pork_data = [
            ("五花肉", "肥瘦相间，层次分明。适合：红烧肉、扣肉、烤肉、东坡肉", 18.0, 100, ""),
            ("里脊肉", "纯瘦肉，肉质细嫩。适合：糖醋里脊、锅包肉、水煮肉片", 22.0, 80, ""),
            ("排骨", "带骨带肉，骨香浓郁。适合：糖醋排骨、炖排骨、红烧排骨", 28.0, 60, ""),
            ("猪蹄", "富含胶原蛋白，口感软糯。适合：卤猪蹄、红烧猪蹄、花生猪蹄汤", 15.0, 50, ""),
            ("猪头肉", "皮厚肉嫩，风味独特。适合：凉拌猪头肉、卤猪头肉", 12.0, 40, ""),
            ("梅花肉", "瘦中带肥，口感嫩滑。适合：叉烧、煎猪排、涮火锅", 20.0, 70, ""),
            ("猪肘", "皮厚筋多，肉质紧实。适合：酱肘子、红烧肘子、水晶肘子", 16.0, 45, ""),
            ("猪肝", "补血佳品，营养丰富。适合：爆炒猪肝、猪肝粥、猪肝汤", 10.0, 30, ""),
        ]
        c.executemany(
            "INSERT INTO pork_parts (name, description, price, stock, image) VALUES (?, ?, ?, ?, ?)",
            pork_data,
        )
        print("已预填 8 种猪肉部位数据")

    # 预填管理员账号（默认 admin / admin123）
    from werkzeug.security import generate_password_hash
    c.execute("SELECT COUNT(*) FROM admin_users")
    if c.fetchone()[0] == 0:
        pw_hash = generate_password_hash("admin123")
        c.execute(
            "INSERT INTO admin_users (username, password_hash) VALUES (?, ?)",
            ("admin", pw_hash),
        )
        print("已创建默认管理员: admin / admin123")

    conn.commit()
    conn.close()
    print(f"数据库初始化完成！文件位置: {DB_PATH}")

if __name__ == "__main__":
    init_database()

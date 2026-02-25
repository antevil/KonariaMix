import sqlite3
import csv

# ============================================
# 1. DB 初期化
# ============================================
conn = sqlite3.connect("data.db")
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS combos")
cur.execute("DROP TABLE IF EXISTS drugs")
cur.execute("DROP TABLE IF EXISTS foods")

cur.execute("""
    CREATE TABLE drugs (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
""")

cur.execute("""
    CREATE TABLE foods (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT NOT NULL UNIQUE,
        display_order INTEGER NOT NULL
    );
""")

cur.execute("""
    CREATE TABLE combos (
        drug_id INTEGER NOT NULL,
        food_id INTEGER NOT NULL,
        result  TEXT NOT NULL,
        note    TEXT,
        PRIMARY KEY (drug_id, food_id),
        FOREIGN KEY (drug_id) REFERENCES drugs(id),
        FOREIGN KEY (food_id) REFERENCES foods(id)
    );
""")

# ============================================
# 2. CSV（行列形式）を読み込む
# ============================================
with open("combos_matrix.csv", encoding="utf-8") as f:
    reader = csv.reader(f)
    rows = list(reader)

# rows[0] = ["drug_name", "水", "離乳食", "牛乳", "お茶"]
header = rows[0]
food_names = header[1:]  # 1列目以外 → 全て飲食物名

# --------------------------------------------
# 2-1. foods テーブルへ登録
# --------------------------------------------
for order, food in enumerate(food_names):
    cur.execute(
        "INSERT INTO foods (name, display_order) VALUES (?, ?)",
        (food, order)
    )

# food_name → id を作る
cur.execute("SELECT id, name FROM foods ORDER BY id")
food_name_to_id = {row[1]: row[0] for row in cur.fetchall()}

# ============================================
# 3. 行（薬）を読み込み → combos に展開
# ============================================
for row in rows[1:]:
    drug_name = row[0].strip()
    results = row[1:]  # 水・離乳食・牛乳・お茶 の結果

    # drug 登録
    cur.execute(
        "INSERT OR IGNORE INTO drugs (name) VALUES (?)",
        (drug_name,)
    )
    cur.execute("SELECT id FROM drugs WHERE name = ?", (drug_name,))
    drug_id = cur.fetchone()[0]

    # 各飲食物の判定を combos に登録
    for food, result in zip(food_names, results):
        result = result.strip()
        food_id = food_name_to_id[food]

        cur.execute("""
            INSERT OR REPLACE INTO combos (drug_id, food_id, result, note)
            VALUES (?, ?, ?, ?)
        """, (drug_id, food_id, result, ""))

conn.commit()
conn.close()

print("data.db を作成しました！（行列形式CSV対応）")

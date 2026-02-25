from flask import Flask, render_template, request, jsonify
import sqlite3
import re

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/search")
def api_search():
    # 入力（スペース/改行/カンマ区切りで複数OK）
    raw = request.args.get("drugs", "").strip()
    if not raw:
        return jsonify({"foods": [], "drugs": [], "not_found": []})

    tokens = re.split(r"[\s,、，]+", raw)
    tokens = [t for t in tokens if t]

    conn = get_db()

    # foods（列）
    cur = conn.execute("SELECT id, name FROM foods ORDER BY display_order")
    foods = [dict(row) for row in cur.fetchall()]

    # 入力トークンから drugs を検索（簡易：LIKEで最初にヒットした1件を採用）
    drug_entries = []
    not_found = []

    for token in tokens:
        cur = conn.execute(
            "SELECT id, name FROM drugs WHERE name LIKE ? ORDER BY name LIMIT 1",
            (f"%{token}%",)
        )
        row = cur.fetchone()
        if row is None:
            not_found.append(token)
        else:
            # 重複追加を防ぐ
            if all(d["id"] != row["id"] for d in drug_entries):
                drug_entries.append({"id": row["id"], "name": row["name"]})

    if not drug_entries:
        return jsonify({
            "foods": [f["name"] for f in foods],
            "drugs": [],
            "not_found": not_found
        })

    drug_ids = [d["id"] for d in drug_entries]
    placeholders = ",".join("?" for _ in drug_ids)

    # combos を JOIN して結果をまとめて取る
    query = f"""
        SELECT d.id AS drug_id,
               d.name AS drug_name,
               f.name AS food_name,
               c.result,
               c.note
        FROM combos c
        JOIN drugs d ON d.id = c.drug_id
        JOIN foods f ON f.id = c.food_id
        WHERE c.drug_id IN ({placeholders})
        ORDER BY d.name, f.display_order
    """
    cur = conn.execute(query, drug_ids)
    rows = cur.fetchall()

    # 行列に整形
    matrix = {}
    for row in rows:
        drug_name = row["drug_name"]
        food_name = row["food_name"]
        if drug_name not in matrix:
            matrix[drug_name] = {}
        matrix[drug_name][food_name] = {
            "result": row["result"],
            "note": row["note"] or ""
        }

    # APIの戻り形式
    return jsonify({
        "foods": [f["name"] for f in foods],
        "drugs": [
            {"name": d["name"], "results": matrix.get(d["name"], {})}
            for d in drug_entries
        ],
        "not_found": not_found
    })

if __name__ == "__main__":
    app.run(debug=True)

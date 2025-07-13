from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
from elo_calculator import process_elo

app = Flask(__name__)
DB_PATH = "elo_ranking.db"

# Tạo bảng matches_raw nếu chưa có
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS matches_raw (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     timestamp TEXT,
    #     player1 TEXT,
    #     race1 TEXT,
    #     map TEXT,
    #     result REAL,
    #     player2 TEXT,
    #     race2 TEXT,
    #     processed BOOLEAN DEFAULT 0
    # )
    # """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        name TEXT PRIMARY KEY,
        elo INTEGER DEFAULT 1500,
        w3vn_7 INTEGER DEFAULT 0,        
        matches_played INTEGER DEFAULT 0,
        matches_won INTEGER DEFAULT 0
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS elo_history_raw (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        player TEXT,
        elo INTEGER
    )
    """)
    conn.commit()
    conn.close()
    
@app.route("/add", methods=["GET", "POST"])
def add_match():
    message = None
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM players ORDER BY name")
    player_names = [row[0] for row in cursor.fetchall()]
    conn.close()

    # Cố định race/map nếu chưa có bảng riêng
    races = ["HU", "ORC", "NE", "UD"]
    maps = ["Amazonia", "Autumn Leaves", "Concealed Hill", "Echo Isles", "Hammerfall", "Last Refuge", "Northern Isles", "Terenas Stand"]
    if request.method == "POST":
        try:
            ts = datetime.now()
            player1 = request.form["player1"].strip()
            race1 = request.form["race1"].strip()
            map_name = request.form["map"].strip()
            result_text = request.form["result_text"].strip().lower()
            player2 = request.form["player2"].strip()
            race2 = request.form["race2"].strip()

            # Convert result
            if result_text == "thắng":
                result = 1
            elif result_text == "thua":
                result = 0
            else:
                message = "⛔ Kết quả chỉ nhận 'Thắng' hoặc 'Thua'"
                return render_template("add_match.html", message=message)

            # Ghi vào DB
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO form_responses_raw (timestamp, player1, race1, map, result, player2, race2, processed)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """, (ts.isoformat(), player1, race1, map_name, result, player2, race2))
            
            # Tự động xử lý ELO sau khi thêm
            process_elo(cursor, ts)
            
            conn.commit()
            conn.close()

            message = "✅ Đã thêm kết quả trận đấu."
        except Exception as e:
            message = f"⛔ Lỗi: {str(e)}"

    return render_template(
        "add_match.html",
        message=message,
        player_names=player_names,
        races=races,
        maps=maps
    )
        
def get_rankings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = datetime.today().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT rank, player, elo FROM rankings
        WHERE rank_date = ?
        ORDER BY rank ASC
    """, (today,))
    data = cursor.fetchall()
    cursor.execute("SELECT MAX(date) FROM elo_history_raw")
    raw_time = cursor.fetchone()[0]
    
    conn.close()
    
    # ✅ Định dạng lại thành: 13/07/2025 21:30
    last_updated = None
    if raw_time:
        try:
            dt = datetime.fromisoformat(raw_time)
            last_updated = dt.strftime("%d/%m/%Y %H:%M")
        except:
            last_updated = raw_time  # fallback nếu lỗi định dạng
            
    return data, last_updated

def penalize_non_participants(db_path="elo_ranking.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Trừ 200 ELO cho người chơi không tham gia
    cursor.execute("""
        UPDATE players
        SET elo = elo - 200
        WHERE w3vn_7 = 0
    """)

    conn.commit()
    conn.close()
    print("✅ Đã trừ 200 ELO cho người chơi không tham gia W3VN 7.")

@app.route("/", methods=["GET"])
def index():
    search_result = None
    rankings, last_updated = get_rankings()

    return render_template("index.html", rankings=rankings, search_result=search_result, last_updated=last_updated)

@app.route("/matches")
def show_matches():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, player1, race1, map, result, player2, race2
        FROM form_responses_raw
        ORDER BY id DESC
        LIMIT 100
    """)
    matches = cursor.fetchall()
    conn.close()

    # Chuyển result thành "Thắng" hoặc "Thua" dựa trên player1
    matches_display = [
        {
            "timestamp": r[0],
            "player1": r[1],
            "race1": r[2],
            "map": r[3],
            "result": "Thắng" if r[4] == 1 else "Thua",
            "player2": r[5],
            "race2": r[6],
        } for r in matches
    ]

    return render_template("matches.html", matches=matches_display)

@app.route("/players")
def list_players():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, elo, matches_played, matches_won, win_rate, w3vn_7 FROM players ORDER BY elo DESC")
    players = cursor.fetchall()
    conn.close()

    return render_template("players.html", players=players)

@app.route("/add_player", methods=["GET", "POST"])
def add_player():
    message = None
    if request.method == "POST":
        name = request.form.get("name").strip()
        if not name:
            message = "⛔ Tên không được để trống."
        else:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO players (name, elo, matches_played, matches_won, win_rate) VALUES (?, 1500, 0, 0, 0.0)", (name,))
                conn.commit()
                message = f"✅ Đã thêm người chơi: {name}"
            except sqlite3.IntegrityError:
                message = "⚠️ Người chơi đã tồn tại."
            finally:
                conn.close()
    return render_template("add_player.html", message=message)

@app.route("/edit_w3vn", methods=["GET", "POST"])
def edit_w3vn():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    message = None

    if request.method == "POST":
        name = request.form.get("name")
        value = request.form.get("w3vn_7")
        try:
            cursor.execute("UPDATE players SET w3vn_7 = ? WHERE name = ?", (int(value), name))
            conn.commit()
            message = f"✅ Đã cập nhật người chơi {name} với w3vn_7 = {value}"
        except:
            message = "⛔ Cập nhật thất bại."

    cursor.execute("SELECT name, w3vn_7 FROM players ORDER BY name")
    players = cursor.fetchall()
    conn.close()

    return render_template("edit_w3vn.html", players=players, message=message)


if __name__ == "__main__":
    # init_db()    
    import os
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":  # chạy lần đầu, không phải reload
        penalize_non_participants()
    app.run(debug=True)

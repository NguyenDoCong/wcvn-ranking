from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
from elo_calculator import process_elo
from rankings import update_rankings

app = Flask(__name__)
DB_PATH = "elo_ranking.db"

# Tạo bảng matches_raw nếu chưa có
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        name TEXT PRIMARY KEY,
        elo INTEGER DEFAULT 1500,
        w3vn_7 INTEGER DEFAULT 0,        
        matches_played INTEGER DEFAULT 0,
        matches_won INTEGER DEFAULT 0,
        win_rate REAL DEFAULT 0.0,
        penalized INTEGER DEFAULT 0
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
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS form_responses_raw (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player1 TEXT,
        player2 TEXT,
        result REAL,
        timestamp TEXT,
        race1 TEXT,
        race2 TEXT,
        map TEXT,
        processed BOOLEAN DEFAULT 0
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_flags (
        flag_name TEXT PRIMARY KEY,
        flag_value INTEGER DEFAULT 0
    )
    """)
    
    cursor.execute("""
    INSERT OR IGNORE INTO system_flags (flag_name, flag_value)
    VALUES ('penalty_applied', 0)
    """)
    
    cursor.execute("""
        INSERT OR IGNORE INTO players (name, elo, matches_played, matches_won, win_rate)
        SELECT DISTINCT player1, 1500, 0, 0, 0.0
        FROM form_responses_raw
        WHERE player1 NOT IN (SELECT name FROM players)
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO players (name, elo, matches_played, matches_won, win_rate)
        SELECT DISTINCT player2, 1500, 0, 0, 0.0
        FROM form_responses_raw
        WHERE player2 NOT IN (SELECT name FROM players)
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO system_flags (flag_name, flag_value)
        VALUES ('penalty_applied', 0)
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

    get_rankings()

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

    update_rankings(DB_PATH)  # Cập nhật bảng xếp hạng mới nhất
    
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

    # # Kiểm tra xem đã apply penalty chưa
    # cursor.execute("SELECT flag_value FROM system_flags WHERE flag_name = 'penalty_applied'")
    # result = cursor.fetchone()
    
    # if result and result[0] == 1:
    #     print("⚠️ Penalty đã được áp dụng trước đó, bỏ qua.")
    #     conn.close()
    #     return

    # Trừ 200 ELO cho người chưa từng bị phạt và không tham gia W3VN 7
    cursor.execute("""
        UPDATE players
        SET elo = elo - 200,
            penalized = 1
        WHERE w3vn_7 = 0 AND penalized = 0
    """)

    # Đánh dấu đã apply penalty
    cursor.execute("""
        UPDATE system_flags 
        SET flag_value = 1 
        WHERE flag_name = 'penalty_applied'
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
        SELECT id, timestamp, player1, race1, map, result, player2, race2
        FROM form_responses_raw
        ORDER BY id DESC
    """)
    matches = cursor.fetchall()
    conn.close()

    matches_display = [
        {
            "id": r[0],
            "timestamp": r[1],
            "player1": r[2],
            "race1": r[3],
            "map": r[4],
            "result": "Thắng" if r[5] == 1 else "Thua",
            "player2": r[6],
            "race2": r[7],
        } for r in matches
    ]

    return render_template("matches.html", matches=matches_display)

@app.route("/delete_match/<int:id>", methods=["POST"])
def delete_match(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM form_responses_raw WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/matches")

@app.route("/edit_match/<int:id>", methods=["GET", "POST"])
def edit_match(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Lấy danh sách người chơi, race, map như phần thêm
    cursor.execute("SELECT name FROM players ORDER BY name")
    player_names = [row[0] for row in cursor.fetchall()]
    races = ["HU", "ORC", "NE", "UD"]
    maps = ["Amazonia", "Autumn Leaves", "Concealed Hill", "Echo Isles", "Hammerfall", "Last Refuge", "Northern Isles", "Terenas Stand"]

    if request.method == "POST":
        try:
            player1 = request.form["player1"].strip()
            race1 = request.form["race1"].strip()
            map_name = request.form["map"].strip()
            result_text = request.form["result_text"].strip().lower()
            player2 = request.form["player2"].strip()
            race2 = request.form["race2"].strip()

            result = 1 if result_text == "thắng" else 0 if result_text == "thua" else None
            if result is None:
                return render_template("edit_match.html", message="⛔ Kết quả không hợp lệ.", **locals())

            # Cập nhật vào DB
            cursor.execute("""
                UPDATE form_responses_raw
                SET player1=?, race1=?, map=?, result=?, player2=?, race2=?
                WHERE id=?
            """, (player1, race1, map_name, result, player2, race2, id))
            conn.commit()
            conn.close()
            return redirect("/matches")

        except Exception as e:
            message = f"⛔ Lỗi: {str(e)}"
            return render_template("edit_match.html", message=message, **locals())

    # GET – lấy dữ liệu cũ
    cursor.execute("""
        SELECT player1, race1, map, result, player2, race2
        FROM form_responses_raw WHERE id=?
    """, (id,))
    match = cursor.fetchone()
    conn.close()

    if not match:
        return f"⛔ Không tìm thấy trận có ID {id}", 404

    match_dict = {
        "player1": match[0],
        "race1": match[1],
        "map": match[2],
        "result_text": "Thắng" if match[3] == 1 else "Thua",
        "player2": match[4],
        "race2": match[5],
    }

    return render_template("edit_match.html", match=match_dict, player_names=player_names, races=races, maps=maps)



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

    if request.method == "POST" and 'w3vn_7' in request.form and 'name' in request.form:
        try:
            name = request.form.get("name")
            new_value = int(request.form.get("w3vn_7"))
        except (ValueError, TypeError):
            message = "⛔ Dữ liệu không hợp lệ."
            new_value = None

        if new_value is not None:

            # Lấy giá trị cũ
            cursor.execute("SELECT w3vn_7, penalized, elo FROM players WHERE name = ?", (name,))
            row = cursor.fetchone()
            if not row:
                message = "⛔ Người chơi không tồn tại."
            else:
                old_value, penalized, current_elo = row

                try:
                    cursor.execute("UPDATE players SET w3vn_7 = ? WHERE name = ?", (new_value, name))

                    # 👇 Nếu sửa từ 0 thành 1 và đã bị trừ → hoàn điểm lại
                    if old_value == 0 and new_value == 1 and penalized == 1:
                        cursor.execute("""
                            UPDATE players SET elo = ?, penalized = 0 WHERE name = ?
                        """, (current_elo + 200, name))
                        message = f"✅ Đã cập nhật {name} và hoàn lại 200 ELO do chuyển sang tham gia W3VN 7."

                    # 👇 Nếu sửa từ 1 thành 0 và chưa bị trừ → trừ điểm và đánh dấu
                    elif old_value == 1 and new_value == 0 and penalized == 0:
                        cursor.execute("""
                            UPDATE players SET elo = ?, penalized = 1 WHERE name = ?
                        """, (current_elo - 200, name))
                        message = f"✅ Đã cập nhật {name} và trừ 200 ELO do không tham gia W3VN 7."

                    else:
                        message = f"✅ Đã cập nhật người chơi {name} (không thay đổi ELO)."

                    conn.commit()

                except Exception as e:
                    message = f"⛔ Lỗi: {str(e)}"

    cursor.execute("SELECT name, w3vn_7 FROM players ORDER BY name")
    players = cursor.fetchall()
    conn.close()
    
    get_rankings()
    return render_template("edit_w3vn.html", players=players, message=message)


if __name__ == "__main__":
    # init_db()    
    import os
    # if os.environ.get("WERKZEUG_RUN_MAIN") == "true":  # chạy lần đầu, không phải reload
    penalize_non_participants()
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=5000, debug=True)

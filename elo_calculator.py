import sqlite3
from datetime import datetime

def process_elo(cursor, match_time, player1, player2, result, mark_processed=True, match_id=None):
    k = 32

    # Lấy ELO hiện tại hoặc mặc định là 1500
    for player in [player1, player2]:
        cursor.execute("SELECT elo, matches_played, matches_won FROM players WHERE name = ?", (player,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO players (name, elo, matches_played, matches_won, win_rate) VALUES (?, ?, 0, 0, 0)", (player, 1500))

    cursor.execute("SELECT elo, matches_played, matches_won FROM players WHERE name = ?", (player1,))
    elo1, played1, won1 = cursor.fetchone()

    cursor.execute("SELECT elo, matches_played, matches_won FROM players WHERE name = ?", (player2,))
    elo2, played2, won2 = cursor.fetchone()

    # Tính ELO mới
    expected1 = 1 / (1 + 10 ** ((elo2 - elo1) / 400))
    new_elo1 = round(elo1 + k * (result - expected1))
    new_elo2 = round(elo2 + k * ((1 - result) - (1 - expected1)))

    # Cập nhật thống kê
    played1 += 1
    played2 += 1
    won1 += int(result == 1)
    won2 += int(result == 0)
    win_rate1 = won1 / played1
    win_rate2 = won2 / played2

    cursor.execute("""
        UPDATE players SET elo = ?, matches_played = ?, matches_won = ?, win_rate = ?
        WHERE name = ?
    """, (new_elo1, played1, won1, win_rate1, player1))
    cursor.execute("""
        UPDATE players SET elo = ?, matches_played = ?, matches_won = ?, win_rate = ?
        WHERE name = ?
    """, (new_elo2, played2, won2, win_rate2, player2))

    # Lưu lịch sử
    cursor.execute("INSERT INTO elo_history_raw (date, player, elo) VALUES (?, ?, ?)", (match_time, player1, new_elo1))
    cursor.execute("INSERT INTO elo_history_raw (date, player, elo) VALUES (?, ?, ?)", (match_time, player2, new_elo2))

    # Đánh dấu đã xử lý nếu cần
    if mark_processed and match_id:
        cursor.execute("UPDATE form_responses_raw SET processed = 1 WHERE id = ?", (match_id,))

def process_elo_matches(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Lấy các trận chưa xử lý
    cursor.execute("""
        SELECT id, player1, player2, result, timestamp
        FROM form_responses_raw
        WHERE processed = 0
        ORDER BY id ASC
    """)
    matches = cursor.fetchall()

    for match_id, player1, player2, result, timestamp in matches:
        match_time = timestamp or datetime.now().strftime("%Y-%m-%d")
        process_elo(cursor, match_time, player1, player2, result, mark_processed=True, match_id=match_id)
        
    print(f"✅ Đã xử lý {len(matches)} trận đấu ELO.")

    conn.commit()
    conn.close()

def reset_all_elo(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("UPDATE players SET elo = 1500, matches_played = 0, matches_won = 0, win_rate = 0.0, penalized= 0")
    cursor.execute("DELETE FROM elo_history_raw")
    cursor.execute("UPDATE form_responses_raw SET processed = 0")
    cursor.execute("UPDATE system_flags SET flag_value = 0")
    
    conn.commit()
    conn.close()
    print("✅ Đã reset toàn bộ ELO về 1500 và xóa lịch sử.")


# Gọi hàm
if __name__ == "__main__":
    reset_all_elo("elo_ranking.db")

    process_elo_matches("elo_ranking.db")

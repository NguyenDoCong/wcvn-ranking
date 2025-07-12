import sqlite3
from datetime import datetime

def process_elo_matches(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Lấy các trận chưa xử lý
    cursor.execute("""
        SELECT id, player1, player2, result
        FROM matches_raw
        WHERE processed = 0
    """)
    matches = cursor.fetchall()

    k = 32  # Hệ số ELO
    today = datetime.today().strftime("%Y-%m-%d")

    for match_id, player1, player2, result in matches:
        # Lấy ELO hiện tại hoặc mặc định là 1500
        cursor.execute("SELECT elo, matches_played, matches_won FROM players WHERE name = ?", (player1,))
        row1 = cursor.fetchone()
        if row1:
            elo1, played1, won1 = row1
        else:
            elo1, played1, won1 = 1500, 0, 0
            cursor.execute("INSERT INTO players (name, elo, matches_played, matches_won, win_rate) VALUES (?, ?, 0, 0, 0)", (player1, elo1))

        cursor.execute("SELECT elo, matches_played, matches_won FROM players WHERE name = ?", (player2,))
        row2 = cursor.fetchone()
        if row2:
            elo2, played2, won2 = row2
        else:
            elo2, played2, won2 = 1500, 0, 0
            cursor.execute("INSERT INTO players (name, elo, matches_played, matches_won, win_rate) VALUES (?, ?, 0, 0, 0)", (player2, elo2))

        # Tính toán ELO mới
        expected1 = 1 / (1 + 10 ** ((elo2 - elo1) / 400))
        new_elo1 = round(elo1 + k * (result - expected1))
        new_elo2 = round(elo2 + k * ((1 - result) - (1 - expected1)))

        # Cập nhật thông tin người chơi
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
        cursor.execute("INSERT INTO elo_history_raw (date, player, elo) VALUES (?, ?, ?)", (today, player1, new_elo1))
        cursor.execute("INSERT INTO elo_history_raw (date, player, elo) VALUES (?, ?, ?)", (today, player2, new_elo2))

        # Đánh dấu trận đã xử lý
        cursor.execute("UPDATE matches_raw SET processed = 1 WHERE id = ?", (match_id,))

    conn.commit()
    conn.close()

# Gọi hàm
process_elo_matches("elo_ranking.db")

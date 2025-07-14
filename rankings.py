import sqlite3
from datetime import datetime

def update_rankings(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Tạo bảng rankings nếu chưa có
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rankings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player TEXT NOT NULL,
        elo INTEGER NOT NULL,
        rank INTEGER NOT NULL,
        rank_date TEXT DEFAULT (date('now'))
    )
    """)

    # Lấy danh sách người chơi đủ điều kiện
    cursor.execute("""
        SELECT name, elo
        FROM players
        WHERE matches_played >= 5
        ORDER BY elo DESC
    """)
    players = cursor.fetchall()

    today = datetime.today().strftime("%Y-%m-%d")

    # Xoá bảng xếp hạng hôm nay nếu đã có
    cursor.execute("DELETE FROM rankings WHERE rank_date = ?", (today,))

    # Lưu bảng xếp hạng
    for rank, (player, elo) in enumerate(players, start=1):
        cursor.execute("""
            INSERT INTO rankings (player, elo, rank, rank_date)
            VALUES (?, ?, ?, ?)
        """, (player, elo, rank, today))

    conn.commit()
    conn.close()

# Gọi hàm
update_rankings("elo_ranking.db")


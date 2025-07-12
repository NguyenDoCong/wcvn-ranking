import pandas as pd
import sqlite3

# Đường dẫn tới file Excel và SQLite
file_path = "ELO ranking by map.xlsx"
sqlite_db_path = "elo_ranking.db"

# Đọc Excel
xls = pd.ExcelFile(file_path)
player_df = xls.parse("Danh sách người chơi")
match_df = xls.parse("Kết quả")
history_df = xls.parse("Lịch sử ELO")

# Chuẩn hóa player_df
player_df.columns = ["name", "elo", "elo_formula", "matches_played", "matches_won", "win_rate"]
player_df = player_df[["name", "elo", "matches_played", "matches_won"]]
player_df["win_rate"] = player_df["matches_won"] / player_df["matches_played"]
player_df = player_df.dropna(subset=["elo", "matches_played", "matches_won"])

# Chuẩn hóa match_df
match_df = match_df.rename(columns={
    "Unnamed: 0": "player1",
    "Unnamed: 2": "player2",
    "Kết quả": "result",
    "Đã xử lý": "processed"
})
match_df = match_df[["player1", "player2", "result", "processed"]]
match_df = match_df.dropna(subset=["player1", "player2", "result"])

# Chuẩn hóa history_df
history_df.columns = ["date", "player", "elo"]

# Kết nối SQLite
conn = sqlite3.connect(sqlite_db_path)
cursor = conn.cursor()

# Tạo các bảng
cursor.executescript("""
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS matches_raw;
DROP TABLE IF EXISTS elo_history_raw;

CREATE TABLE players (
    name TEXT PRIMARY KEY,
    elo INTEGER NOT NULL DEFAULT 1500,
    matches_played INTEGER NOT NULL DEFAULT 0,
    matches_won INTEGER NOT NULL DEFAULT 0,
    win_rate REAL DEFAULT 0.0
);

CREATE TABLE matches_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player1 TEXT NOT NULL,
    player2 TEXT NOT NULL,
    result REAL CHECK (result IN (0, 1)),
    processed BOOLEAN DEFAULT 0
);

CREATE TABLE elo_history_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    player TEXT,
    elo INTEGER
);
""")

# Ghi dữ liệu
player_df.to_sql("players", conn, if_exists="append", index=False)
match_df.to_sql("matches_raw", conn, if_exists="append", index=False)
history_df.to_sql("elo_history_raw", conn, if_exists="append", index=False)

conn.commit()
conn.close()

print("✅ Đã ghi dữ liệu vào SQLite:", sqlite_db_path)

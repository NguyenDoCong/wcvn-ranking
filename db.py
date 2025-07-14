import pandas as pd
import sqlite3
from datetime import datetime

# Đường dẫn tới file Excel và SQLite
file_path = "ELO ranking by map.xlsx"
sqlite_db_path = "elo_ranking.db"

# Đọc Excel
xls = pd.ExcelFile(file_path)
# player_df = xls.parse("Danh sách người chơi")
# match_df = xls.parse("Kết quả")
history_df = xls.parse("Lịch sử ELO")
match_raw_df = xls.parse("Form Responses 4")

# Chuẩn hóa player_df
# player_df.columns = ["name", "elo", "elo_formula", "matches_played", "matches_won", "win_rate"]
# player_df = player_df[["name", "elo", "matches_played", "matches_won"]]
# player_df["win_rate"] = player_df["matches_won"] / player_df["matches_played"]
# player_df = player_df.dropna(subset=["elo", "matches_played", "matches_won"])

# # Chuẩn hóa match_df
# match_df = match_df.rename(columns={
#     "Unnamed: 0": "player1",
#     "Unnamed: 2": "player2",
#     "Kết quả": "result",
#     "Đã xử lý": "processed"
# })
# match_df = match_df[["player1", "player2", "result", "processed"]]
# match_df = match_df.dropna(subset=["player1", "player2", "result"])

# Chuẩn hóa match_df
match_raw_df = match_raw_df.rename(columns={
    "Timestamp": "timestamp",    
    "Người chơi 1": "player1",
    "Race 1": "race1",
    "Map": "map",        
    "Kết quá": "result_text",
    "Người chơi 2": "player2",
    "Race 2": "race2",
})

# match_raw_df.columns = ["timestamp", "player1", "race1", "map", "result_text", "player2", "race2"]
# match_raw_df = match_raw_df.dropna(subset=["player1", "player2", "result_text"])

# Chuyển kết quả thành số: player1 thắng = 1, thua = 0
def convert_result(text):
    text = text.strip().lower()
    if text == "thắng":
        return 1
    elif text == "thua":
        return 0
    else:
        return None
    
match_raw_df["result"] = match_raw_df["result_text"].apply(convert_result)
match_raw_df = match_raw_df.dropna(subset=["result"])  

# # Chuẩn hoá timestamp
# def convert_time(t):
#     try:
#         return datetime.strptime(t, "%m/%d/%Y %H:%M:%S")
#     except:
#         return None  

# match_raw_df["timestamp"] = match_raw_df["timestamp"].apply(convert_time)
# match_raw_df = match_raw_df.dropna(subset=["timestamp"])

# Ghi dữ liệu
df_to_insert = match_raw_df[["timestamp", "player1", "race1", "map", "result", "player2", "race2"]]

df_to_insert["processed"] = False

# Tạo bảng matches_raw nếu chưa có
# conn = sqlite3.connect(sqlite_db_path)
# cursor = conn.cursor()
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS form_responses_raw (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     player1 TEXT,
#     player2 TEXT,
#     result REAL,
#     timestamp TEXT,
#     race1 TEXT,
#     race2 TEXT,
#     map TEXT,
#     processed BOOLEAN DEFAULT 0
# )
# """)

# Chuẩn hóa history_df
history_df.columns = ["date", "player", "elo"]

# Kết nối SQLite
conn = sqlite3.connect(sqlite_db_path)
cursor = conn.cursor()

# Tạo các bảng
cursor.executescript("""
DROP TABLE IF EXISTS elo_history_raw;
DROP TABLE IF EXISTS form_responses_raw;

CREATE TABLE IF NOT EXISTS players (
    name TEXT PRIMARY KEY,
    elo INTEGER NOT NULL DEFAULT 1500,
    w3vn_7 INTEGER DEFAULT 0,        
    matches_played INTEGER NOT NULL DEFAULT 0,
    matches_won INTEGER NOT NULL DEFAULT 0,
    win_rate REAL DEFAULT 0.0,
    penalized INTEGER DEFAULT 0
);

CREATE TABLE elo_history_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    player TEXT,
    elo INTEGER
);

CREATE TABLE form_responses_raw (
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

# Ghi dữ liệu
# player_df.to_sql("players", conn, if_exists="append", index=False)
# match_df.to_sql("matches_raw", conn, if_exists="append", index=False)
history_df.to_sql("elo_history_raw", conn, if_exists="append", index=False)
df_to_insert.to_sql("form_responses_raw", conn, if_exists="append", index=False)

conn.commit()
conn.close()

print("✅ Đã ghi dữ liệu vào SQLite:", sqlite_db_path)

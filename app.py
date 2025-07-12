from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_PATH = "elo_ranking.db"

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
    conn.close()
    return data

@app.route("/", methods=["GET", "POST"])
def index():
    search_result = None
    rankings = get_rankings()

    # if request.method == "POST":
    #     name = request.form.get("search_name")
    #     for r in rankings:
    #         if r[1].lower() == name.lower():
    #             search_result = r
    #             break

    return render_template("index.html", rankings=rankings, search_result=search_result)

if __name__ == "__main__":
    app.run(debug=True)

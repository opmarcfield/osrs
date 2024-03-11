from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def get_experience_change(player_name, skill):
    conn = sqlite3.connect('runescape.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT experience FROM player_daily_stats
        WHERE player_name = ? AND skill = ?
        ORDER BY date DESC
        LIMIT 2
    ''', (player_name, skill))
    last_two_days = cursor.fetchall()
    conn.close()
    
    if len(last_two_days) == 2:
        return last_two_days[0][0] - last_two_days[1][0]  # Latest - Previous
    else:
        return 0

@app.route('/playerxp/<player_name>')
def playerxp(player_name):
    # Your existing code to fetch player skills and minigames...
    conn = get_db_connection()
    skills = conn.execute('SELECT * FROM player_skills WHERE player_name = ?', (player_name,)).fetchall()
    minigames = conn.execute('SELECT * FROM player_minigames WHERE player_name = ?', (player_name,)).fetchall()
    
    exp_change = get_experience_change(player_name, "Overall")
    return render_template('player.html', player_name=player_name, skills=skills, minigames=minigames, exp_change=exp_change)


def get_db_connection():
    conn = sqlite3.connect('runescape.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name: row['column_name']
    return conn

@app.route('/')
def index():
    return "Welcome to the OSRS Hiscores Viewer!"

@app.route('/player/<player_name>')
def player(player_name):
    conn = get_db_connection()
    skills = conn.execute('SELECT * FROM player_skills WHERE player_name = ?', (player_name,)).fetchall()
    minigames = conn.execute('SELECT * FROM player_minigames WHERE player_name = ?', (player_name,)).fetchall()
    conn.close()
    return render_template('player.html', player_name=player_name, skills=skills, minigames=minigames)

if __name__ == '__main__':
    app.run(debug=True)

import sqlite3
        
def fetch_skill_data_for_player(player_name):
    conn = sqlite3.connect('runescape.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT skill, rank, level, experience FROM player_skills
        WHERE player_name = ?
    ''', (player_name,))
    
    skills = cursor.fetchall()
    
    conn.close()
    
    if skills:
        print(f"Skills for {player_name}:")
        for skill in skills:
            print(f"Skill: {skill[0]}, Rank: {skill[1]}, Level: {skill[2]}, Experience: {skill[3]}")
    else:
        print(f"No skill data found for {player_name}.")

def fetch_minigame_data_for_player(player_name):
    conn = sqlite3.connect('runescape.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT minigame, rank, score FROM player_minigames
        WHERE player_name = ?
    ''', (player_name,))
    
    minigames = cursor.fetchall()
    
    conn.close()
    
    if minigames:
        print(f"Minigames for {player_name}:")
        for minigame in minigames:
            print(f"Minigame: {minigame[0]}, Rank: {minigame[1]}, Score: {minigame[2]}")
    else:
        print(f"No minigame data found for {player_name}.")
        
#query_player_data("nodle boy")
player_name = "nodle boy"
#fetch_skill_data_for_player(player_name)
fetch_minigame_data_for_player(player_name)
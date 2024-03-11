import sqlite3
import requests

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
        
player_name = "nodle boy"
#fetch_skill_data_for_player(player_name)
#fetch_minigame_data_for_player(player_name)

def fetch_player_data(player_name):
    url = f"https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws?player={player_name}"
    response = requests.get(url)
    if response.status_code == 200:
        raw_data = response.text
        print(f"Raw data for player {player_name}:")
        print(raw_data)
        return raw_data
    else:
        print(f"Error fetching data for player: {player_name}")
        return None
    
fetch_player_data(player_name)
import requests
import sqlite3
import ast
import re
from datetime import datetime

SKILLS = [
    "Overall", "Attack", "Defence", "Strength", "Hitpoints", "Ranged", 
    "Prayer", "Magic", "Cooking", "Woodcutting", "Fletching", "Fishing",
    "Firemaking", "Crafting", "Smithing", "Mining", "Herblore", "Agility", 
    "Thieving", "Slayer", "Farming", "Runecraft", "Hunter", "Construction"
]

# Adjust based on the actual minigames and their order in your data
MINIGAMES = [
    "BH1","BH2","BH3","BH4","BH5","BH6","Clue Scrolls (all)", "Clue Scrolls (beginner)", "Clue Scrolls (easy)", 
    "Clue Scrolls (medium)", "Clue Scrolls (hard)", "Clue Scrolls (elite)", 
    "Clue Scrolls (master)", "LMS - Rank", "PVPARENA", "Soul Wars Zeal", "Rifts closed",
    "Abyssal Sire", "Alchemical Hydra", "Artio", "Barrows", "Bryophyta", 
    "Callisto", "Calvarion", "Cerberus", "Chambers of Xeric", 
    "Chambers of Xeric: Challenge Mode", "Chaos Elemental", "Chaos Fanatic", 
    "Commander Zilyana", "Corporeal Beast", "Crazy Archaeologist", 
    "Dagannoth Prime", "Dagannoth Rex", "Dagannoth Supreme", 
    "Deranged Archaeologist", "Duke Sucellus", "General Graardor", 
    "Giant Mole", "Grotesque Guardians", "Hespori", "Kalphite Queen", 
    "King Black Dragon", "Kraken", "Kree'Arra", "K'ril Tsutsaroth", 
    "Mimic", "Nex", "Nightmare", "Phosani's Nightmare", "Obor", 
    "Phantom Muspah", "Sarachnis", "Scorpia", "Scurrius", "Skotizo", 
    "Spindel", "Tempoross", "The Gauntlet", "The Corrupted Gauntlet", 
    "The Leviathan", "The Whisperer", "Theatre of Blood", 
    "Theatre of Blood: Hard Mode", "Thermonuclear Smoke Devil", 
    "Tombs of Amascut", "Tombs of Amascut: Expert Mode", "TzKal-Zuk", 
    "TzTok-Jad", "Vardorvis", "Venenatis", "Vet'ion", "Vorkath", 
    "Wintertodt", "Zalcano", "Zulrah"
]


def fetch_player_data(player_name):
    url = f"https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws?player={player_name}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error fetching data for player: {player_name}")
        return None


def setup_database():
    conn = sqlite3.connect('runescape.db')
    cursor = conn.cursor()
    
    # Create a table for player skills
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_skills (
            player_name TEXT,
            skill TEXT,
            rank INTEGER,
            level INTEGER,
            experience INTEGER,
            PRIMARY KEY (player_name, skill)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_daily_stats (
            player_name TEXT NOT NULL,
            date DATE NOT NULL,
            skill TEXT NOT NULL,
            experience INTEGER,
            PRIMARY KEY (player_name, date, skill)
        )
    ''')
    

    # Create a table for player minigame scores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_minigames (
            player_name TEXT,
            minigame TEXT,
            rank INTEGER,
            score INTEGER,
            PRIMARY KEY (player_name, minigame)
        )
    ''')

    # Create a table for overall experience
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_overall_experience (
            player_name TEXT,
            overall_experience INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (player_name, timestamp)
        )
    ''')

    conn.commit()
    conn.close()

def parse_and_save_player_data(player_name, data):
    # Split the data into lines
    lines = data.strip().split("\n")
    
    conn = sqlite3.connect('runescape.db')
    cursor = conn.cursor()
    
    # Process skills
    for i, line in enumerate(lines[:24]):  # Assuming the first 24 lines are skills
        parts = line.split(',')
        if len(parts) >= 3:
            rank, level, experience = parts[:3]
            skill = SKILLS[i]
            cursor.execute('''
                INSERT INTO player_skills (player_name, skill, rank, level, experience) 
                VALUES (?, ?, ?, ?, ?) 
                ON CONFLICT(player_name, skill) DO UPDATE SET
                rank = excluded.rank, level = excluded.level, experience = excluded.experience;
            ''', (player_name, skill, rank, level, experience))
            #insert_daily_stats(player_name, skill, experience)
            # Store the overall experience if the skill is "Overall"
            if skill == "Overall":
                overall_experience = int(experience)

    
    if overall_experience is not None:
        cursor.execute('''
            INSERT INTO player_overall_experience (player_name, overall_experience, timestamp) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (player_name, overall_experience))

    # Assuming the remaining lines are minigames
    for i, line in enumerate(lines[24:], start=24):
        parts = line.split(',')
        if len(parts) >= 2:
            rank, score = parts[:2]
            # Calculate the minigame index relative to the start of the minigame entries
            minigame_index = i - 24  # Adjusting for the 24 skills entries before the minigames
            if minigame_index < len(MINIGAMES):
                minigame = MINIGAMES[minigame_index]
                cursor.execute('''
                    INSERT INTO player_minigames (player_name, minigame, rank, score) 
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(player_name, minigame) DO UPDATE SET
                    rank = excluded.rank, score = excluded.score;
                ''', (player_name, minigame, rank, score))

    conn.commit()
    conn.close()
    
def insert_daily_stats(player_name, skill, experience):
    conn = sqlite3.connect('runescape.db')
    cursor = conn.cursor()
    date_today = datetime.now().date().isoformat()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO player_daily_stats (player_name, date, skill, experience) 
            VALUES (?, ?, ?, ?)
        ''', (player_name, date_today, skill, experience))
        conn.commit()
    except sqlite3.IntegrityError:
        print("Duplicate entry detected. Skipping insertion.")
    finally:
        conn.close()
    
def main(player_names):
    setup_database()
    for player_name in player_names:
        raw_data = fetch_player_data(player_name)
        if raw_data:
            # Directly parse and save data; this function now handles both operations
            parse_and_save_player_data(player_name, raw_data)
            print(f"Data for player {player_name} saved successfully.")
        else:
            print(f"Failed to fetch or save data for player {player_name}.")

if __name__ == "__main__":
    player_names = ["nodle boy", "Main Scaper", "Gael L"] # Add more player names as needed
    main(player_names)


import requests
import sqlite3
import ast
import re
import os
import psycopg2
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
    "Clue Scrolls (master)", "LMS - Rank", "PVPARENA", "Soul Wars Zeal", "Rifts closed", "Colosseum Glory","Collections Logged",
    "Abyssal Sire", "Alchemical Hydra", "Amoxliatl", "Araxxor", "Artio", "Barrows", "Bryophyta", 
    "Callisto", "Calvarion", "Cerberus", "Chambers of Xeric", 
    "Chambers of Xeric: Challenge Mode", "Chaos Elemental", "Chaos Fanatic", 
    "Commander Zilyana", "Corporeal Beast", "Crazy Archaeologist", 
    "Dagannoth Prime", "Dagannoth Rex", "Dagannoth Supreme", 
    "Deranged Archaeologist", "Duke Sucellus", "General Graardor", 
    "Giant Mole", "Grotesque Guardians", "Hespori", "Kalphite Queen", 
    "King Black Dragon", "Kraken", "Kree'Arra", "K'ril Tsutsaroth", "Lunar Chests",
    "Mimic", "Nex", "Nightmare", "Phosani's Nightmare", "Obor", 
    "Phantom Muspah", "Sarachnis", "Scorpia", "Scurrius", "Skotizo", "Sol Heredit", 
    "Spindel", "Tempoross", "The Gauntlet", "The Corrupted Gauntlet", "The Hueycoatl", 
    "The Leviathan", "The Royal Titans", "The Whisperer", "Theatre of Blood", 
    "Theatre of Blood: Hard Mode", "Thermonuclear Smoke Devil", 
    "Tombs of Amascut", "Tombs of Amascut: Expert Mode", "TzKal-Zuk", 
    "TzTok-Jad", "Vardorvis", "Venenatis", "Vet'ion", "Vorkath", 
    "Wintertodt", "Yama", "Zalcano", "Zulrah"
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
    DATABASE_URL = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_overall_pvm (
            player_name TEXT,
            overall_raids INTEGER,
            overall_bosses INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (player_name, timestamp)
        )
    ''')

    conn.commit()
    conn.close()

def parse_and_save_player_data(player_name, data):
    # Split the data into lines
    lines = data.strip().split("\n")
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    # Put a dict to store combined scores
    combined_raids = {}
    combined_bosses = {}
    
    # Process skills
    for i, line in enumerate(lines[:24]):  # first 24 lines are skills
        parts = line.split(',')
        if len(parts) >= 3:
            rank, level, experience = parts[:3]
            skill = SKILLS[i]
            cursor.execute('''
                INSERT INTO player_skills (player_name, skill, rank, level, experience) 
                VALUES (%s, %s, %s, %s, %s) 
                ON CONFLICT(player_name, skill) DO UPDATE SET
                rank = excluded.rank, level = excluded.level, experience = excluded.experience;
            ''', (player_name, skill, rank, level, experience))
            # Store the overall experience if the skill is "Overall"
            if skill == "Overall":
                overall_experience = int(experience)

   # Add overall xp history data
    if overall_experience is not None:
        cursor.execute('''
            INSERT INTO player_overall_experience (player_name, overall_experience, timestamp) 
            VALUES (%s, %s, CURRENT_TIMESTAMP)
        ''', (player_name, overall_experience))

    # the remaining lines are minigames
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
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT(player_name, minigame) DO UPDATE SET
                    rank = excluded.rank, score = excluded.score;
                ''', (player_name, minigame, rank, score))
                if minigame in ["Chambers of Xeric", "Chambers of Xeric: Challenge Mode", "Theatre of Blood", 
                                        "Theatre of Blood: Hard Mode", "Tombs of Amascut", "Tombs of Amascut: Expert Mode"]:
                    if minigame not in combined_raids:
                        combined_raids[minigame] = 0
                    combined_raids[minigame] += int(score)
                elif minigame in ["Abyssal Sire", "Alchemical Hydra", "Amoxliatl", "Araxxor", "Artio", "Barrows", "Bryophyta", 
                                    "Callisto", "Calvarion", "Cerberus", "Chaos Elemental", "Chaos Fanatic", 
                                    "Commander Zilyana", "Corporeal Beast", "Crazy Archaeologist", 
                                    "Dagannoth Prime", "Dagannoth Rex", "Dagannoth Supreme", 
                                    "Deranged Archaeologist", "Duke Sucellus", "General Graardor", 
                                    "Giant Mole", "Grotesque Guardians", "Hespori", "Kalphite Queen", 
                                    "King Black Dragon", "Kraken", "Kree'Arra", "K'ril Tsutsaroth", "Lunar Chests",
                                    "Mimic", "Nex", "Nightmare", "Phosani's Nightmare", "Obor", 
                                    "Phantom Muspah", "Sarachnis", "Scorpia", "Scurrius", "Skotizo", "Sol Heredit", 
                                    "Spindel", "Tempoross", "The Gauntlet", "The Corrupted Gauntlet", "The Hueycoatl",
                                    "The Leviathan", "The Royal Titans", "The Whisperer", "Thermonuclear Smoke Devil", 
                                    "TzKal-Zuk", "TzTok-Jad", "Vardorvis", "Venenatis", "Vet'ion", "Vorkath", 
                                    "Wintertodt", "Yama", "Zalcano", "Zulrah"]:
                    if minigame not in combined_bosses:
                        combined_bosses[minigame] = 0
                    combined_bosses[minigame] += int(score)
    
    
    total_raids = sum(combined_raids.values()) if combined_raids else 0
    total_bosses = sum(combined_bosses.values()) if combined_bosses else 0
    cursor.execute('''
        INSERT INTO player_overall_pvm (player_name, overall_raids, overall_bosses, timestamp) 
        VALUES (%s, %s, %s ,CURRENT_TIMESTAMP)
    ''', (player_name, total_raids, total_bosses))

    conn.commit()
    conn.close()
    
def main(player_names):
    setup_database()
    for player_name in player_names:
        raw_data = fetch_player_data(player_name)
        if raw_data:
            # Directly parse and save data
            parse_and_save_player_data(player_name, raw_data)
            print(f"Data for player {player_name} saved successfully.")
        else:
            print(f"Failed to fetch or save data for player {player_name}.")

if __name__ == "__main__":
    # Add all the fashion guildies here, later this can be done in a better way but cba now
    player_names = ["nodle boy", "Main Scaper", "Learner Gael", "Dre1", "GetPurpz", "Dub Tbow", "Hoarseness", "ArtiMeyer", "Pure Tristan", "solo_glow", "interwebfrog", "W0nderbrad", "rocketdoggy", "daddy thor", "daddyy thor", "Logannen", "peajib", "SquatJogsBro", "Se rena", "Sunneh", "X Skimo", "LurpakShakur", "BrutaIX", "0nlySpoonz", "ThePatman", "Kasmacku", "8llu"] 
    main(player_names)


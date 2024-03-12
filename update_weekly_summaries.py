import psycopg2
import os

# SQL command to update weekly_experience_summary
SQL_UPDATE_WEEKLY_EXPERIENCE = """
WITH DateBounds AS (
    SELECT
        player_name,
        DATE_TRUNC('week', timestamp) AS week_start,
        MIN(timestamp) AS first_record,
        MAX(timestamp) AS last_record
    FROM
        player_overall_experience
    GROUP BY
        player_name, DATE_TRUNC('week', timestamp)
),
StartEndExperience AS (
    SELECT
        db.player_name,
        db.week_start,
        first_exp.overall_experience AS start_experience,
        last_exp.overall_experience AS end_experience,
        last_exp.overall_experience - first_exp.overall_experience AS experience_gain
    FROM
        DateBounds db
    JOIN
        player_overall_experience first_exp ON db.player_name = first_exp.player_name AND db.first_record = first_exp.timestamp
    JOIN
        player_overall_experience last_exp ON db.player_name = last_exp.player_name AND db.last_record = last_exp.timestamp
)
INSERT INTO weekly_experience_summary (player_name, week_start, start_experience, end_experience, experience_gain)
SELECT
    player_name,
    week_start AS week_start_date,
    start_experience,
    end_experience,
    experience_gain
FROM
    StartEndExperience
ON CONFLICT (player_name, week_start)
DO UPDATE SET
    start_experience = EXCLUDED.start_experience,
    end_experience = EXCLUDED.end_experience,
    experience_gain = EXCLUDED.experience_gain;

"""

# SQL command to update weekly_pvm_summary
SQL_UPDATE_WEEKLY_PVM = """
WITH DateBounds AS (
    SELECT
        player_name,
        DATE_TRUNC('week', timestamp) AS week_start,
        MIN(timestamp) AS first_record,
        MAX(timestamp) AS last_record
    FROM
        player_overall_pvm
    GROUP BY
        player_name, DATE_TRUNC('week', timestamp)
),
StartEndPvM AS (
    SELECT
        db.player_name,
        db.week_start,
        MIN(pvm.overall_raids) OVER (PARTITION BY db.player_name, db.week_start) AS raids_start,
        MAX(pvm.overall_raids) OVER (PARTITION BY db.player_name, db.week_start) AS raids_end,
        MAX(pvm.overall_raids) OVER (PARTITION BY db.player_name, db.week_start) - MIN(pvm.overall_raids) OVER (PARTITION BY db.player_name, db.week_start) AS raids_increase,
        MIN(pvm.overall_bosses) OVER (PARTITION BY db.player_name, db.week_start) AS bosses_start,
        MAX(pvm.overall_bosses) OVER (PARTITION BY db.player_name, db.week_start) AS bosses_end,
        MAX(pvm.overall_bosses) OVER (PARTITION BY db.player_name, db.week_start) - MIN(pvm.overall_bosses) OVER (PARTITION BY db.player_name, db.week_start) AS bosses_increase
    FROM
        DateBounds db
    JOIN
        player_overall_pvm pvm ON db.player_name = pvm.player_name AND pvm.timestamp BETWEEN db.first_record AND db.last_record
)
INSERT INTO weekly_pvm_summary (player_name, week_start_date, raids_start, raids_end, raids_increase, bosses_start, bosses_end, bosses_increase)
SELECT DISTINCT
    player_name,
    week_start AS week_start_date,
    raids_start,
    raids_end,
    raids_increase,
    bosses_start,
    bosses_end,
    bosses_increase
FROM
    StartEndPvM
ON CONFLICT (player_name, week_start_date)
DO UPDATE SET
    raids_start = EXCLUDED.raids_start,
    raids_end = EXCLUDED.raids_end,
    raids_increase = EXCLUDED.raids_increase,
    bosses_start = EXCLUDED.bosses_start,
    bosses_end = EXCLUDED.bosses_end,
    bosses_increase = EXCLUDED.bosses_increase;
"""

def run_sql_command(conn, sql_command):
    """Executes a given SQL command using the provided connection."""
    with conn.cursor() as cur:
        cur.execute(sql_command)
        conn.commit()
        print("SQL command executed successfully.")

def main():
    # Database connection params - using DATABASE_URL from the environment variable
    DATABASE_URL = os.environ.get('DATABASE_URL')

    try:
        # Connect to your database
        with psycopg2.connect(DATABASE_URL, sslmode='require') as conn:  # Heroku Postgres requires SSL
            # Update weekly experience summary
            run_sql_command(conn, SQL_UPDATE_WEEKLY_EXPERIENCE)
            
            # Update weekly pvm summary
            run_sql_command(conn, SQL_UPDATE_WEEKLY_PVM)
            
    except Exception as e:
        print(f"Failed to update weekly summaries due to: {e}")

if __name__ == "__main__":
    main()

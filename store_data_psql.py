import psycopg2
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

# import db params from soccer_dashboard/config.py
from soccer_dashboard.config import DB_PARAMS

# Load data from Excel files
def load_xlsx_data():
    print("Loading data from Excel files...")
    df = pd.read_excel("./data/combined_data.xlsx")
    df_players = pd.read_excel("./data/players_matches_data.xlsx")
    df_shots = pd.read_excel("./data/shot_events.xlsx")
    df_team_stats = pd.read_excel("./data/team_stats.xlsx")
    return df, df_players, df_shots, df_team_stats

def main():
    # Connect to PostgreSQL
    try:
        engine = create_engine('postgresql://{user}:{password}@{host}:{port}/{database}'.format(**DB_PARAMS))
        print("Database connection successful")
    except Exception as e:
        print("Database connection failed")
        print(e)
        return

    # Read the Excel files
    df, df_players, df_shots, df_team_stats = load_xlsx_data()

    # Write the DataFrame to the SQL database
    df_players.to_sql("players_stats", engine, if_exists="replace", index=False)

    df_shots.to_sql("shots_events", engine, if_exists="replace", index=False)

    df_team_stats.to_sql("team_stats", engine, if_exists="replace", index=False)

    df.to_sql("combined_data", engine, if_exists="replace", index=False)

    print("Data has been loaded to PostgreSQL successfully")

if __name__ == "__main__":
    main()
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import numpy as np
import seaborn as sns
import matplotlib.colors as mcolors
from unidecode import unidecode
from jinja2 import Environment, ChoiceLoader, FileSystemLoader
from IPython.display import HTML
from streamlit_extras.add_vertical_space import add_vertical_space
from pandas.io.formats.style import Styler
import os
import altair as alt
import logging
from mplsoccer import FontManager


import urllib.error
from config import (
    API_KEY,
    EPL_ID,
    EFL_CHAMPIONSHIP_ID,
    EFL_LEAGUE_ONE_ID,
    SEASON,
    fm_rubik,

    FenomenSans,
)

# setup logging
logging.basicConfig(level=logging.INFO)

# Define the path to the template directory and the template file name
template_dir = "/Users/hogan/2425_project/soccer_dashboard/html"
template_file = "template.tpl"

highlight_max_props = "color:crimson; font-weight:bold; background-color:#030021;"
highlight_min_props = "color:#A6FFFE; font-weight:bold; background-color:#100000;"

# make sure they are string
highlight_max_props = str(highlight_max_props)
highlight_min_props = str(highlight_min_props)

# define dictionaries to be used as table styles
table_styles = {
    "font-family": fm_rubik,
    "background-color": "#0d0b17",
    "color": "gainsboro",
    "border-color": "#ffbd6d",
}

table_styles_header = {
    "font-family": fm_rubik,
    "background-color": "#070d1d",
    "color": "floralwhite",
    "border-color": "#ffbd6d",
    "text-align": "center",
}

table_styles_hover = {
    "background-color": "black",
    "color": "floralwhite",
    "border-color": "#ffbd6d",
}

table_styles_blank = {
    "background-color": "transparent",
    "color": "floralwhite",
    "border-color": "#ffbd6d",
    "text-align": "center",
}

table_styles_blank_hover = {
    "background-color": "transparent",
    "color": "black",
    "border-color": "#ffbd6d",
    "text-align": "center",
}

table_styles_blank_level1 = {
    "background-color": "transparent",
    "color": "floralwhite",
    "border-color": "#ffbd6d",
    "text-align": "center",
}

table_styles_blank_level1_hover = {
    "background-color": "transparent",
    "color": "black",
    "border-color": "#ffbd6d",
    "text-align": "center",
}

table_styles_blank_level2 = {
    "background-color": "transparent",
    "color": "floralwhite",
    "border-color": "#ffbd6d",
    "text-align": "center",
}

# PAGE_TITLE_LOCAL = "Soccer Dashboard - Local"
# PAGE_TITLE_PROD = "Soccer Dashboard - Dev"

# PAGE_ICON_LOCAL = ":caution:"
# PAGE_ICON_PROD = ":exclamation:"

# Set the page configuration
st.set_page_config(
    page_title="Soccer Dashboard",
    page_icon=":exclamation:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# st.write(os.sys.executable)


@st.cache_data
def get_team_to_id_mapping():
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookup_all_teams.php?id={EPL_ID}"
    response = requests.get(url)
    data = response.json()
    team_to_id = {team["strTeam"]: team["idTeam"] for team in data["teams"]}
    print(f"team_to_id: {team_to_id}")
    return team_to_id


def get_id_from_team_name(team_to_id, team_name):
    return team_to_id.get(team_name, None)


@st.cache_data
def fetch_player_data(team_name, team_id):
    print("Inside fetch_player_data()")
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/searchplayers.php?t={team_name}"
    response = requests.get(url)
    data = response.json()
    players = data.get("player", [])

    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookup_all_players.php?id={team_id}"
    response = requests.get(url)
    data = response.json()
    players = data.get("player", [])

    for player in players:
        print(f"Fetched player: {player['strPlayer']}")
        honors_url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookuphonours.php?id={player['idPlayer']}"
        honors_response = requests.get(honors_url)
        honors_data = honors_response.json()
        player["trophies"] = (
            len(honors_data.get("honours", [])) if honors_data.get("honours") else 0
        )

        if player.get("idTeam2"):
            team2_url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookupteam.php?id={player['idTeam2']}"
            team2_response = requests.get(team2_url)
            team2_data = team2_response.json()
            if "teams" in team2_data and team2_data["teams"]:
                team2_badge = team2_data["teams"][0]["strTeamBadge"] + "/tiny"
                player["Int"] = team2_badge
            else:
                player["Int"] = (
                    f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookupteam.php?id={player['idTeam']}"
                )
                team_response = requests.get(player["Int"])
                team_data = team_response.json()
                if "teams" in team_data and team_data["teams"]:
                    player["Int"] = team_data["teams"][0]["strTeamBadge"] + "/tiny"
                else:
                    player["Int"] = "\u20DD"
        else:
            player["Int"] = (
                f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookupteam.php?id={player['idTeam']}"
            )
            team_response = requests.get(player["Int"])
            team_data = team_response.json()
            if "teams" in team_data and team_data["teams"]:
                player["Int"] = team_data["teams"][0]["strTeamBadge"] + "/tiny"
            else:
                player["Int"] = "\u20DD"

    return players


@st.cache_data
def get_badges():
    league_ids = [EPL_ID, EFL_CHAMPIONSHIP_ID, EFL_LEAGUE_ONE_ID]
    badges = {}
    player_images = {}

    with requests.Session() as session:
        for league_id in league_ids:
            url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookup_all_teams.php?id={league_id}"
            response = session.get(url)
            if response.status_code != 200:
                print(f"Failed to fetch data for league ID: {league_id}")
                continue
            data = response.json()
            league_badges = {
                team["strTeam"]: team["strTeamBadge"] + "/tiny"
                for team in data.get("teams", [])
            }
            badges.update(league_badges)

            team_ids = [team["idTeam"] for team in data.get("teams", [])]

            for team_id in team_ids:
                url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookup_all_players.php?id={team_id}"
                response = session.get(url)
                if response.status_code != 200:
                    print(f"Failed to fetch data for team ID: {team_id}")
                    continue
                data = response.json()
                team_data = data.get("player", [])
                player_images.update(
                    {
                        player["strPlayer"]: player["strRender"] + "/tiny"
                        for player in team_data
                        if player["strRender"]
                    }
                )

    player_images_df = pd.DataFrame(
        player_images.items(), columns=["Player", "Player_Image"]
    )
    player_images_df["Player"] = player_images_df["Player"].apply(unidecode)
    player_images_dict = player_images_df.set_index("Player")["Player_Image"].to_dict()

    return badges, player_images_dict


@st.cache_data
def feature_engineering(
    df_players_matches, df_players_summary, df_shots, team_badges, player_images_dict
):
    print(f"Columns_in_df_shots: {list(df_shots.columns)}")

    df_players_matches["is_starter"] = df_players_matches["position"].apply(
        lambda x: False if "Sub" in x else True
    )

    df_players_matches["Apps"] = df_players_matches["minutes"].apply(
        lambda x: True if x > 0 else False
    )

    df_players_matches["mins_as_starter"] = df_players_matches.apply(
        lambda row: row["minutes"] if row["is_starter"] else 0, axis=1
    )

    df_players_matches["90s"] = df_players_matches["minutes"] / 90

    agg_dict = {
        "player": "first",
        "team": lambda x: x.mode()[0] if not x.mode().empty else np.nan,
        "position": lambda x: x.mode()[0] if not x.mode().empty else np.nan,
        "starts": "sum",
        "Apps": "sum",
        "minutes_played": "sum",
        "mins_as_starter": "sum",
        "goals": "sum",
        "shots": "sum",
        "xg": "sum",
        "xa": "sum",
        "xg_chain": "sum",
        "xg_buildup": "sum",
        "own_goals": "sum",
        "90s": "sum",
    }

    df_players_matches.rename(
        columns={
            "position": "position",
            "is_starter": "starts",
            "Apps": "Apps",
            "minutes": "minutes_played",
            "mins_as_starter": "mins_as_starter",
            "goals": "goals",
            "shots": "shots",
            "own_goals": "own_goals",
        },
        inplace=True,
    )

    df_players_matches = df_players_matches.groupby(["player_id"], as_index=False).agg(
        agg_dict
    )

    df_players_matches["mins/start"] = (
        df_players_matches["mins_as_starter"] / df_players_matches["starts"]
    )

    numerical_columns = df_players_matches.columns.difference(
        ["player", "team", "position", "xg", "xa", "xg_chain", "xg_buildup"]
    )
    df_players_matches[numerical_columns] = df_players_matches[numerical_columns].apply(
        np.ceil
    )

    df_players_matches["img"] = df_players_matches["team"].map(team_badges)
    df_players_matches["player_image"] = df_players_matches["player"].map(
        player_images_dict
    )

    df_players_merge = pd.merge(
        df_players_matches,
        df_players_summary,
        left_on="player_id",
        right_on="player_id",
        how="left",
        suffixes=("", "_summary"),
    )

    print(f"Columns_in_df_players_merge: {list(df_players_merge.columns)}")
    print(df_players_merge.info())

    df_shots = df_shots.groupby(
        [
            "player_id",
            "player",
            "result",
            "situation",
            "body_part",
            "zone_y",
            "opponent_name",
            "is_home_team",
            "season_id",
            "assist_player",
        ],
        as_index=False,
    ).agg({"shot_id": "count", "xg": "sum"})
    df_shots.rename(columns={"shot_id": "shots"}, inplace=True)

    df_situations = pd.merge(
        df_players_merge,
        df_shots,
        left_on="player_id",
        right_on="player_id",
        how="right",
        suffixes=("", "_shots"),
    )

    print(f"Columns_in_df_situations: {list(df_situations.columns)}")
    print(df_situations.info())

    df_situations = df_situations[
        [
            "img",
            "player",
            "position",
            "90s",
            "season_id",
            "team_id",
            "player_shots",
            "result",
            "situation",
            "body_part",
            "zone_y",
            "opponent_name",
            "is_home_team",
            "season_id_shots",
            "assist_player",
            "shots_shots",
            "xg_shots",
        ]
    ]

    df_situations.columns = [
        "img",
        "player",
        "pos",
        "90s",
        "season_id",
        "team_id",
        "player_shots",
        "result",
        "situation",
        "body_part",
        "zone_y",
        "opponent",
        "is_home_team",
        "season_id_shots",
        "assist_player",
        "shots",
        "xg",
    ]

    df_players_merge = df_players_merge[
        [
            "img",
            "player_image",
            "player",
            "position",
            "starts",
            "Apps",
            "minutes_played",
            "goals",
            "assists",
            "xg",
            "xa",
            "shots",
            "xg_chain",
            "xg_buildup",
            "season",
            "season_id",
            "position_summary",
            "matches",
            "np_goals",
            "np_xg",
            "key_passes",
            "yellow_cards",
            "red_cards",
            "90s",
            "xT_total",
            "xT_perAction",
        ]
    ]

    df_players_merge["KPs/90"] = (
        df_players_merge["key_passes"] / df_players_merge["90s"]
    )
    df_players_merge["Sh/90"] = df_players_merge["shots"] / df_players_merge["90s"]
    df_players_merge["npxG/shot"] = (
        df_players_merge["np_xg"] / df_players_merge["shots"]
    )

    df_players_merge["np:G-xG"] = (
        df_players_merge["np_goals"] - df_players_merge["np_xg"]
    )
    df_players_merge["A-xA"] = df_players_merge["assists"] - df_players_merge["xa"]

    df_players_merge["npxG/shot"] = df_players_merge["npxG/shot"].round(3)
    df_players_merge["KPs/90"] = df_players_merge["KPs/90"].round(3)
    df_players_merge["Sh/90"] = df_players_merge["Sh/90"].round(3)
    df_players_merge["np:G-xG"] = df_players_merge["np:G-xG"].round(3)
    df_players_merge["A-xA"] = df_players_merge["A-xA"].round(3)

    df_players_merge = df_players_merge[
        [
            "img",
            "player_image",
            "player",
            "position",
            "starts",
            "goals",
            "np_goals",
            "xg",
            "np:G-xG",
            "assists",
            "xa",
            "A-xA",
            "shots",
            "xg_chain",
            "xg_buildup",
            "season_id",
            "90s",
            "KPs/90",
            "Sh/90",
            "npxG/shot",
            "xT_total",
            "xT_perAction",
        ]
    ]

    df_players_matches = df_players_matches.sort_values(
        "goals", ascending=False
    ).reset_index(drop=True)

    df_players_merge = df_players_merge.sort_values(
        ["np_goals", "xg"], ascending=False
    ).reset_index(drop=True)

    return df_players_matches, df_players_merge, df_situations


# @st.cache_data
# define a function that adds badges to a df and returns a styled df with badges
def add_badges(df, badges, playerwise=True):
    # Add badges to the df
    df["img"] = df["team"].map(badges)

    # Create a copy of the df
    df_badges = df.copy()

    # Log the columns of the DataFrame for debugging
    st.write("DataFrame columns before processing:", df_badges.columns.tolist())

    # Sort by "Open Play xG" if it exists in the DataFrame
    if "Open Play xG" in df_badges.columns:
        df_badges = df_badges.sort_values("Open Play xG", ascending=False)

    # Determine the order of the columns
    if playerwise:
        if "assist_player" in df_badges.columns:
            columns_order = ["img", "assist_player", "Open Play xG"] + [
                col
                for col in df_badges.columns
                if col
                not in ["img", "assist_player", "team", "Open Play xG"]
            ]
        else:
            columns_order = ["img", "player", "position", "Open Play xG"] + [
                col
                for col in df_badges.columns
                if col not in ["img", "player", "position", "team", "Open Play xG"]
            ]
        if "matches" in df_badges.columns:
            columns_order.insert(4, "matches")  # Insert matches column if it exists
    else:
        columns_order = ["img", "team", "Open Play xG"] + [
            col
            for col in df_badges.columns
            if col not in ["img", "team", "Open Play xG"]
        ]

    # Ensure the required columns are in the DataFrame
    missing_columns = [col for col in columns_order if col not in df_badges.columns]
    if missing_columns:
        st.error(f"Columns missing in DataFrame: {missing_columns}")
        return df_badges  # Return the DataFrame without processing

    # Reorder the columns
    df_badges = df_badges[columns_order]

    # Format the badge column
    df_badges["img"] = df_badges["img"].apply(
        lambda x: f'<img src="{x}" style="width: 32px; height: 32px;">'
    )

    # Get numerical and categorical columns
    numerical_columns = df_badges.select_dtypes(include="number").columns
    categorical_columns = df_badges.select_dtypes(exclude="number").columns

    # Create a styled df with badges
    styled_df_badges = (
        df_badges.style.set_properties(
            subset=categorical_columns.difference(["img", "position"]),
            **{
                "text-align": "left",
                "font-family": "Arial, sans-serif",
                "background-color": "#0d0b17",
                "color": "gainsboro",
                "border-color": "#ffbd6d",
            },
        )
        .set_properties(
            subset=numerical_columns,
            **{
                "text-align": "center",
                "font-family": "Arial, sans-serif",
                "background-color": "#0d0b17",
                "color": "gainsboro",
                "border-color": "#ffbd6d",
            },
        )
        .set_properties(
            subset=["img"],
            **{
                "text-align": "center",
                "font-family": "Arial, sans-serif",
                "background-color": "#0d0b17",
                "color": "gainsboro",
                "border-color": "#ffbd6d",
            },
        )
    )

    if "position" in df_badges.columns:
        styled_df_badges = styled_df_badges.set_properties(
            subset=["position"],
            **{
                "text-align": "center",
                "font-family": "Arial, sans-serif",
                "background-color": "#0d0b17",
                "color": "gainsboro",
                "border-color": "#ffbd6d",
            },
        )

    styled_df_badges = (
        styled_df_badges.set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        ("font-family", "Arial, sans-serif"),
                        ("background-color", "#070d1d"),
                        ("color", "floralwhite"),
                        ("border-color", "#ffbd6d"),
                        ("text-align", "center"),
                        ("border-weight", "3px"),
                    ],
                },
                {
                    "selector": "td:hover",
                    "props": [
                        ("background-color", "black"),
                        ("color", "gold"),
                        ("border-color", "#ffbd6d"),
                    ],
                },
                {
                    "selector": ".blank.level0",
                    "props": [
                        ("background-color", "black"),
                        ("color", "floralwhite"),
                        ("border-color", "#ffbd6d"),
                        ("text-align", "center"),
                    ],
                },
                {
                    "selector": ".blank.hover",
                    "props": [
                        ("background-color", "black"),
                        ("color", "black"),
                        ("border-color", "#ffbd6d"),
                        ("text-align", "center"),
                    ],
                },
            ]
        )
        # Highlight the maximum value in each column
        .highlight_max(
            subset=numerical_columns,
            props="color: green; font-weight: bold;",
        )
        # Highlight the minimum value in each column
        .highlight_min(
            subset=numerical_columns,
            props="color: red; font-weight: bold;",
        )
        .format(subset=numerical_columns, formatter="{:.2f}")
        .hide(axis="index")
    )

    return styled_df_badges


def transform_shots_data(df_shots):
    print(f"Columns_in_df_shots: {list(df_shots.columns)}")

    # fill nans in assist_player with 'Self'
    df_shots["assist_player"].fillna("Self", inplace=True)

    # groupby player, result, situation, body_part, zone_y, opponent_name, h_a, season_id, assist_player and count the number of shot_id, sum xg_shots
    df_shots = df_shots.groupby(
        [
            "player_id",
            "player",
            "result",
            "situation",
            "body_part",
            "zone_y",
            "opponent_name",
            "is_home_team",
            "season_id",
            # "assist_player",
        ],
        as_index=False,
    ).agg({"shot_id": "count", "xg": "sum"})
    df_shots.rename(columns={"shot_id": "shots"}, inplace=True)

    return df_shots

@st.cache_data
def transform_shot_data(df_shots):
    # Calculate the total xG, the count of shots, and the count of unique games for each group
    grouped_data = (
        df_shots.groupby(
            ["player", "team", "position", "situation", "body_part", "zone_y", "result"]
        )
        .agg(
            total_xg=pd.NamedAgg(column="xg", aggfunc="sum"),
            shot_count=pd.NamedAgg(column="xg", aggfunc="count"),
        )
        .reset_index()
    )

    # Calculate matches per player, team, and position
    matches_data = (
        df_shots.groupby(["player", "team", "position"])
        .agg(matches=pd.NamedAgg(column="game", aggfunc="nunique"))
        .reset_index()
    )

    # Calculate the per shot xG
    grouped_data["per_shot_xg"] = grouped_data["total_xg"] / grouped_data["shot_count"]

    # Pivot the data for situations
    situation_pivot = grouped_data.pivot_table(
        index=["player", "team", "position"],
        columns="situation",
        values="per_shot_xg",
        fill_value=0,
    )
    situation_pivot.columns = [f"{col} xG" for col in situation_pivot.columns]
    situation_pivot.reset_index(inplace=True)

    # Pivot the data for body parts
    body_part_pivot = grouped_data.pivot_table(
        index=["player", "team", "position"],
        columns="body_part",
        values="per_shot_xg",
        fill_value=0,
    )
    body_part_pivot.columns = [f"{col} xG" for col in body_part_pivot.columns]
    body_part_pivot.reset_index(inplace=True)

    # Pivot the data for zone_y
    zone_y_pivot = grouped_data.pivot_table(
        index=["player", "team", "position"],
        columns="zone_y",
        values="per_shot_xg",
        fill_value=0,
    )
    zone_y_pivot.columns = [f"{col} xG" for col in zone_y_pivot.columns]
    zone_y_pivot.reset_index(inplace=True)

    # Pivot the data for result
    result_pivot = grouped_data.pivot_table(
        index=["player", "team", "position"],
        columns="result",
        values="per_shot_xg",
        fill_value=0,
    )
    result_pivot.columns = [f"{col} xG" for col in result_pivot.columns]
    result_pivot.reset_index(inplace=True)

    # Merge the pivot tables on player, team, and position
    playerwise_result = situation_pivot.merge(
        body_part_pivot, on=["player", "team", "position"], how="outer"
    )
    playerwise_result = playerwise_result.merge(
        zone_y_pivot, on=["player", "team", "position"], how="outer"
    )

    # Merge the result_pivot with playerwise_result
    playerwise_result = playerwise_result.merge(
        result_pivot, on=["player", "team", "position"], how="outer"
    )

    # Add matches to the playerwise_result
    playerwise_result = playerwise_result.merge(
        matches_data, on=["player", "team", "position"], how="left"
    )

    # Calculate teamwise data
    team_grouped_data = (
        df_shots.groupby(["team", "situation", "body_part", "zone_y", "result"])
        .agg(
            total_xg=pd.NamedAgg(column="xg", aggfunc="sum"),
            shot_count=pd.NamedAgg(column="xg", aggfunc="count"),
        )
        .reset_index()
    )

    # Calculate the per shot xG
    team_grouped_data["per_shot_xg"] = (
        team_grouped_data["total_xg"] / team_grouped_data["shot_count"]
    )

    # Pivot the data for situations
    team_situation_pivot = team_grouped_data.pivot_table(
        index=["team"],
        columns="situation",
        values="per_shot_xg",
        fill_value=0,
    )
    team_situation_pivot.columns = [f"{col} xG" for col in team_situation_pivot.columns]
    team_situation_pivot.reset_index(inplace=True)

    # Pivot the data for body parts
    team_body_part_pivot = team_grouped_data.pivot_table(
        index=["team"],
        columns="body_part",
        values="per_shot_xg",
        fill_value=0,
    )
    team_body_part_pivot.columns = [f"{col} xG" for col in team_body_part_pivot.columns]
    team_body_part_pivot.reset_index(inplace=True)

    # Pivot the data for zone_y
    team_zone_y_pivot = team_grouped_data.pivot_table(
        index=["team"],
        columns="zone_y",
        values="per_shot_xg",
        fill_value=0,
    )
    team_zone_y_pivot.columns = [f"{col} xG" for col in team_zone_y_pivot.columns]
    team_zone_y_pivot.reset_index(inplace=True)

    # Pivot the data for result
    team_result_pivot = team_grouped_data.pivot_table(
        index=["team"],
        columns="result",
        values="per_shot_xg",
        fill_value=0,
    )
    team_result_pivot.columns = [f"{col} xG" for col in team_result_pivot.columns]
    team_result_pivot.reset_index(inplace=True)

    # Merge the pivot tables on team
    teamwise_result = team_situation_pivot.merge(
        team_body_part_pivot, on="team", how="outer"
    )
    teamwise_result = teamwise_result.merge(team_zone_y_pivot, on="team", how="outer")

    # Merge the result_pivot with teamwise_result
    teamwise_result = teamwise_result.merge(team_result_pivot, on="team", how="outer")

    return playerwise_result, teamwise_result

@st.cache_data
def transform_shot_data_assist(df_shots):
    required_columns = ["assist_player", "team", "situation", "body_part", "zone_y", "result", "xg", "game"]
    
    # Check if all required columns are in the DataFrame
    missing_columns = [col for col in required_columns if col not in df_shots.columns]
    if missing_columns:
        logging.error(f"Missing columns in DataFrame: {missing_columns}")
        return None, None

    # Calculate the total xG, the count of shots, and the count of unique games for each group
    grouped_data = (
        df_shots.groupby(
            ["assist_player", "team", "situation", "body_part", "zone_y", "result"]
        )
        .agg(
            total_xg=pd.NamedAgg(column="xg", aggfunc="sum"),
            shot_count=pd.NamedAgg(column="xg", aggfunc="count"),
        )
        .reset_index()
    )

    # Calculate matches per assist_player and team
    matches_data = (
        df_shots.groupby(["assist_player", "team"])
        .agg(matches=pd.NamedAgg(column="game", aggfunc="nunique"))
        .reset_index()
    )

    # Calculate the per shot xG
    grouped_data["per_shot_xg"] = grouped_data["total_xg"] / grouped_data["shot_count"]

    # Pivot the data for situations
    situation_pivot = grouped_data.pivot_table(
        index=["assist_player", "team"],
        columns="situation",
        values="per_shot_xg",
        fill_value=0,
    )
    situation_pivot.columns = [f"{col} xG" for col in situation_pivot.columns]
    situation_pivot.reset_index(inplace=True)

    # Pivot the data for body parts
    body_part_pivot = grouped_data.pivot_table(
        index=["assist_player", "team"],
        columns="body_part",
        values="per_shot_xg",
        fill_value=0,
    )
    body_part_pivot.columns = [f"{col} xG" for col in body_part_pivot.columns]
    body_part_pivot.reset_index(inplace=True)

    # Pivot the data for zone_y
    zone_y_pivot = grouped_data.pivot_table(
        index=["assist_player", "team"],
        columns="zone_y",
        values="per_shot_xg",
        fill_value=0,
    )
    zone_y_pivot.columns = [f"{col} xG" for col in zone_y_pivot.columns]
    zone_y_pivot.reset_index(inplace=True)

    # Pivot the data for result
    result_pivot = grouped_data.pivot_table(
        index=["assist_player", "team"],
        columns="result",
        values="per_shot_xg",
        fill_value=0,
    )
    result_pivot.columns = [f"{col} xG" for col in result_pivot.columns]
    result_pivot.reset_index(inplace=True)

    # Merge the pivot tables on assist_player and team
    assistwise_result = situation_pivot.merge(
        body_part_pivot, on=["assist_player", "team"], how="outer"
    )
    assistwise_result = assistwise_result.merge(
        zone_y_pivot, on=["assist_player", "team"], how="outer"
    )

    # Merge the result_pivot with assistwise_result
    assistwise_result = assistwise_result.merge(
        result_pivot, on=["assist_player", "team"], how="outer"
    )

    # Add matches to the assistwise_result
    assistwise_result = assistwise_result.merge(
        matches_data, on=["assist_player", "team"], how="left"
    )

    # Calculate teamwise data
    team_grouped_data = (
        df_shots.groupby(["team", "situation", "body_part", "zone_y", "result"])
        .agg(
            total_xg=pd.NamedAgg(column="xg", aggfunc="sum"),
            shot_count=pd.NamedAgg(column="xg", aggfunc="count"),
        )
        .reset_index()
    )

    # Calculate the per shot xG
    team_grouped_data["per_shot_xg"] = (
        team_grouped_data["total_xg"] / team_grouped_data["shot_count"]
    )

    # Pivot the data for situations
    team_situation_pivot = team_grouped_data.pivot_table(
        index=["team"],
        columns="situation",
        values="per_shot_xg",
        fill_value=0,
    )
    team_situation_pivot.columns = [f"{col} xG" for col in team_situation_pivot.columns]
    team_situation_pivot.reset_index(inplace=True)

    # Pivot the data for body parts
    team_body_part_pivot = team_grouped_data.pivot_table(
        index=["team"],
        columns="body_part",
        values="per_shot_xg",
        fill_value=0,
    )
    team_body_part_pivot.columns = [f"{col} xG" for col in team_body_part_pivot.columns]
    team_body_part_pivot.reset_index(inplace=True)

    # Pivot the data for zone_y
    team_zone_y_pivot = team_grouped_data.pivot_table(
        index=["team"],
        columns="zone_y",
        values="per_shot_xg",
        fill_value=0,
    )
    team_zone_y_pivot.columns = [f"{col} xG" for col in team_zone_y_pivot.columns]
    team_zone_y_pivot.reset_index(inplace=True)

    # Pivot the data for result
    team_result_pivot = team_grouped_data.pivot_table(
        index=["team"],
        columns="result",
        values="per_shot_xg",
        fill_value=0,
    )
    team_result_pivot.columns = [f"{col} xG" for col in team_result_pivot.columns]
    team_result_pivot.reset_index(inplace=True)

    # Merge the pivot tables on team
    teamwise_result = team_situation_pivot.merge(
        team_body_part_pivot, on="team", how="outer"
    )
    teamwise_result = teamwise_result.merge(team_zone_y_pivot, on="team", how="outer")

    # Merge the result_pivot with teamwise_result
    teamwise_result = teamwise_result.merge(team_result_pivot, on="team", how="outer")

    return assistwise_result, teamwise_result

@st.cache_data
# plot home v away goals for all teams data using hexbin plot
def plot_home_away_goals(df):
    # Size of the hexbins
    size = 15
    # Count of distinct x features
    xFeaturesCount = df['home_goals'].nunique()
    # Count of distinct y features
    yFeaturesCount = df['away_goals'].nunique()
    # Name of the x field
    xField = 'home_goals'
    # Name of the y field
    yField = 'away_goals'

    # the shape of a hexagon
    hexagon = "M0,-2.3094010768L2,-1.1547005384 2,1.1547005384 0,2.3094010768 -2,1.1547005384 -2,-1.1547005384Z"

    # Calculate the total number of matches
    total_matches = df.shape[0]

    # Calculate the number of matches for each combination of home and away goals
    df['matches'] = df.groupby(['home_goals', 'away_goals'])['home_goals'].transform('count')

    # Calculate the percentage of total for each bin
    df['percentage'] = df['matches'] / total_matches * 100

    chart = alt.Chart(df).mark_rect().encode(
        alt.X('xFeaturePos:Q', title='Home Goals', axis=alt.Axis(values=list(range(int(df['home_goals'].max()+1))), grid=False, tickOpacity=0, domainOpacity=0)),
        alt.Y('yFeaturePos:O', title='Away Goals', scale=alt.Scale(domain=list(range(int(df['away_goals'].max()), -1, -1))), axis=alt.Axis(values=list(range(int(df['away_goals'].max()+1))), labelPadding=20, tickOpacity=0, domainOpacity=0)),
        stroke=alt.value('black'),
        strokeWidth=alt.value(0.2),
        fill=alt.Color('count():Q', title="Number of Matches", scale=alt.Scale(scheme='tableau10')),
        tooltip=[alt.Tooltip('home_goals:Q', title='Home Goals'), alt.Tooltip('away_goals:Q', title='Away Goals'), alt.Tooltip('count():Q', title='Number of Matches'), alt.Tooltip('percentage:Q', title='Percentage of Total')]
    ).transform_calculate(
        xFeaturePos='datum.' + xField,
        yFeaturePos='datum.' + yField
    ).properties(
        width=600,  # Increase the width
        height=600  # Increase the height
    )
    chart = alt.Chart(df).mark_rect().encode(
        alt.X('home_goals:Q', title='Home Goals').bin(maxbins=xFeaturesCount),
        alt.Y('away_goals:Q', title='Away Goals').bin(maxbins=yFeaturesCount),
        alt.Color('count():Q', title="Number of Matches").scale(scheme='viridis'),
        tooltip=[alt.Tooltip('home_goals:Q', title='Home Goals'), alt.Tooltip('away_goals:Q', title='Away Goals'), alt.Tooltip('count():Q', title='Number of Matches')]
    ).properties(
        width=600,
        height=400
    )

    # Convert the 'date' column to datetime
    df['date'] = pd.to_datetime(df['date'])

    # Create a new column for the day of the week
    df['day_of_week'] = df['date'].dt.day_name()

    # Create a month column
    df['month'] = df['date'].dt.month_name()

    # Create a new column for the total goals scored
    df['total_goals'] = df['home_goals'] + df['away_goals']

    # Put the data in order of the month from August to May and seasons so that the most recent season is at the top of the bar
    df['month'] = pd.Categorical(df['month'], categories=['August', 'September', 'October', 'November', 'December', 'January', 'February', 'March', 'April', 'May'], ordered=True)
    df['season_id'] = pd.Categorical(df['season_id'], categories=df['season_id'].unique(), ordered=True)

    # Calculate the total number of matches for each combination of 'month', 'day_of_week' and 'season_id'
    df['total_matches'] = df.groupby(['month', 'day_of_week', 'season_id'])['total_goals'].transform('size')

    # Calculate the number of unique seasons for each combination of 'month' and 'day_of_week'
    df['unique_seasons'] = df.groupby(['month', 'day_of_week'])['season_id'].transform('nunique')

    # Calculate the average total goals per match for each combination of 'month', 'day_of_week' and 'season_id'
    avg_goals_month_day_season = df.groupby(['month', 'day_of_week', 'season_id']).agg({'total_goals': 'mean', 'total_matches': 'first', 'unique_seasons': 'first'}).reset_index().round(2)
    avg_goals_month_day_season.columns = ['month', 'day_of_week', 'season_id', 'avg_total_goals', 'total_matches', 'unique_seasons']

    # Update the tooltip in chart2 to include total matches
    chart2 = (
        alt.Chart(avg_goals_month_day_season)
        .mark_rect()
        .encode(
            alt.X(
                "month:N",
                title="Month",
                sort=alt.EncodingSortField(field="date", op="min"),
            ),
            alt.Y("day_of_week:N", title="Day of the Week"),
            alt.Color(
                "avg_total_goals:Q",
                title="Average Total Goals",
                scale=alt.Scale(scheme="viridis"),
            ),
            tooltip=[
                alt.Tooltip("total_matches:Q", title="Total Matches"),
                alt.Tooltip("avg_total_goals:Q", title="Average Total Goals"),
                alt.Tooltip("unique_seasons:Q", title="Unique Seasons"),
            ],
        )
        .properties(width=600, height=400)
    )

    return chart, chart2

def render_player_table(players, player_wages):
    print("Inside render_player_table()")
    df_players_matches = pd.DataFrame(players)

    print(f"df_players_matches columns: {df_players_matches.columns}")
    print(f"player_wages columns: {player_wages.columns}")

    df_players_matches = df_players_matches[
        [
            "strCutout",
            "strPlayer",
            "strPosition",
            "trophies",
            "dateBorn",
            "Int",
            "strNationality",
            "strNumber",
            "strHeight",
        ]
    ]
    df_players_matches.columns = [
        "Player",
        "Name",
        "Position",
        "Trophies",
        "Age",
        "Int",
        "Nation",
        "Number",
        "Height",
    ]

    print(f"\n\nUnique players in df_players_matches: {df_players_matches['Name'].unique()}")
    # print(f"\n\nUnique players in player_wages: {player_wages['name'].unique()}")

    # Convert trophies to int
    df_players_matches["Trophies"] = df_players_matches["Trophies"].astype(int)

    # Calculate age from birth date
    df_players_matches["Age"] = pd.to_datetime(df_players_matches["Age"]).apply(
        lambda x: pd.Timestamp.now().year - x.year
    )

    # Apply unidecode to the player names for consistent merging
    df_players_matches["Name"] = df_players_matches["Name"].apply(unidecode)

    # Merge player data with player wages
    df_players_wages = pd.merge(
        df_players_matches,
        player_wages,
        left_on="Name",
        right_on="name",
        how="left",
    )

    print(f"\n\nAfter merge...\n\ndf_players_wages columns: {df_players_wages.columns}")

    # print unique players in df_players_wages
    print(f"Unique players in df_players_wages: {df_players_wages['Name'].unique()}")

    # Rename columns in df_players_wages
    df_players_wages = df_players_wages[
        [
            "Player",
            "Name",
            "Position",
            "Trophies",
            "Age",
            "Int",
            "Nation",
            "Number",
            "weekly_gross_gbp",
            "years",
            "release_gbp",
        ]
    ]
    df_players_wages.columns = [
        "Player",
        "Name",
        "Position",
        "Trophies",
        "Age",
        "Int",
        "Nation",
        "Number",
        "WklyWages",
        "YrsLeft",
        "Release",
    ]

    # Sort by trophies descending
    df_players_matches = df_players_matches.sort_values("Trophies", ascending=False).reset_index(
        drop=True
    )

    # Sort df_players_wages by Wages
    df_players_wages = df_players_wages.sort_values(
        "WklyWages", ascending=False
    ).reset_index(drop=True)

    # Fill nan values with NA
    df_players_wages.fillna("NA", inplace=True)

    # If there is Manager in position, move it to the top
    if "Manager" in df_players_matches["Position"].values:
        manager = df_players_matches[df_players_matches["Position"] == "Manager"]
        df_players_matches = df_players_matches[df_players_matches["Position"] != "Manager"]
        df_players_matches = pd.concat([manager, df_players_matches]).reset_index(drop=True)

    # If there is Manager in position, move it to the top
    if "Manager" in df_players_wages["Position"].values:
        manager_wages = df_players_wages[df_players_wages["Position"] == "Manager"]
        df_players_wages = df_players_wages[df_players_wages["Position"] != "Manager"]
        df_players_wages = pd.concat([manager_wages, df_players_wages]).reset_index(
            drop=True
        )

    # Format the wage columns to include currency symbol and commas
    df_players_wages["WklyWages"] = df_players_wages["WklyWages"].apply(
        lambda x: f"£{x:,.2f}" if x != "NA" else "NA"
    )
    df_players_wages["Release"] = df_players_wages["Release"].apply(
        lambda x: f"£{x:,.2f}" if x != "NA" else "NA"
    )
    df_players_wages["YrsLeft"] = df_players_wages["YrsLeft"].apply(
        lambda x: f"{x}" if x != "NA" else "NA"
    )

    df_players_matches["Player"] = df_players_matches.apply(
        lambda row: f'<img src="{row["Player"]}" width="50">', axis=1
    )

    df_players_wages["Player"] = df_players_wages.apply(
        lambda row: f'<img src="{row["Player"]}" width="50">', axis=1
    )

    df_players_matches["Int"] = df_players_matches.apply(
        lambda row: (f'<img src="{row["Int"]}" width="32">' if row["Int"] else ""),
        axis=1,
    )

    df_players_wages["Int"] = df_players_wages.apply(
        lambda row: (f'<img src="{row["Int"]}" width="32">' if row["Int"] else ""),
        axis=1,
    )

    styled_df_players_matches = (
        df_players_matches.style.set_properties(
            subset=["Name", "Position", "Nation"],
            **{
                "text-align": "left",
                "font-family": FenomenSans,
                "background-color": "#0d0b17",
                "color": "gainsboro",
                "border-color": "#ffbd6d",
            },
        )
        .set_properties(
            subset=df_players_matches.columns.difference(["Name", "Position", "Nation"]),
            **{
                "text-align": "center",
                "font-family": FenomenSans,
                "background-color": "#0d0b17",
                "color": "gainsboro",
                "border-color": "#ffbd6d",
            },
        )
        .set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        ("font-family", fm_rubik),
                        ("background-color", "#070d1d"),
                        ("color", "floralwhite"),
                        ("border-color", "#ffbd6d"),
                        ("text-align", "center"),
                        ("border-weight", "3px"),
                    ],
                },
                {
                    "selector": "td:hover",
                    "props": [
                        ("background-color", "black"),
                        ("color", "gold"),
                        ("border-color", "#ffbd6d"),
                    ],
                },
                {
                    "selector": ".blank.level0",
                    "props": [
                        ("background-color", "black"),
                        ("color", "floralwhite"),
                        ("border-color", "#ffbd6d"),
                        ("text-align", "center"),
                    ],
                },
                {
                    "selector": ".blank.hover",
                    "props": [
                        ("background-color", "black"),
                        ("color", "black"),
                        ("border-color", "#ffbd6d"),
                        ("text-align", "center"),
                    ],
                },
            ]
        )
    )

    styled_df_players_wages = (
        df_players_wages.style.set_properties(
            subset=["Name", "Position", "Nation"],
            **{
                "text-align": "left",
                "font-family": FenomenSans,
                "background-color": "#0d0b17",
                "color": "gainsboro",
                "border-color": "#ffbd6d",
            },
        )
        .set_properties(
            subset=df_players_wages.columns.difference(["Name", "Position", "Nation"]),
            **{
                "text-align": "center",
                "font-family": FenomenSans,
                "background-color": "#0d0b17",
                "color": "gainsboro",
                "border-color": "#ffbd6d",
            },
        )
        .set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        ("font-family", fm_rubik),
                        ("background-color", "#070d1d"),
                        ("color", "floralwhite"),
                        ("border-color", "#ffbd6d"),
                        ("text-align", "center"),
                        ("border-weight", "3px"),
                    ],
                },
                {
                    "selector": "td:hover",
                    "props": [
                        ("background-color", "black"),
                        ("color", "gold"),
                        ("border-color", "#ffbd6d"),
                    ],
                },
                {
                    "selector": ".blank.level0",
                    "props": [
                        ("background-color", "black"),
                        ("color", "floralwhite"),
                        ("border-color", "#ffbd6d"),
                        ("text-align", "center"),
                    ],
                },
                {
                    "selector": ".blank.hover",
                    "props": [
                        ("background-color", "black"),
                        ("color", "black"),
                        ("border-color", "#ffbd6d"),
                        ("text-align", "center"),
                    ],
                },
            ]
        )
    )

    return styled_df_players_matches, styled_df_players_wages


# Fetch data from the API
@st.cache_data
def get_data():
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookuptable.php?l={EPL_ID}&s={SEASON}"
    response = requests.get(url)
    data = response.json()
    return data["table"]


# we will get all strTeamBadge media from api here: https://www.thesportsdb.com/api/v1/json/60130162/lookup_all_teams.php?id=4328 ,id= and we will get the /tiny/ strTeamBadge such as https://www.thesportsdb.com/images/media/team/badge/uyhbfe1612467038.png/tiny
# Get badges from API


# @st.cache_data
# def load_player_data(filter=None):
#     try:
#         # Determine the base path
#         base_path = os.path.dirname(
#             os.path.abspath(__file__)
#         )  # Get the current script directory
#         data_path = os.path.join(base_path, "../data")  # Local data path

#         if not os.path.exists(
#             data_path
#         ):  # If not in local environment, use production path
#             data_path = "/mnt/src/2425_project/data"

#         # Construct the file paths using the data path
#         df1 = pd.read_csv(os.path.join(data_path, "combined_data.csv"))
#         df_players_matches = pd.read_csv(
#             os.path.join(data_path, "players_matches_data.csv")
#         )
#         df_players_summary = pd.read_csv(
#             os.path.join(data_path, "players_summary_data.csv")
#         )
#         df_shots = pd.read_csv(os.path.join(data_path, "shot_events.csv"))
#         df_team_stats = pd.read_csv(os.path.join(data_path, "team_stats.csv"))
#         df_player_wages = pd.read_csv(
#             os.path.join(data_path, "premier_league_salaries.csv")
#         )
#         df_xT = pd.read_csv(os.path.join(data_path, "players_xT_data.csv"))

#         # Print df_team_stats columns for debugging
#         print(f"Columns_in_df_team_stats:\n\n{df_team_stats.columns}")

#         # Groupby team df_players_summary by team and season
#         df_summary_teams = df_players_summary.groupby(
#             ["team", "season_id"], as_index=False
#         ).sum()

#         # If filter is True, filter the df_player_wages data for the 2023 season
#         if filter:
#             df_player_wages = df_player_wages[df_player_wages["season"] == 2023]
#             df_summary_teams = df_summary_teams[df_summary_teams["season_id"] == 2023]


#         return (
#             df1,
#             df_players_matches,
#             df_players_summary,
#             df_summary_teams,
#             df_shots,
#             df_team_stats,
#             df_player_wages,
#             df_xT
#         )
#     except FileNotFoundError as e:
#         print(f"FileNotFoundError caught: {e}")
#         logging.exception("Exception occurred")
#         return None, None, None, None, None, None, None, None


@st.cache_data
def load_player_data(filter=None):
    try:
        # Determine the base path
        current_path = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(os.path.join(current_path, "../data")):
            base_path = os.path.join(current_path, "../data")  # Local environment
        else:
            base_path = "/mnt/src/2425_project/data"  # Deployed environment

        # Construct the file paths using the base path
        df1 = pd.read_csv(os.path.join(base_path, "combined_data.csv"))
        df_players_matches = pd.read_csv(
            os.path.join(base_path, "players_matches_data.csv")
        )
        df_players_summary = pd.read_csv(
            os.path.join(base_path, "players_summary_data.csv")
        )
        df_shots = pd.read_csv(os.path.join(base_path, "shot_events.csv"))
        df_team_stats = pd.read_csv(os.path.join(base_path, "team_stats.csv"))
        df_player_wages = pd.read_csv(
            os.path.join(base_path, "premier_league_salaries.csv")
        )
        df_xT = pd.read_csv(os.path.join(base_path, "players_xT_data.csv"))

        # Groupby team df_players_summary by team and season
        df_summary_teams = df_players_summary.groupby(
            ["team", "season_id"], as_index=False
        ).sum()

        def get_most_common_position(positions):
            filtered_positions = positions[positions != "Sub"]
            if filtered_positions.empty:
                return "Sub"
            return filtered_positions.value_counts().index[0]

        # Create a dictionary that maps player_id to the most common position
        player_positions = df_players_matches.groupby("player_id")["position"].agg(get_most_common_position)

        # Add position to the df_shots DataFrame
        df_shots = df_shots.merge(
            player_positions, left_on="player_id", right_index=True, how="left"
        )

        # If filter is True, filter the df_player_wages data for the 2023 season
        if filter:
            df_player_wages = df_player_wages[df_player_wages["season"] == 2023]
            df_summary_teams = df_summary_teams[df_summary_teams["season_id"] == 2023]

        return (
            df1,
            df_players_matches,
            df_players_summary,
            df_summary_teams,
            df_shots,
            df_team_stats,
            df_player_wages,
            df_xT,
            player_positions
        )
    except FileNotFoundError as e:
        logging.exception("Exception occurred")
        return None, None, None, None, None, None, None, None, None


# @st.cache_data
def process_team_stats(df, df_team_summary, season_range, team_badges):
    print("Inside process_team_stats()")

    # Convert team and season columns to consistent types
    df["season_id"] = df["season_id"].astype(int)
    df_team_summary["team"] = df_team_summary["team"].astype(str)
    df_team_summary["season_id"] = df_team_summary["season_id"].astype(int)

    # Filter data based on the selected season range
    df = df[(df["season_id"] >= season_range[0]) & (df["season_id"] <= season_range[1])]
    df_team_summary = df_team_summary[
        (df_team_summary["season_id"] >= season_range[0])
        & (df_team_summary["season_id"] <= season_range[1])
    ]

    # Home DataFrame
    home_df = df[
        [
            "match_id",
            "season",
            "game",
            "league_id",
            "season_id",
            "game_id",
            "date",
            "home_team",
            "home_points",
            "home_expected_points",
            "home_goals",
            "home_xg",
            "home_np_xg",
            "home_np_xg_difference",
            "away_goals",
            "home_ppda",
            "away_ppda",
            "home_deep_completions",
            "away_deep_completions",
        ]
    ].rename(
        columns={
            "home_team": "team",
            "home_points": "points",
            "home_expected_points": "xPoints",
            "home_goals": "goals",
            "away_goals": "GA",
            "home_xg": "xG",
            "home_np_xg": "npxG",
            "home_np_xg_difference": "npxGD",
            "home_ppda": "ppda",
            "away_ppda": "ppda_against",
            "home_deep_completions": "deep_completions",
            "away_deep_completions": "deep_completions_allowed",
        }
    )

    # Away DataFrame
    away_df = df[
        [
            "match_id",
            "season",
            "game",
            "league_id",
            "season_id",
            "game_id",
            "date",
            "away_team",
            "away_points",
            "away_expected_points",
            "away_goals",
            "away_xg",
            "away_np_xg",
            "away_np_xg_difference",
            "home_goals",
            "away_ppda",
            "home_ppda",
            "away_deep_completions",
            "home_deep_completions",
        ]
    ].rename(
        columns={
            "away_team": "team",
            "away_points": "points",
            "away_expected_points": "xPoints",
            "away_goals": "goals",
            "home_goals": "GA",
            "away_xg": "xG",
            "away_np_xg": "npxG",
            "away_np_xg_difference": "npxGD",
            "away_ppda": "ppda",
            "home_ppda": "ppda_against",
            "away_deep_completions": "deep_completions",
            "home_deep_completions": "deep_completions_allowed",
        }
    )

    # Concatenate DataFrames
    team_df = pd.concat([home_df, away_df], ignore_index=True)

    pd.set_option("display.float_format", lambda x: "%.1f" % x)

    team_df["img"] = team_df["team"].map(team_badges)

    # Aggregate team_df by team and season
    agg_funcs = {
        "img": "first",  # Get the first badge
        "points": "sum",
        "xPoints": "sum",
        "goals": "sum",
        "GA": "sum",
        "xG": "sum",
        "npxG": "sum",
        "npxGD": "sum",
        "ppda": "mean",
        "ppda_against": "mean",
        "deep_completions": "sum",
        "deep_completions_allowed": "sum",
    }

    team_aggregated = team_df.groupby(["team", "season_id"]).agg(agg_funcs).reset_index()

    # Merge team_aggregated with df_team_summary on team and season
    merged_df = pd.merge(
        team_aggregated,
        df_team_summary,
        how="left",
        on=["team", "season_id"],
        suffixes=("", "_summary"),
    )

    print(f"After_merge_Columns_in_merged_df:\n{merged_df.columns.tolist()}")

    # Further aggregation if needed
    agg_funcs_final = {
        "img": "first",
        "points": "sum",
        "xPoints": "sum",
        "goals": "sum",
        "np_goals": "sum",
        "assists": "sum",
        "GA": "sum",
        "xG": "sum",
        "npxG": "sum",
        "npxGD": "sum",
        "xa": "sum",
        "ppda": "mean",
        "ppda_against": "mean",
        "deep_completions": "sum",
    }

    team_stats = (
        merged_df.groupby("team")
        .agg(agg_funcs_final)
        .reset_index()
        .round(1)
        .sort_values(by="points", ascending=False)
        .reset_index(drop=True)
    )

    # Format badge column
    team_stats["img"] = team_stats["img"].apply(
        lambda x: f'<img src="{x}" width="32">'
    )

    # Reorder columns to have badge as the first column
    team_stats = team_stats[
        ["img"] + [col for col in team_stats.columns if col != "img"]
    ]

    # Calculate goal difference
    team_stats["goal_diff"] = team_stats["goals"] - team_stats["GA"]

    # Create np:G-xG
    team_stats["np:G-xG"] = team_stats["np_goals"] - team_stats["npxG"]
    team_stats["A-xA"] = team_stats["assists"] - team_stats["xa"]

    # Drop GA column
    team_stats = team_stats.drop(columns=["GA"])

    # Ensure to include goal_diff in the rounding and formatting
    numeric_cols = [
        "points",
        "xPoints",
        "goals",
        "np_goals",
        "xG",
        "np:G-xG",
        "A-xA",
        "npxG",
        "npxGD",
        "ppda",
        "deep_completions",
    ]

    # Round numeric columns to 1 decimal place
    team_stats[numeric_cols] = team_stats[numeric_cols].round(1)

    cols_to_keep = [
        'team',
        'img',
        'points',
        'xPoints',
        'goals',
        'np_goals',    
        'xG',
        'npxG',
        'npxGD',
        "np:G-xG",
        "A-xA",
        "ppda",
        "deep_completions",
    ]

    team_stats = team_stats[cols_to_keep]

    # Reorder columns to have badge as the first column
    team_stats = team_stats[
        ["img"] + [col for col in team_stats.columns if col != "img"]
    ]

    # drop ppda_against, deep_completions_allowed columns
    # team_stats = team_stats.drop(columns=["ppda_against", "deep_completions_allowed"])

    # Create a summary DataFrame with the same columns as team_stats
    summary_df = team_stats[numeric_cols].agg(["sum", "mean"]).transpose()
    summary_df.columns = ["Sum", "Average"]
    summary_df = summary_df.T

    # Add non-numeric columns to the summary DataFrame with empty values
    for col in team_stats.columns:
        if col not in numeric_cols:
            summary_df[col] = ""

    # Ensure the summary DataFrame has the same column order as team_stats
    summary_df = summary_df[team_stats.columns]

    # Format the main table
    styled_team_stats = team_stats.style.format({col: "{:.1f}" for col in numeric_cols})

    # set table styles and properties
    styled_team_stats = (
        styled_team_stats.set_properties(
            subset=["team"],
            **{
                "text-align": "left",
                "font-family": FenomenSans,
                "background-color": "#0d0b17",
                "color": "gainsboro",
                "border-color": "#ffbd6d",
            },
        )
        .set_properties(
            subset=team_stats.columns.difference(["team"]),
            **{
                "text-align": "center",
                "font-family": fm_rubik,
                "background-color": "#0d0b17",
                "color": "gainsboro",
                "border-color": "#ffbd6d",
            },
        )
        .set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        ("font-family", fm_rubik),
                        ("background-color", "#070d1d"),
                        ("color", "floralwhite"),
                        ("border-color", "#ffbd6d"),
                        ("text-align", "center"),
                        ("border-weight", "3px"),
                    ],
                },
                {
                    "selector": "td:hover",
                    "props": [
                        ("background-color", "black"),
                        ("color", "wheat"),
                        ("border-color", "#ffbd6d"),
                    ],
                },
                {
                    "selector": ".blank.level0",
                    "props": [
                        ("background-color", "black"),
                        ("color", "floralwhite"),
                        ("border-color", "#ffbd6d"),
                        ("text-align", "center"),
                    ],
                },
                {
                    "selector": ".blank.hover",
                    "props": [
                        ("background-color", "black"),
                        ("color", "black"),
                        ("border-color", "#ffbd6d"),
                        ("text-align", "center"),
                    ],
                },
            ]
        )
        .text_gradient(
            subset=numeric_cols,
            cmap="coolwarm",
        )
        .highlight_max(
            subset=numeric_cols,
            props=highlight_max_props,
        )
        .highlight_min(
            subset=numeric_cols,
            props=highlight_min_props,
        )
        .hide(axis="index")
        # .set_sticky(axis="index", levels=[1,2])
    )

    # Format the summary table
    styled_summary_stats = summary_df.style.format(
        {col: "{:.1f}" for col in numeric_cols}
    )

    # set table styles and properties
    styled_summary_stats = styled_summary_stats.set_properties(
        subset=["team"],
        **{
            "text-align": "left",
            "font-family": FenomenSans,
            "background-color": "#0d0b17",
            "color": "gainsboro",
            "border-color": "#ffbd6d",
        },
    ).set_properties(
        subset=summary_df.columns.difference(["team"]),
        **{
            "text-align": "center",
            "font-family": fm_rubik,
            "background-color": "#0d0b17",
            "color": "gainsboro",
            "border-color": "#ffbd6d",
        },
    ).set_table_styles(
        [
            {
                "selector": "th",
                "props": [
                    ("font-family", fm_rubik),
                    ("background-color", "#070d1d"),
                    ("color", "floralwhite"),
                    ("border-color", "#ffbd6d"),
                    ("text-align", "center"),
                ],
            },
            {
                "selector": "td:hover",
                "props": [
                    ("background-color", "black"),
                    ("color", "floralwhite"),
                    ("border-color", "#ffbd6d"),
                ],
            },
            {
                "selector": ".blank.level0",
                "props": [
                    ("background-color", "black"),
                    ("color", "floralwhite"),
                    ("border-color", "#ffbd6d"),
                    ("text-align", "center"),
                ],
            },
            {
                "selector": ".blank.hover",
                "props": [
                    ("background-color", "black"),
                    ("color", "black"),
                    ("border-color", "#ffbd6d"),
                    ("text-align", "center"),
                ],
            },
        ]
    )

    # Concatenate the main table with the summary
    combined_styler = styled_team_stats.concat(styled_summary_stats)

    # Define CSS for horizontal scrolling
    css = """
    <style>
    .scrollable-table {
        overflow-x: auto;
        white-space: nowrap;
    }
    </style>
    """

    # Wrap the table in a div with horizontal scrolling
    # html = f"""
    # {css}
    # <div class="scrollable-table">
    #     {combined_styler.to_html(escape=False, index=False)}
    # </div>
    # """

    # drop the team column

    return combined_styler


def highlight_max(s):
    is_max = s == s.max()
    return ["background-color: crimson" if v else "" for v in is_max]


def get_color_mapping(unique_values):
    colors = sns.color_palette("brg", len(unique_values))
    color_mapping = {
        val: mcolors.rgb2hex(colors[i]) for i, val in enumerate(unique_values)
    }
    return color_mapping


def highlight_categorical(val, color_mapping):
    if val in color_mapping:
        return f"background-color: {color_mapping[val]}"
    return ""


# MyStyler = Styler.from_custom_template(
#     template_dir,
#     template_file,
# )

def main():
    team_badges, player_images = get_badges()
    team_to_id_dict = get_team_to_id_mapping()

    data = get_data()
    df = pd.DataFrame(data)

    df = df[
        [
            "intRank",
            "intPoints",
            "strTeamBadge",
            "strTeam",
            "intPlayed",
            "intWin",
            "intDraw",
            "intLoss",
            "intGoalsFor",
            "intGoalsAgainst",
            "intGoalDifference",
        ]
    ]
    df.columns = [
        "Rank",
        "Points",
        "img",
        "Team",
        "Played",
        "Wins",
        "Draws",
        "Losses",
        "Goals For",
        "Goals Against",
        "Goal Difference",
    ]
    df.reset_index(drop=True, inplace=True)

    st.markdown(
        f'<p style="font-family:{fm_rubik}; font-size: 56px; color: wheat;">English Premier League Dashboard</p>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Standings", "Team Stats", "Player Stats", "Chance Creation", "Team Players", "Scoring Trends"])

    with tab1:
        st.markdown(
            f'<p style="font-family:{fm_rubik}; font-size: 24px; color: wheat;">2023-2024 Season Standings</p>',
            unsafe_allow_html=True,
        )

        df["img"] = df.apply(
            lambda row: f'<img src="{row["img"]}" width="32">', axis=1
        )
        df["Goal Difference"] = df["Goal Difference"].astype(int)
        df["Goals Against"] = df["Goals Against"].astype(int)

        styled_df = (
            df.style.set_properties(
                subset=["Team"],
                **{
                    "text-align": "left",
                    "font-family": FenomenSans,
                    "background-color": "black",
                    "color": "gainsboro",
                    "border-color": "#ffbd6d",
                },
            )
            .set_properties(
                subset=df.columns.difference(["Team"]),
                **{
                    "text-align": "center",
                    "font-family": fm_rubik,
                    "background-color": "black",
                    "color": "gainsboro",
                    "border-color": "#ffbd6d",
                },
            )
            .set_table_styles(
                [
                    {
                        "selector": "th",
                        "props": [
                            ("font-family", fm_rubik),
                            ("background-color", "#070d1d"),
                            ("color", "floralwhite"),
                            ("border-color", "#ffbd6d"),
                            ("text-align", "center"),
                        ],
                    },
                    {
                        "selector": "td:hover",
                        "props": [
                            ("background-color", "black"),
                            ("color", "floralwhite"),
                            ("border-color", "#ffbd6d"),
                        ],
                    },
                    {
                        "selector": ".blank.level0",
                        "props": [
                            ("background-color", "black"),
                            ("color", "floralwhite"),
                            ("border-color", "#ffbd6d"),
                            ("text-align", "center"),
                        ],
                    },
                    {
                        "selector": ".blank.hover",
                        "props": [
                            ("background-color", "black"),
                            ("color", "black"),
                            ("border-color", "#ffbd6d"),
                            ("text-align", "center"),
                        ],
                    },
                ]
            )
            .text_gradient(
                subset=["Points", "Goals For", "Goals Against", "Goal Difference"],
                cmap="coolwarm",
            )
            .highlight_max(
                subset=["Points", "Goals For", "Goals Against", "Goal Difference"],
                props=highlight_max_props,
            )
            .highlight_min(
                subset=["Points", "Goals For", "Goals Against", "Goal Difference"],
                props=highlight_min_props,
            )
            .hide(axis="index")
        )

        st.markdown(
            styled_df.to_html(escape=False, index=False, bold_headers=True),
            unsafe_allow_html=True,
        )

    with tab2:
        st.header("Team Stats")
        _, _, _, df_team_summary, _, df_team_stats, _, _, _ = load_player_data()

        season_ids = df_team_stats['season_id'].unique()
        default_season = 2023
        season_range = st.slider(
            "Select Season Range",
            min_value=int(season_ids.min()),
            max_value=int(season_ids.max()),
            value=(default_season, default_season),
            key="team_season_range",
        )

        styled_team_stats = process_team_stats(
            df_team_stats, df_team_summary, season_range, team_badges
        )

        st.markdown(
            styled_team_stats.to_html(escape=False, index=False, bold_headers=True),
            unsafe_allow_html=True,
        )

    with tab3:
        st.header("Player Stats")
        (
            df1,
            df_players,
            df_players_summary,
            df_summary_teams,
            df_shots,
            df_team_stats,
            df_players_wages,
            df_xT,
            _
        ) = load_player_data()

        all_season_ids = ["All"] + sorted(df_players["season_id"].unique(), reverse=True)
        season_id = st.selectbox(
            "Select a season to filter the data",
            sorted(df_players["season_id"].unique(), reverse=True),
            placeholder="2023",
        )

        teams = ["All"] + sorted(df_players["team"].unique())
        team = st.selectbox(
            "Select a team to filter the data",
            teams,
            placeholder="All",
        )

        if team != "All":
            df_players = df_players[df_players["team"] == team]
            df_players_summary = df_players_summary[df_players_summary["team"] == team]
            df_shots = df_shots[df_shots["team"] == team]

        if season_id != "All":
            df_players = df_players[df_players["season_id"] == season_id]
            df_players_summary = df_players_summary[df_players_summary["season_id"] == season_id]
            df_shots = df_shots[df_shots["season_id"] == season_id]

        positions = ["All"] + sorted(df_players["position"].unique().tolist())
        position = st.selectbox(
            "Select a position to filter the data",
            positions,
            placeholder="All",
        )

        if position != "All":
            df_players = df_players[df_players["position"] == position]

        df_players_matches, df_players_summary_merge, _ = feature_engineering(
            df_players, df_xT, df_shots, team_badges, player_images
        )

        df_players_matches["img"] = df_players_matches.apply(
            lambda row: f'<img src="{row["img"]}" width="32">', axis=1
        )
        df_players_matches["player_image"] = df_players_matches["player_image"].apply(lambda x: f'<img src="{x}" width="32">')

        df_players_summary_merge["img"] = df_players_summary_merge.apply(
            lambda row: f'<img src="{row["img"]}" width="32">', axis=1
        )
        df_players_summary_merge["player_image"] = df_players_summary_merge["player_image"].apply(lambda x: f'<img src="{x}" width="32">')

        df_players_matches = df_players_matches[
            [
                "player_image",
                "player",
                "img",
                "position",
                "starts",
                "Apps",
                "goals",
                "shots",
                "xg",
                "xa",
                "xg_chain",
                "xg_buildup",
            ]
        ]
        df_players_matches.columns = [
            "Img",
            "Player",
            "Team",
            "Pos",
            "Starts",
            "Apps",
            "Gls",
            "Shots",
            "xG",
            "xA",
            "xGChain",
            "xGBuildup",
        ]

        df_players_summary_merge = df_players_summary_merge[
            [
                "img",
                "player",
                "position",
                "starts",
                "goals",
                "np_goals",
                "xg",
                "np:G-xG",
                "assists",
                "xa",
                "A-xA",
                "npxG/shot",
                "KPs/90",
                "Sh/90",
                "xg_chain",
                "xg_buildup",
                "xT_total",
                "xT_perAction",
            ]
        ]
        df_players_summary_merge.columns = [
            "Team",
            "Player",
            "Pos",
            "GS",
            "Gls",
            "npGls",
            "xG",
            "np:G-xG",
            "Assists",
            "xA",
            "A-xA",
            "npxG/Shot",
            "KPs/90",
            "Sh/90",
            "xGChain",
            "xGBuildup",
            "xT_total",
            "xT_perAction",
        ]

        color_mapping = get_color_mapping(df_players_matches["Pos"].unique())

        numerical_columns_matches = df_players_matches.columns.difference(
            ["Img", "Player", "Team", "Pos"]
        )

        styled_df_players_matches = (
            df_players_matches.style.format(
                {
                    **{
                        col: "{:.0f}"
                        for col in df_players_matches.columns.difference(
                            ["Img", "Player", "Team", "Pos", "xG", "xA", "xGChain", "xGBuildup"]
                        )
                    },
                    "xG": "{:.2f}",
                    "xA": "{:.2f}",
                    "xGChain": "{:.2f}",
                    "xGBuildup": "{:.2f}",
                }
            )
            .set_properties(
                subset=["Player"],
                **{
                    "text-align": "left",
                    "font-family": FenomenSans,
                    "background-color": "#0d0b17",
                    "color": "gainsboro",
                    "border-color": "#ffbd6d",
                },
            )
            .set_properties(
                subset=df_players_matches.columns.difference(["Player"]),
                **{
                    "text-align": "center",
                    "font-family": fm_rubik,
                    "background-color": "#0d0b17",
                    "color": "gainsboro",
                    "border-color": "#ffbd6d",
                },
            )
            .set_table_styles(
                [
                    {
                        "selector": "th",
                        "props": [
                            ("font-family", fm_rubik),
                            ("background-color", "#070d1d"),
                            ("color", "floralwhite"),
                            ("border-color", "#ffbd6d"),
                            ("text-align", "center"),
                        ],
                    },
                    {
                        "selector": "td:hover",
                        "props": [
                            ("background-color", "black"),
                            ("color", "gold"),
                            ("border-color", "#ffbd6d"),
                        ],
                    },
                    {
                        "selector": ".blank.level0",
                        "props": [
                            ("background-color", "black"),
                            ("color", "floralwhite"),
                            ("border-color", "#ffbd6d"),
                            ("text-align", "center"),
                        ],
                    },
                    {
                        "selector": ".blank.hover",
                        "props": [
                            ("background-color", "black"),
                            ("color", "black"),
                            ("border-color", "#ffbd6d"),
                            ("text-align", "center"),
                        ],
                    },
                ]
            )
            .text_gradient(subset=numerical_columns_matches, cmap="coolwarm")
            .highlight_max(subset=numerical_columns_matches, props=highlight_max_props)
            .highlight_min(subset=numerical_columns_matches, props=highlight_min_props)
            .applymap(
                lambda val: highlight_categorical(val, color_mapping),
                subset=["Pos"],
            )
            .hide(axis="index")
        )

        numerical_columns_summary = df_players_summary_merge.columns.difference(
            ["Img", "Player", "Team", "Pos"]
        )

        styled_df_players_summary = (
            df_players_summary_merge.style.format(
                {
                    **{
                        col: "{:.0f}"
                        for col in df_players_summary_merge.columns.difference(
                            ["Img", "Player", "Team", "Pos"]
                        )
                    },
                    "xT_total": "{:.2f}",
                    "xT_perAction": "{:.3f}",
                    "xG": "{:.2f}",
                    "xA": "{:.2f}",
                    "xGChain": "{:.2f}",
                    "xGBuildup": "{:.2f}",
                    "npxG/Shot": "{:.2f}",
                    "KPs/90": "{:.1f}",
                    "Sh/90": "{:.1f}",
                }
            )
            .set_properties(
                subset=["Player"],
                **{
                    "text-align": "left",
                    "font-family": FenomenSans,
                    "background-color": "#0d0b17",
                    "color": "gainsboro",
                    "border-color": "#ffbd6d",
                },
            )
            .set_properties(
                subset=df_players_summary_merge.columns.difference(["Player"]),
                **{
                    "text-align": "center",
                    "font-family": fm_rubik,
                    "background-color": "#0d0b17",
                    "color": "gainsboro",
                    "border-color": "#ffbd6d",
                },
            )
            .set_table_styles(
                [
                    {
                        "selector": "th",
                        "props": [
                            ("font-family", fm_rubik),
                            ("background-color", "#070d1d"),
                            ("color", "floralwhite"),
                            ("border-color", "#ffbd6d"),
                            ("text-align", "center"),
                        ],
                    },
                    {
                        "selector": "td:hover",
                        "props": [
                            ("background-color", "black"),
                            ("color", "gold"),
                            ("border-color", "#ffbd6d"),
                        ],
                    },
                    {
                        "selector": ".blank.level0",
                        "props": [
                            ("background-color", "black"),
                            ("color", "floralwhite"),
                            ("border-color", "#ffbd6d"),
                            ("text-align", "center"),
                        ],
                    },
                    {
                        "selector": ".blank.hover",
                        "props": [
                            ("background-color", "black"),
                            ("color", "black"),
                            ("border-color", "#ffbd6d"),
                            ("text-align", "center"),
                        ],
                    },
                ]
            )
            .text_gradient(subset=numerical_columns_summary, cmap="coolwarm")
            .highlight_max(subset=numerical_columns_summary, props=highlight_max_props)
            .highlight_min(subset=numerical_columns_summary, props=highlight_min_props)
            .applymap(
                lambda val: highlight_categorical(val, color_mapping),
                subset=["Pos"],
            )
            .hide(axis="index")
        )

        st.markdown(
            styled_df_players_summary.to_html(escape=False, index=False, bold_headers=True),
            unsafe_allow_html=True,
        )

    with tab4:
        st.header("Chance Creation")

        _, _, _, _, df_shots, _, _, _, player_positions = load_player_data()

        df_shots_copy = df_shots.copy()

        # Log shots data columns
        st.write(df_shots.columns)

        season_ids = sorted(df_shots["season_id"].unique(), reverse=True)
        default_season = 2023
        season_range = st.slider(
            "Select Season Range",
            min_value=int(min(season_ids)),
            max_value=int(max(season_ids)),
            value=(default_season, default_season),
            key="chance_creation_season_range",
        )

        df_shots = df_shots[
            (df_shots["season_id"] >= season_range[0])
            & (df_shots["season_id"] <= season_range[1])
        ]

        teams = ["All"] + sorted(df_shots["team"].unique())
        default_team = "All"

        team = st.selectbox(
            "Select a team",
            teams,
            index=teams.index(default_team),
            key="chance_creation_team",
        )

        if team != "All":
            df_shots = df_shots[df_shots["team"] == team]

        positions = ["All"] + sorted(df_shots["position"].unique())
        default_position = "All"

        position = st.selectbox(
            "Select a position",
            positions,
            index=positions.index(default_position),
            key="chance_creation_position",
        )

        if position != "All":
            df_shots = df_shots[df_shots["position"] == position]

        df_shots, df_shots_team = transform_shot_data(df_shots)

        # Create a toggle for instead getting shot creators ie shot assistors
        shot_assistors = st.radio(
            "Show shot assistors", ["No", "Yes"], key="shot_assistors"
        )

        # Add filter for minimum games for df_shots
        if shot_assistors == "No":
            default_matches_value = int(0.3 * max(df_shots["matches"]))
            min_games = st.number_input(
                "Minimum number of games",
                min_value=1,
                max_value=max(df_shots["matches"]),
                value=default_matches_value,
                key="min_games",
            )
            df_shots = df_shots[df_shots["matches"] >= min_games]
            df_shots = df_shots.drop(columns=["matches"])

        if shot_assistors == "Yes":
            # Call the function to get shot assistors
            df_shots_assists, df_shots_assists_team = transform_shot_data_assist(
                df_shots_copy
            )

            df_shots_assists = add_badges(
                df_shots_assists, team_badges, playerwise=True
            )
            df_shots_assists_team = add_badges(
                df_shots_assists_team, team_badges, playerwise=False
            )
        else:
            df_shots = add_badges(df_shots, team_badges, playerwise=True)
            df_shots_team = add_badges(df_shots_team, team_badges, playerwise=False)

        team_wise = st.radio("Show team-wise stats", ["No", "Yes"], key="team_wise")

        if team_wise == "Yes":
            if shot_assistors == "Yes":
                st.info(
                    f"Table displays per shot assist stats for each **team**", icon="🚨"
                )
                st.markdown(
                    df_shots_assists_team.to_html(escape=False, index=False),
                    unsafe_allow_html=True,
                )
            else:
                st.info(f"Table displays per shot stats for each team", icon="🚨")
                st.markdown(
                    df_shots_team.to_html(escape=False, index=False, bold_headers=True),
                    unsafe_allow_html=True,
                )
        else:
            if shot_assistors == "Yes":
                st.info(
                    f"Table displays per shot assist stats for each **player**",
                    icon="🚨",
                )
                st.markdown(
                    df_shots_assists.to_html(escape=False, index=False),
                    unsafe_allow_html=True,
                )
            else:
                st.info(f"Table displays per shot stats for each **player**", icon="🚨")
                st.markdown(
                    df_shots.to_html(escape=False, index=False, bold_headers=True),
                    unsafe_allow_html=True,
                )
    with tab5:
        st.header("Team Players")

        _, _, _, _, _, _, df_players_wages, _, _ = load_player_data(filter=True)

        team = st.selectbox(
            "Select a team", sorted(df["Team"].unique()), placeholder="Arsenal"
        )

        team_id = team_to_id_dict[team]
        players = fetch_player_data(team, team_id)

        show_wages = st.radio("Show player wages", ["Yes", "No"])

        if players:
            styled_players, styled_players_wages = render_player_table(
                players, df_players_wages
            )

            if show_wages == "Yes":
                st.markdown(
                    f'<p style="font-family:{fm_rubik}; font-size: 24px; color: wheat;">{team} Player Wages</p>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    styled_players_wages.to_html(escape=False, index=False, bold_headers=True), unsafe_allow_html=True
                )
            else:
                st.write("Player Stats")
                st.markdown(
                    styled_players.to_html(escape=False, index=False, bold_headers=True), unsafe_allow_html=True
                )
        else:
            st.write("No player data available for the selected team.")

    with tab6:
        st.header("Scoring Trends")

        _, _, _, _, _, df_team_stats, _, _, _ = load_player_data()

        season_ids = df_team_stats['season_id'].unique()
        default_season = 2023
        season_range = st.slider(
            "Select Season Range",
            min_value=int(season_ids.min()),
            max_value=int(season_ids.max()),
            value=(default_season, default_season),
            key="scoring_trends_season_range",
        )

        df_team_stats = df_team_stats[
            (df_team_stats["season_id"] >= season_range[0])
            & (df_team_stats["season_id"] <= season_range[1])
        ]

        alt_chart, alt_chart2 = plot_home_away_goals(df_team_stats)

        st.altair_chart(alt_chart, use_container_width=True)
        st.altair_chart(alt_chart2, use_container_width=True)

if __name__ == "__main__":
    main()

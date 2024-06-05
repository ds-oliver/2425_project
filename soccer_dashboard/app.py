import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import numpy as np
import altair as alt
import logging
import os

from config import API_KEY, EPL_ID, EFL_CHAMPIONSHIP_ID, EFL_LEAGUE_ONE_ID, SEASON, fm_rubik, FenomenSans

# setup logging
logging.basicConfig(level=logging.INFO)

# Define the path to the template directory and the template file name
template_dir = "/Users/hogan/2425_project/soccer_dashboard/html"
template_file = "template.tpl"

highlight_max_props = "color:crimson; font-weight:bold; background-color:#030021;"
highlight_min_props = "color:#A6FFFE; font-weight:bold; background-color:#100000;"

# Set the page configuration
st.set_page_config(
    page_title="Soccer Dashboard",
    page_icon=":exclamation:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Caching API calls to minimize repeated requests
@st.cache_data
def get_team_to_id_mapping():
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookup_all_teams.php?id={EPL_ID}"
    response = requests.get(url)
    data = response.json()
    team_to_id = {team["strTeam"]: team["idTeam"] for team in data["teams"]}
    return team_to_id

@st.cache_data
def fetch_player_data(team_name, team_id):
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookup_all_players.php?id={team_id}"
    response = requests.get(url)
    data = response.json()
    players = data.get("player", [])
    return players

@st.cache_data
def get_badges():
    league_ids = [EPL_ID, EFL_CHAMPIONSHIP_ID, EFL_LEAGUE_ONE_ID]
    badges = {}

    with requests.Session() as session:
        for league_id in league_ids:
            url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookup_all_teams.php?id={league_id}"
            response = session.get(url)
            data = response.json()
            league_badges = {
                team["strTeam"]: team["strTeamBadge"] + "/tiny"
                for team in data.get("teams", [])
            }
            badges.update(league_badges)

    return badges

@st.cache_data
def load_player_data(filter=None):
    base_path = "/mnt/src/2425_project/data" if os.path.exists("/mnt/src/2425_project/data") else os.path.join(os.path.dirname(__file__), "../data")

    df1 = pd.read_csv(os.path.join(base_path, "combined_data.csv"))
    df_players_matches = pd.read_csv(os.path.join(base_path, "players_matches_data.csv"))
    df_players_summary = pd.read_csv(os.path.join(base_path, "players_summary_data.csv"))
    df_shots = pd.read_csv(os.path.join(base_path, "shot_events.csv"))
    df_team_stats = pd.read_csv(os.path.join(base_path, "team_stats.csv"))
    df_player_wages = pd.read_csv(os.path.join(base_path, "premier_league_salaries.csv"))
    df_xT = pd.read_csv(os.path.join(base_path, "players_xT_data.csv"))

    df_summary_teams = df_players_summary.groupby(["team", "season_id"], as_index=False).sum()

    if filter:
        df_player_wages = df_player_wages[df_player_wages["season"] == 2023]
        df_summary_teams = df_summary_teams[df_summary_teams["season_id"] == 2023]

    return df1, df_players_matches, df_players_summary, df_summary_teams, df_shots, df_team_stats, df_player_wages, df_xT

@st.cache_data
def feature_engineering(df_players_matches, df_players_summary, df_shots, team_badges):
    df_players_matches["is_starter"] = df_players_matches["position"].apply(lambda x: False if "Sub" in x else True)
    df_players_matches["Apps"] = df_players_matches["minutes"].apply(lambda x: True if x > 0 else False)
    df_players_matches["mins_as_starter"] = df_players_matches.apply(lambda row: row["minutes"] if row["is_starter"] else 0, axis=1)
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

    df_players_matches = df_players_matches.groupby(["player_id"], as_index=False).agg(agg_dict)
    df_players_matches["mins/start"] = df_players_matches["mins_as_starter"] / df_players_matches["starts"]

    numerical_columns = df_players_matches.columns.difference(["player", "team", "position", "xg", "xa", "xg_chain", "xg_buildup"])
    df_players_matches[numerical_columns] = df_players_matches[numerical_columns].apply(np.ceil)

    df_players_matches["badge"] = df_players_matches["team"].map(team_badges)

    df_players_merge = pd.merge(
        df_players_matches,
        df_players_summary,
        left_on="player_id",
        right_on="player_id",
        how="left",
        suffixes=("", "_summary"),
    )

    df_shots = df_shots.groupby(
        ["player_id", "player", "result", "situation", "body_part", "zone_y", "opponent_name", "is_home_team", "season_id", "assist_player"],
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

    df_situations = df_situations[['badge', 'player', 'position', '90s', 'season_id', 'team_id', 'player_shots', 'result', 'situation', 'body_part', 'zone_y', 'opponent_name', 'is_home_team', 'season_id_shots', 'assist_player', 'shots_shots', 'xg_shots']]

    df_situations.columns = [
        "badge",
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
            "badge",
            "player",
            "position",
            "starts",
            "Apps",
            "minutes_played",
            "mins_as_starter",
            "goals",
            "shots",
            "xg",
            "xa",
            "xg_chain",
            "xg_buildup",
            "own_goals",
            "90s",
        ]
    ]

    df_players_merge["mins/start"] = df_players_merge["mins_as_starter"] / df_players_merge["starts"]

    return df_players_matches, df_players_merge, df_situations

@st.cache_data
def transform_shot_data(df_shots):
    grouped_data = df_shots.groupby(["player", "team", "position", "situation", "body_part", "zone_y"]).agg(
        total_xg=pd.NamedAgg(column="xg", aggfunc="sum"),
        shot_count=pd.NamedAgg(column="xg", aggfunc="count"),
    ).reset_index()

    matches_data = df_shots.groupby(["player", "team", "position"]).agg(matches=pd.NamedAgg(column="game", aggfunc="nunique")).reset_index()

    grouped_data["per_shot_xg"] = grouped_data["total_xg"] / grouped_data["shot_count"]

    situation_pivot = grouped_data.pivot_table(
        index=["player", "team", "position"],
        columns="situation",
        values="per_shot_xg",
        fill_value=0,
    )
    situation_pivot.columns = [f"{col} xG" for col in situation_pivot.columns]
    situation_pivot.reset_index(inplace=True)

    body_part_pivot = grouped_data.pivot_table(
        index=["player", "team", "position"],
        columns="body_part",
        values="per_shot_xg",
        fill_value=0,
    )
    body_part_pivot.columns = [f"{col} xG" for col in body_part_pivot.columns]
    body_part_pivot.reset_index(inplace=True)

    zone_y_pivot = grouped_data.pivot_table(
        index=["player", "team", "position"],
        columns="zone_y",
        values="per_shot_xg",
        fill_value=0,
    )
    zone_y_pivot.columns = [f"{col} xG" for col in zone_y_pivot.columns]
    zone_y_pivot.reset_index(inplace=True)

    playerwise_result = situation_pivot.merge(body_part_pivot, on=["player", "team", "position"], how="outer")
    playerwise_result = playerwise_result.merge(zone_y_pivot, on=["player", "team", "position"], how="outer")
    playerwise_result = playerwise_result.merge(matches_data, on=["player", "team", "position"], how="left")

    team_grouped_data = df_shots.groupby(["team", "situation", "body_part", "zone_y"]).agg(
        total_xg=pd.NamedAgg(column="xg", aggfunc="sum"),
        shot_count=pd.NamedAgg(column="xg", aggfunc="count"),
    ).reset_index()

    team_grouped_data["per_shot_xg"] = team_grouped_data["total_xg"] / team_grouped_data["shot_count"]

    team_situation_pivot = team_grouped_data.pivot_table(
        index=["team"],
        columns="situation",
        values="per_shot_xg",
        fill_value=0,
    )
    team_situation_pivot.columns = [f"{col} xG" for col in team_situation_pivot.columns]
    team_situation_pivot.reset_index(inplace=True)

    team_body_part_pivot = team_grouped_data.pivot_table(
        index=["team"],
        columns="body_part",
        values="per_shot_xg",
        fill_value=0,
    )
    team_body_part_pivot.columns = [f"{col} xG" for col in team_body_part_pivot.columns]
    team_body_part_pivot.reset_index(inplace=True)

    team_zone_y_pivot = team_grouped_data.pivot_table(
        index=["team"],
        columns="zone_y",
        values="per_shot_xg",
        fill_value=0,
    )
    team_zone_y_pivot.columns = [f"{col} xG" for col in team_zone_y_pivot.columns]
    team_zone_y_pivot.reset_index(inplace=True)

    teamwise_result = team_situation_pivot.merge(team_body_part_pivot, on="team", how="outer")
    teamwise_result = teamwise_result.merge(team_zone_y_pivot, on="team", how="outer")

    return playerwise_result, teamwise_result

@st.cache_data
def plot_home_away_goals(df):
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.day_name()
    df['month'] = df['date'].dt.month_name()
    df['total_goals'] = df['home_goals'] + df['away_goals']
    df['month'] = pd.Categorical(df['month'], categories=['August', 'September', 'October', 'November', 'December', 'January', 'February', 'March', 'April', 'May'], ordered=True)
    df['season_id'] = pd.Categorical(df['season_id'], categories=df['season_id'].unique(), ordered=True)

    total_matches = df.shape[0]
    df['matches'] = df.groupby(['home_goals', 'away_goals'])['home_goals'].transform('count')
    df['percentage'] = df['matches'] / total_matches * 100

    chart = alt.Chart(df).mark_rect().encode(
        alt.X('home_goals:Q', title='Home Goals').bin(maxbins=15),
        alt.Y('away_goals:Q', title='Away Goals').bin(maxbins=15),
        alt.Color('count():Q', title="Number of Matches").scale(scheme='viridis'),
        tooltip=[alt.Tooltip('home_goals:Q', title='Home Goals'), alt.Tooltip('away_goals:Q', title='Away Goals'), alt.Tooltip('count():Q', title='Number of Matches')]
    ).properties(
        width=600,
        height=400
    )

    avg_goals_month_day_season = df.groupby(['month', 'day_of_week', 'season_id']).agg({'total_goals': 'mean', 'total_matches': 'first', 'unique_seasons': 'first'}).reset_index().round(2)
    avg_goals_month_day_season.columns = ['month', 'day_of_week', 'season_id', 'avg_total_goals', 'total_matches', 'unique_seasons']

    chart2 = alt.Chart(avg_goals_month_day_season).mark_rect().encode(
        alt.X("month:N", title="Month", sort=alt.EncodingSortField(field="date", op="min")),
        alt.Y("day_of_week:N", title="Day of the Week"),
        alt.Color("avg_total_goals:Q", title="Average Total Goals", scale=alt.Scale(scheme="viridis")),
        tooltip=[
            alt.Tooltip("total_matches:Q", title="Total Matches"),
            alt.Tooltip("avg_total_goals:Q", title="Average Total Goals"),
            alt.Tooltip("unique_seasons:Q", title="Unique Seasons"),
        ],
    ).properties(width=600, height=400)

    return chart, chart2

def render_player_table(players, player_wages):
    df_players_matches = pd.DataFrame(players)

    df_players_matches = df_players_matches[
        ["strCutout", "strPlayer", "strPosition", "trophies", "dateBorn", "Int", "strNationality", "strNumber", "strHeight"]
    ]
    df_players_matches.columns = ["Player", "Name", "Position", "Trophies", "Age", "Int", "Nation", "Number", "Height"]

    df_players_matches["Trophies"] = df_players_matches["Trophies"].astype(int)
    df_players_matches["Age"] = pd.to_datetime(df_players_matches["Age"]).apply(lambda x: pd.Timestamp.now().year - x.year)
    df_players_matches["Name"] = df_players_matches["Name"].apply(unidecode)

    df_players_wages = pd.merge(df_players_matches, player_wages, left_on="Name", right_on="name", how="left")

    df_players_wages = df_players_wages[
        ["Player", "Name", "Position", "Trophies", "Age", "Int", "Nation", "Number", "weekly_gross_gbp", "years", "release_gbp"]
    ]
    df_players_wages.columns = ["Player", "Name", "Position", "Trophies", "Age", "Int", "Nation", "Number", "WklyWages", "YrsLeft", "Release"]

    df_players_matches = df_players_matches.sort_values("Trophies", ascending=False).reset_index(drop=True)
    df_players_wages = df_players_wages.sort_values("WklyWages", ascending=False).reset_index(drop=True)
    df_players_wages.fillna("NA", inplace=True)

    if "Manager" in df_players_matches["Position"].values:
        manager = df_players_matches[df_players_matches["Position"] == "Manager"]
        df_players_matches = df_players_matches[df_players_matches["Position"] != "Manager"]
        df_players_matches = pd.concat([manager, df_players_matches]).reset_index(drop=True)

    if "Manager" in df_players_wages["Position"].values:
        manager_wages = df_players_wages[df_players_wages["Position"] == "Manager"]
        df_players_wages = df_players_wages[df_players_wages["Position"] != "Manager"]
        df_players_wages = pd.concat([manager_wages, df_players_wages]).reset_index(drop=True)

    df_players_wages["WklyWages"] = df_players_wages["WklyWages"].apply(lambda x: f"£{x:,.2f}" if x != "NA" else "NA")
    df_players_wages["Release"] = df_players_wages["Release"].apply(lambda x: f"£{x:,.2f}" if x != "NA" else "NA")
    df_players_wages["YrsLeft"] = df_players_wages["YrsLeft"].apply(lambda x: f"{x}" if x != "NA" else "NA")

    df_players_matches["Player"] = df_players_matches.apply(lambda row: f'<img src="{row["Player"]}" width="50">', axis=1)
    df_players_wages["Player"] = df_players_wages.apply(lambda row: f'<img src="{row["Player"]}" width="50">', axis=1)
    df_players_matches["Int"] = df_players_matches.apply(lambda row: (f'<img src="{row["Int"]}" width="32">' if row["Int"] else ""), axis=1)
    df_players_wages["Int"] = df_players_wages.apply(lambda row: (f'<img src="{row["Int"]}" width="32">' if row["Int"] else ""), axis=1)

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
        ).set_properties(
            subset=df_players_matches.columns.difference(["Name", "Position", "Nation"]),
            **{
                "text-align": "center",
                "font-family": FenomenSans,
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
        ).set_properties(
            subset=df_players_wages.columns.difference(["Name", "Position", "Nation"]),
            **{
                "text-align": "center",
                "font-family": FenomenSans,
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


@st.cache_data
def get_data():
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookuptable.php?l={EPL_ID}&s={SEASON}"
    response = requests.get(url)
    data = response.json()
    return data["table"]


def main():
    team_badges = get_badges()
    team_to_id_dict = get_team_to_id_mapping()

    data = get_data()
    df = pd.DataFrame(data, index=None)

    df = df[
        ["intRank", "intPoints", "strTeamBadge", "strTeam", "intPlayed", "intWin", "intDraw", "intLoss", "intGoalsFor", "intGoalsAgainst", "intGoalDifference"]
    ]
    df.columns = [
        "Rank",
        "Points",
        "Badge",
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

    st.markdown(f'<p style="font-family:{fm_rubik}; font-size: 56px; color: wheat;">English Premier League Dashboard</p>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Standings", "Team Stats", "Player Stats", "Chance Creation", "Team Players", "Scoring Trends"])

    with tab1:
        st.markdown(f'<p style="font-family:{fm_rubik}; font-size: 24px; color: wheat;">2023-2024 Season Standings</p>', unsafe_allow_html=True)
        df["Badge"] = df.apply(lambda row: f'<img src="{row["Badge"]}" width="32">', axis=1)
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
            ).set_properties(
                subset=df.columns.difference(["Team"]),
                **{
                    "text-align": "center",
                    "font-family": fm_rubik,
                    "background-color": "black",
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
            ).text_gradient(
                subset=["Points", "Goals For", "Goals Against", "Goal Difference"],
                cmap="coolwarm",
            ).highlight_max(
                subset=["Points", "Goals For", "Goals Against", "Goal Difference"],
                props=highlight_max_props,
            ).highlight_min(
                subset=["Points", "Goals For", "Goals Against", "Goal Difference"],
                props=highlight_min_props,
            ).hide(axis="index")
        )

        st.markdown(styled_df.to_html(escape=False, index=False, bold_headers=True), unsafe_allow_html=True)

    with tab2:
        st.header("Team Stats")
        _, _, _, df_team_summary, _, df_team_stats, _, _ = load_player_data()

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

        st.markdown(styled_team_stats.to_html(escape=False, index=False, bold_headers=True), unsafe_allow_html=True)

    with tab3:
        st.header("Player Stats")
        _, df_players, df_players_summary, _, df_shots, _, df_players_wages, df_xT, _ = load_player_data()

        all_season_ids = ["All"] + sorted(df_players["season_id"].unique(), reverse=True)
        season_id = st.selectbox("Select a season to filter the data", sorted(df_players["season_id"].unique(), reverse=True), placeholder="2023")
        teams = ["All"] + sorted(df_players["team"].unique())
        team = st.selectbox("Select a team to filter the data", teams, placeholder="All")

        if team != "All":
            df_players = df_players[df_players["team"] == team]
            df_players_summary = df_players_summary[df_players_summary["team"] == team]
            df_shots = df_shots[df_shots["team"] == team]

        df_players = df_players[df_players["season_id"] == season_id]
        df_players_summary = df_players_summary[df_players_summary["season_id"] == season_id]
        df_shots = df_shots[df_shots["season_id"] == season_id]

        positions = ["All"] + sorted(df_players["position"].unique().tolist())
        position = st.selectbox("Select a position to filter the data", positions, placeholder="All")

        if position != "All":
            df_players = df_players[df_players["position"] == position]

        df_players_matches, df_players_summary_merge, _ = feature_engineering(
            df_players, df_xT, df_shots, team_badges, player_images
        )

        df_players_matches["badge"] = df_players_matches.apply(lambda row: f'<img src="{row["badge"]}" width="32">', axis=1)
        df_players_matches["player_image"] = df_players_matches["player_image"].apply(lambda x: f'<img src="{x}" width="32">')
        df_players_summary_merge["badge"] = df_players_summary_merge.apply(lambda row: f'<img src="{row["badge"]}" width="32">', axis=1)
        df_players_summary_merge["player_image"] = df_players_summary_merge["player_image"].apply(lambda x: f'<img src="{x}" width="32">')

        df_players_matches = df_players_matches[
            ["player_image", "player", "badge", "position", "starts", "Apps", "goals", "shots", "xg", "xa", "xg_chain", "xg_buildup"]
        ]
        df_players_matches.columns = [
            "Img", "Player", "Team", "Pos", "Starts", "Apps", "Gls", "Shots", "xG", "xA", "xGChain", "xGBuildup"
        ]

        df_players_summary_merge.columns.tolist()

        df_players_summary_merge = df_players_summary_merge[
            ["badge", "player", "position", "starts", "goals", "np_goals", "xg", "np:G-xG", "assists", "xa", "A-xA", "npxG/shot", "KPs/90", "Sh/90", "xg_chain", "xg_buildup", "xT_total", "xT_perAction"]
        ]
        df_players_summary_merge.columns = [
            "Team", "Player", "Pos", "GS", "Gls", "npGls", "xG", "np:G-xG", "Assists", "xA", "A-xA", "npxG/Shot", "KPs/90", "Sh/90", "xGChain", "xGBuildup", "xT_total", "xT_perAction"
        ]

        color_mapping = get_color_mapping(df_players_matches["Pos"].unique())

        numerical_columns_matches = df_players_matches.columns.difference(
            ["Img", "Player", "Team", "Pos"]
        )

        styled_df_players_matches = (
            df_players_matches.style.format(
                {**{col: "{:.0f}" for col in df_players_matches.columns.difference(["Img", "Player", "Team", "Pos", "xG", "xA", "xGChain", "xGBuildup"])},
                "xG": "{:.2f}",
                "xA": "{:.2f}",
                "xGChain": "{:.2f}",
                "xGBuildup": "{:.2f}",}
            ).set_properties(
                subset=["Player"],
                **{
                    "text-align": "left",
                    "font-family": FenomenSans,
                    "background-color": "#0d0b17",
                    "color": "gainsboro",
                    "border-color": "#ffbd6d",
                },
            ).set_properties(
                subset=df_players_matches.columns.difference(["Player"]),
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
            ).text_gradient(subset=numerical_columns_matches, cmap="coolwarm").highlight_max(subset=numerical_columns_matches, props=highlight_max_props).highlight_min(subset=numerical_columns_matches, props=highlight_min_props).applymap(
                lambda val: highlight_categorical(val, color_mapping), subset=["Pos"],
            ).hide(axis="index")
        )

        numerical_columns_summary = df_players_summary_merge.columns.difference(
            ["Img", "Player", "Team", "Pos"]
        )

        styled_df_players_summary = (
            df_players_summary_merge.style.format(
                {**{col: "{:.0f}" for col in df_players_summary_merge.columns.difference(["Img", "Player", "Team", "Pos"])},
                "xT_total": "{:.2f}",
                "xT_perAction": "{:.3f}",
                "xG": "{:.2f}",
                "xA": "{:.2f}",
                "xGChain": "{:.2f}",
                "xGBuildup": "{:.2f}",
                "npxG/Shot": "{:.2f}",
                "KPs/90": "{:.1f}",
                "Sh/90": "{:.1f}",}
            ).set_properties(
                subset=["Player"],
                **{
                    "text-align": "left",
                    "font-family": FenomenSans,
                    "background-color": "#0d0b17",
                    "color": "gainsboro",
                    "border-color": "#ffbd6d",
                },
            ).set_properties(
                subset=df_players_summary_merge.columns.difference(["Player"]),
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
            ).text_gradient(subset=numerical_columns_summary, cmap="coolwarm").highlight_max(subset=numerical_columns_summary, props=highlight_max_props).highlight_min(subset=numerical_columns_summary, props=highlight_min_props).applymap(
                lambda val: highlight_categorical(val, color_mapping), subset=["Pos"],
            ).hide(axis="index")
        )

        st.markdown(styled_df_players_summary.to_html(escape=False, index=False, bold_headers=True), unsafe_allow_html=True)

    with tab4:
        st.header("Chance Creation")
        _, _, _, _, df_shots, _, _, _, player_positions = load_player_data()

        season_ids = sorted(df_shots["season_id"].unique(), reverse=True)
        default_season = 2023
        season_range = st.slider(
            "Select Season Range",
            min_value=int(min(season_ids)),
            max_value=int(max(season_ids)),
            value=(default_season, default_season),
            key="chance_creation_season_range",
        )

        df_shots = df_shots[(df_shots["season_id"] >= season_range[0]) & (df_shots["season_id"] <= season_range[1])]
        teams = ["All"] + sorted(df_shots["team"].unique())
        default_team = "All"
        team = st.selectbox("Select a team", teams, index=teams.index(default_team), key="chance_creation_team")

        if team != "All":
            df_shots = df_shots[df_shots["team"] == team]

        positions = ["All"] + sorted(df_shots["position"].unique())
        default_position = "All"
        position = st.selectbox("Select a position", positions, index=positions.index(default_position), key="chance_creation_position")

        if position != "All":
            df_shots = df_shots[df_shots["position"] == position]

        df_shots, df_shots_team = transform_shot_data(df_shots)
        default_matches_value = int(0.3 * max(df_shots["matches"]))
        min_games = st.number_input("Minimum number of games", min_value=1, max_value=max(df_shots["matches"]), value=default_matches_value, key="min_games")
        df_shots = df_shots[df_shots["matches"] >= min_games]
        df_shots = df_shots.drop(columns=["matches"])

        df_shots = add_badges(df_shots, team_badges, playerwise=True)
        df_shots_team = add_badges(df_shots_team, team_badges, playerwise=False)

        team_wise = st.radio("Show team-wise stats", ["No", "Yes"], key="team_wise")

        if team_wise == "Yes":
            st.info(f"Table displays per shot stats for each team", icon="🚨")
            st.markdown(df_shots_team.to_html(escape=False, index=False, bold_headers=True), unsafe_allow_html=True)
        else:
            st.info(f"Table displays per shot stats for each **player**", icon="🚨")
            st.markdown(df_shots.to_html(escape=False, index=False, bold_headers=True), unsafe_allow_html=True)

    with tab5:
        st.header("Team Players")
        _, _, _, _, _, _, df_players_wages, _, _ = load_player_data(filter=True)
        team = st.selectbox("Select a team", sorted(df["Team"].unique()), placeholder="Arsenal")
        team_id = team_to_id_dict[team]
        players = fetch_player_data(team, team_id)
        show_wages = st.radio("Show player wages", ["Yes", "No"])

        if players:
            styled_players, styled_players_wages = render_player_table(players, df_players_wages)
            if show_wages == "Yes":
                st.markdown(f'<p style="font-family:{fm_rubik}; font-size: 24px; color: wheat;">{team} Player Wages</p>', unsafe_allow_html=True)
                st.markdown(styled_players_wages.to_html(escape=False, index=False, bold_headers=True), unsafe_allow_html=True)
            else:
                st.write("Player Stats")
                st.markdown(styled_players.to_html(escape=False, index=False, bold_headers=True), unsafe_allow_html=True)
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

        df_team_stats = df_team_stats[(df_team_stats["season_id"] >= season_range[0]) & (df_team_stats["season_id"] <= season_range[1])]
        alt_chart, alt_chart2 = plot_home_away_goals(df_team_stats)

        st.altair_chart(alt_chart, use_container_width=True)
        st.altair_chart(alt_chart2, use_container_width=True)

if __name__ == "__main__":
    main()

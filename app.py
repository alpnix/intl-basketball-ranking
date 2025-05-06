import streamlit as st
import pandas as pd
import numpy as np
from math import ceil

st.write("## File Upload")
league_games = st.file_uploader(label="File for Domestic League Games", accept_multiple_files=True)
league_weight = st.slider("Weight for Domestic League Games", 0, 10, 1)

european_games = st.file_uploader(label="File for European Games", accept_multiple_files=True)
european_weight = st.slider("Weight for European Games", 0, 10, 2)

segment_input = st.text_input(
        "Enter Time Segment Weights (separated by commas) 👇",
    )

league_ratings = {}

if len(league_games) > 0:
    leagues_df = pd.DataFrame()
    for league_game in league_games: 
        league_df = pd.read_csv(league_game)
        league_df = league_df[['Date', 'Team', 'PTS', 'Opp', 'PTS.1']]
        league_name = league_game.name.split("_")[0]
        league_ratings[league_name] = 0
        league_df["League"] = league_name
        league_df = league_df.rename(columns={'PTS.1': 'PTS_Opp'})
        leagues_df = pd.concat([leagues_df, league_df])

    leagues_df["Weight"] = league_weight


if len(european_games) > 0: 
    europes_df = pd.DataFrame()
    for european_game in european_games:
        europe_df = pd.read_csv(european_game)
        europe_df = europe_df[['Date', 'Team', 'PTS', 'Opp', 'PTS.1']]
        europe_name = european_game.name.split("_")[0]
        europe_df["League"] = europe_name
        europe_df = europe_df.rename(columns={'PTS.1': 'PTS_Opp'})
        europes_df = pd.concat([europes_df, europe_df])

    europes_df["Weight"] = european_weight


if st.button("Rank teams", type="primary"):
    df = pd.concat([leagues_df, europes_df])

    df['Date'] = pd.to_datetime(df['Date'], format='%a %b %d %Y')
    df = df.sort_values(by=['Date'])
    start_date = df['Date'].iloc[0]
    df["Date_enum"] = df['Date'].apply(lambda x: (x - start_date).days + 1)
    df.reset_index(drop=True, inplace=True)

    st.write("## Colley Rankings")
    teams = sorted(set(df['Team']).union(set(df['Opp'])))
    team_indices = {team: i for i, team in enumerate(teams)}
    n = len(teams)

    segmentWeights = [1]

    if segment_input:
        try: 
            segmentWeights = [float(x.strip()) for x in segment_input.split(",")]
        except: 
            print("Invalid input for segment weights. Please enter integers separated by commas.")

    print(segmentWeights)

    C = 2 * np.eye(n) # diagonal initalized to 2 and incremented by games played, other entries will be updated to negative games played
    b = np.zeros(n) # later will be updated to 1 + (W-L)/2

    for _, row in df.iterrows():
        day = row['Date_enum']
        team = row['Team']
        opp = row['Opp']
        pts_team = row['PTS']
        pts_opp = row['PTS_Opp']
        weight = row.get('Weight', 1.0)

        lastDayOfSeason = df["Date_enum"].max()

        numberSegments = len(segmentWeights)
        weightIndex = ceil(numberSegments*((day)/(lastDayOfSeason))) - 1
        timeWeight = segmentWeights[weightIndex]

        # Uncomment the following line if you want to use a linear time weight
        # timeWeight = day/lastDayOfSeason

        weight *= timeWeight

        i = team_indices[team]
        j = team_indices[opp]

        C[i, i] += weight
        C[j, j] += weight
        C[i, j] -= weight
        C[j, i] -= weight

        if pts_team > pts_opp:
            b[i] += weight
            b[j] -= weight
        elif pts_team < pts_opp:
            b[i] -= weight
            b[j] += weight
    
    for i in range(n):
        b[i] = 1 + (b[i] / 2)

    r = np.linalg.solve(C, b)

    league_teams = set(leagues_df["Team"])
    ranking_increment = 1
    rankings = sorted(zip(teams, r), key=lambda x: x[1], reverse=True)
    for rank, (team, score) in enumerate(rankings, 1):
        if team in league_teams:
            teams_league = leagues_df[leagues_df["Team"] == team]["League"].values[0]
            league_ratings[teams_league] += score
            st.write(f"{ranking_increment}. {team}: {score:.4f}")
            ranking_increment += 1

    st.write("## League Ratings")
    for league, rating in league_ratings.items():
        st.write(f"{league}: {rating:.4f}")
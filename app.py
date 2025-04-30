import streamlit as st
import pandas as pd
import numpy as np

st.write("## File Upload")
league_games = st.file_uploader("File for Domestic League Games")
league_weight = st.slider("Weight for Domestic League Games", 0, 1, 0.5)

european_games = st.file_uploader("File for European Games")
european_weight = st.slider("Weight for European Games", 0, 1, 1.0)

if league_games is not None:
    league_df = pd.read_csv(league_games)

if european_games is not None:
    european_df = pd.read_csv(european_games)


if st.button("Rank teams", type="primary"):
    league_df = league_df[['Date', 'Team', 'PTS', 'Opp', 'PTS.1']]
    european_df = european_df[['Date', 'Team', 'PTS', 'Opp', 'PTS.1']]
    league_df = league_df.rename(columns={'PTS.1': 'PTS_Opp'})
    european_df = european_df.rename(columns={'PTS.1': 'PTS_Opp'})

    league_df["Weight"] = league_weight
    european_df["Weight"] = european_weight

    df = pd.concat([league_df, european_df])

    df['Date'] = pd.to_datetime(df['Date'], format='%a %b %d %Y')
    df = df.sort_values(by=['Date'])
    df.reset_index(drop=True, inplace=True)

    st.write("## Colley Rankings")
    teams = sorted(set(df['Team']).union(set(df['Opp'])))
    team_indices = {team: i for i, team in enumerate(teams)}
    n = len(teams)

    C = 2 * np.eye(n) # diagonal initalized to 2 and incremented by games played, other entries will be updated to negative games played
    b = np.zeros(n) # later will be updated to 1 + (W-L)/2

    for _, row in df.iterrows():
        team = row['Team']
        opp = row['Opp']
        pts_team = row['PTS']
        pts_opp = row['PTS_Opp']
        weight = row.get('Weight', 1.0)

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

    league_teams = set(league_df["Team"])
    ranking_increment = 1
    rankings = sorted(zip(teams, r), key=lambda x: x[1], reverse=True)
    for rank, (team, score) in enumerate(rankings, 1):
        if team in league_teams:
            st.write(f"{ranking_increment}. {team}: {score:.4f}")
            ranking_increment += 1
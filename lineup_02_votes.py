"""
Generate player votes database, containing votes for Serie A matchday and player.

Votes data is downloaded from https://www.fantacalcio.it/voti-fantacalcio-serie-a

Serie A calendar is loaded from another file, to add information not containing in votes files: home/away, team opponent.
"""
import os
import requests
import pandas as pd
import numpy as np

# Need to be updated manually when they expire
COOKIES = {
    'fantacalcio.it': 'MIHk4NLeeHZtP%2B2Jh4LwTia4Co99jgjt8cJVthlXYOMXRdKrVtwhooVC3UKVOdQcPNKu6XV4CSnZnA7erB8FSgI5eHmFsJTPJStTBjCnIMHeglZ3Y5w90w8QAzcsRU0Y1H0AskOsiat2e9dzizgDEaPoXIekH2%2BZ2wK65qAQ8K3g%2Fwp2Dr%2BdSiVJw%2FDlE9clcScehnX30ipdLezQBslXTBgM%2B9uoYt3XD9Qiq52fUTzplMzdgyGag8qYlPa%2FXbJHCucCIa7BEz5XBqoRxj8cGCLPbO9eS9rMDOhpYvthBOwtov9EPEbwIv6e%2FDoJQY0PTwOCuL6PfuwQuUECIrH3cMWvnavMNdbKjJG4IaSFKQNszmfHOtH4DxeYpvpQPJNaxkLIVpILNfmspOiyQg9kFFbs1NrmauOCwohUDrZvJnjlnbqsjoZqeo%2BCnr7r7HWH%2F%2BagHEBd%2BU3D8auvn18fSfAHZHlx1QmSttlgx9uIQyJxA4ILwa%2BpDA%3D%3D'
}


def get_votes(giornata, year, cookies):
    """ Function to get the votes of "giornata"."""
    year_id = {
        2022: 17,
        2023: 18
        }
    folder = f'votes/{year}'
    file_path = f'{folder}/giornata_{giornata}.xlsx'
    if not os.path.exists(folder):
        # if the directory is not present then create it.
        os.makedirs(folder)

    url = f"https://www.fantacalcio.it/api/v1/Excel/votes/{year_id[year]}/{giornata}"
    response = requests.get(url, cookies=cookies)

    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Excel file downloaded successfully for giornata {giornata} year {year}.")
    else:
        print(f"Failed to download the Excel file for giornata {giornata} year {year}.")

    return file_path


def home_away_oponent(calendar, team, giornata):
    """ Get the calendar, team and matchday and return 
    a flag 1/0 if home/away and the oponent
    """
    cal = calendar[calendar['matchday'] == giornata]
    if team in cal["team1"].values:
        home = 1
        oponent = cal["team2"][cal["team1"] == team]
    elif team in cal["team2"].values:
        home = 0
        oponent = cal["team1"][cal["team2"] == team]
    else:
        raise ValueError(f"The team {team} is not valid for this year for giornata {giornata}.")

    return home, oponent.values[0]


def process_votes(votes_path, calendar_df):
    """Process the votes file to extract into a df."""
    rx = np.array(pd.read_excel(votes_file, header = None, skiprows=4))

    # Get rid of the rows that contain 6* as value
    rx = np.delete(rx, np.where(rx[:, 3] == '6*')[0], axis=0)

    dfs = []

    team, j = None, None
    for i in range(rx.shape[0]):
        value_first_col = rx[i, 0]
        if isinstance(rx[i, 0], str) or i+1 == rx.shape[0]:
            if value_first_col == "Cod.":
                columns = rx[i]
                continue
            else:
                if i != 0: # To avoid calling the function the first time
                    cur_df = pd.DataFrame(rx[j+2:i], columns=columns)
                    cur_df['matchday'] = matchday
                    cur_df['team'] = team
                    dfs.append(cur_df)
                team = value_first_col
                j = i

    # Merge DataFrames into one
    merged_df = pd.concat(dfs, ignore_index=True)
    merged_df['Voto'] = merged_df['Voto'].astype(float)

    # Remove the coaches (Allenatori)
    merged_df = merged_df[merged_df['Ruolo'] != "ALL"]

    # Final cleaning
    merged_df = merged_df.rename(columns={'Nome': 'player',
                                  'Voto': 'vote',
                                  'Ass': 'assists'})

    merged_df['goals'] = merged_df['Gf'] + merged_df['Rs'] - merged_df['Gs']
    merged_df['cards_malus'] = merged_df['Amm'] * 0.5 + merged_df['Esp']
    merged_df['goals_gen'] = merged_df['goals'] * 3
    merged_df['goals_gen'] = merged_df['goals'][merged_df['goals_gen'] < 0]
    merged_df['fantavote'] = merged_df['vote'] + merged_df['goals_gen'] + merged_df['assists'] - merged_df['cards_malus']

    # Get calendar info
    merged_df[['home', 'opponent']] = merged_df.apply(lambda row: pd.Series(home_away_oponent(calendar_df, row['team'], row['matchday'])), axis=1)

    return merged_df


if __name__ == '__main__':
    year = 2022

    cal_df = pd.read_excel(f'calendar/{year}-{year+1}.xlsx')

    dfs = []
    for matchday in range(38):
        matchday += 1 # Matchdays are 1 based

        votes_file = get_votes(matchday, year, COOKIES)

        votes = process_votes(votes_file, cal_df)
        dfs.append(votes)

        print('loaded votes for matchday ' + str(matchday))

    df = pd.concat(dfs, ignore_index=True)
    df.to_excel(f'votes/{year}/players_votes.xlsx')



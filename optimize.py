import pandas as pd
from pulp import LpMaximize, LpProblem, LpStatus, lpSum, LpVariable, LpBinary

def clean_df(fit_price_df:pd.DataFrame, excluded_players:set=set()) -> pd.DataFrame:
    """Clean the DataFrame

    Args:
        fit_price_df (pd.DataFrame): dataframe containing the price and fitness data
        excluded_players (set): set containing the players not longer available

    Returns:
        pd.DataFrame: same DataFrame but clean
    """
    #  Clean the players that are not longer available and the ones lacking data
    df = fit_price_df[~fit_price_df["Nome"].isin(excluded_players)]
    df = df[df["500K (8)"].notna()]
    
    # Set the name as the index
    df.index = df["Nome"]
    
    return df


def optimize_for_price(df:pd.DataFrame, player_constraints:dict):
    """
    """
    # Create the model
    model = LpProblem(name="fitness-price-balance", sense=LpMaximize)

    # Create binary variables for player selection
    players = df.index
    player_vars = LpVariable.dicts("Player", players, 0, 1, LpBinary)

    # # Define the optimize function
    model += lpSum(df["Fitness"][i] * player_vars[i] for i in players)

    # Create vectors for the different possitions
    df["GK"] = df["Ruolo"] == "POR"
    df["FWD"] = df["Ruolo"] == "ATT"
    df["DEF"] = df["Ruolo"] == "DIF"
    df["MID"] = df["Ruolo"].isin(["CEN", "TRQ"])

    # Add constraints
    model += lpSum(player_vars[i] for i in players if df["GK"][i]) >= player_constraints["num_gk"]
    model += lpSum(player_vars[i] for i in players if df["DEF"][i]) >= player_constraints["num_def"]
    model += lpSum(player_vars[i] for i in players if df["MID"][i]) >= player_constraints["num_mid"]
    model += lpSum(player_vars[i] for i in players if df["FWD"][i]) >= player_constraints["num_fwd"]

    model += lpSum(player_vars[i] for i in players if df["GK"][i]) <= player_constraints["num_gk_max"]
    model += lpSum(player_vars[i] for i in players if df["DEF"][i]) <= player_constraints["num_def_max"]
    model += lpSum(player_vars[i] for i in players if df["MID"][i]) <= player_constraints["num_mid_max"]
    model += lpSum(player_vars[i] for i in players if df["FWD"][i]) <= player_constraints["num_fwd_max"]

    model += lpSum(df["500K (8)"][i] * player_vars[i] for i in players if df["GK"][i]) <= player_constraints["min_budg_gk"]
    model += lpSum(df["500K (8)"][i] * player_vars[i] for i in players if df["GK"][i]) <= player_constraints["min_budg_def"]
    model += lpSum(df["500K (8)"][i] * player_vars[i] for i in players if df["GK"][i]) <= player_constraints["min_budg_mid"]
    model += lpSum(df["500K (8)"][i] * player_vars[i] for i in players if df["GK"][i]) <= player_constraints["min_budg_fwd"]

    model += lpSum(df["500K (8)"][i] * player_vars[i] for i in players) <= player_constraints["budget"]

    # Solve the linear program
    model.solve()

    # Display the selected players
    selected_players = [i for i in players if player_vars[i].value() == 1]

    return cleaned_df[cleaned_df.index.isin(selected_players)]

if __name__ == '__main__':
    # Read the file
    fitness_price_df = pd.read_excel('fit_price.xlsx')
    player_constraints = {
        "num_gk": 1,
        "num_def": 3,
        "num_mid": 4,
        "num_fwd": 3,
        "num_gk_max": 1,
        "num_def_max": 5,
        "num_mid_max": 6,
        "num_fwd_max": 4,
        "min_budg_gk": 30,
        "min_budg_def": 80,
        "min_budg_mid": 140,
        "min_budg_fwd": 100,        
        "budget": 450
    }

    cleaned_df = clean_df(fitness_price_df)

    players = optimize_for_price(cleaned_df, player_constraints)
    print(players)
    
    players.to_excel('players_tobuy.xlsx')


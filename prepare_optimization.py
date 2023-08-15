import pandas as pd

def join_excels(fitness_excel:str, price_excel:str, mapp:pd.DataFrame=None) -> pd.DataFrame:
    """Load and join by name the two excel files into a DataFrame.

    Args:
        fitness_excel (str): path to the excel file containing fitness info.
        price_excel (str): path to the excel file containing price info.
        mapp (pd.DataFrame, optional): mapping to hepl in the join. Defaults to None.

    Returns:
        pd.DataFrame: joined DataFrame
    """

    # Read the dfs
    fitness_df = pd.read_excel(fitness_excel)
    price_df = pd.read_excel(price_excel)
    # If mapping is provided, use it to improve the join
    if mapp is not None:
        price_df = price_df.merge(mapp, how='left', left_on='Nome', right_on='Nome_prices')
        price_df['Nome'] = price_df['Nome_y'].combine_first(price_df['Nome_x'])

    price_df['Nome'] = price_df['Nome'].str.upper().str.strip(' -')
    print(price_df['Nome'])

    # Create the merged df
    return fitness_df.merge(price_df, how='left', on='Nome')

merged = join_excels('players.xlsx', 'price_fanta.xlsx')

# Check how many are wrongly mapped and extract them into a file
print(sum(merged["RT"].isna()))
merged["Nome"][merged["RT"].isna()].to_excel("not_mapped.xlsx", index=False)


# After MANUALLY putting the correct names, load the file
mapping = pd.read_excel("corrected_mapping.xlsx")

# Do the merge again using the mapping as help
merged = join_excels('players.xlsx', 'price_fanta.xlsx', mapping)

# Save the final excel
merged.to_excel('fit_price.xlsx', index=False)
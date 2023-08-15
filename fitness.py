import time
from random import randint
import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm



def get_players(rol: str) -> list:
    """Retrieve a list of players' links from a Fantacalcio website based on the provided role.

    Args:
        rol (str): The role of the players (e.g., "Portieri", "Difensori", "Centrocampisti"...).

    Returns:
        list: A list of URLs representing players' profiles.
    """
    base_url = "https://www.fantacalciopedia.com/lista-calciatori-serie-a"
    html = requests.get(f"{base_url}/{rol.lower()}/", timeout=10)
    soup = BeautifulSoup(html.content, "html.parser")
    players = set()
    all_players = soup.find_all("article")
    for player in all_players:
        player = player.find("a").get("href")
        players.add(player)

    return players


def get_attributes(url: str) -> dict:
    """
    Retrieve player attributes from a Fantacalcio player profile page.

    Args:
        url (str): The URL of the player's profile page.

    Returns:
        dict: A dictionary containing various attributes of the player.
    """
    # Introduce a random delay to avoid overwhelming the server
    time.sleep(randint(0, 2000) / 2000)
    attributes = {}
    html = requests.get(url.strip(), timeout=100)
    soup = BeautifulSoup(html.content, "html.parser")

    # Extract player name
    attributes["Nome"] = soup.find("h1", class_="panel-title").get_text().strip()

    # Extract player's score
    selector = "div.col_one_fourth:nth-of-type(1) span.stickdan"
    attributes["Punteggio"] = soup.select_one(selector).text.strip().replace("/100", "")

    # Extract average scores for each year
    selector = "div.col_one_fourth:nth-of-type(n+2) div"
    average = [el.find("span").text.strip() for el in soup.select(selector)]
    presences = [el.find("span", class_="rouge").text.strip() for el in soup.select(selector)]
    years = [
        el.find("strong").text.split(" ")[-1].strip() for el in soup.select(selector)
    ]

    for i, _ in enumerate(years):
        attributes[f"Fantamedia anno + {i}"] = average[i]
        attributes[f"Presences anno + {i}"] = presences[i]

    # Get presences, fantamedia and FM/all presences
    # selector = "div.col_one_third:nth-of-type(2) div"
    # stats_last_year = soup.select_one(selector)
    # parameters = [
    # " ".join(el.text.strip().split(" ")[:-1]) + " + 0" for el in stats_last_year.find_all("strong")
    # ]
    # values = [el.text.strip() for el in stats_last_year.find_all("span")]
    # attributes.update(dict(zip(parameters, values)))

    # Presences, foreseen goals and assists
    selector = ".col_one_third.col_last div"
    stats_forseen = soup.select_one(selector)
    parameters = [
        el.text.strip().replace(":", "") for el in stats_forseen.find_all("strong")
    ]
    values = [el.text.strip() for el in stats_forseen.find_all("span")]
    attributes.update(dict(zip(parameters, values)))

    # Extract player's role
    selector = ".label12 span.label"
    ruolo = soup.select_one(selector)
    attributes["Ruolo"] = ruolo.get_text().strip()

    # Extract player's skills
    selector = "span.stickdanpic"
    skills = [el.text for el in soup.select(selector)]
    attributes["Skills"] = skills

    # Extract investment percentage (Buon investimento)
    selector = "div.progress-percent"
    investimento = soup.select(selector)[2]
    attributes["Buon investimento"] = investimento.text.replace("%", "")

    # Extract injury resistance percentage (Resistenza infortuni)
    selector = "div.progress-percent"
    investimento = soup.select(selector)[3]
    attributes["Resistenza infortuni"] = investimento.text.replace("%", "")

    # Check for recommended and injury icons
    selector = "img.inf_calc"
    icon = soup.select_one(selector)
    attributes["Consigliato prossima giornata"] = False
    attributes["Infortunato"] = False
    if icon:
        icon_text = icon.get("title")
        if "Consigliato per la giornata" in icon_text:
            attributes["Consigliato prossima giornata"] = True
        elif "Infortunato" in icon_text:
            attributes["Infortunato"] = True

    # Check if player is a new acquisition
    selector = "span.new_calc"
    new = soup.select_one(selector)
    if new is not None:
        attributes["Nuovo acquisto"] = True
    else:
        attributes["Nuovo acquisto"] = False

    # Extract player's team
    selector = "#content > div > div.section.nobg.nomargin > div > div > div:nth-child(2) > div.col_three_fifth > div.promo.promo-border.promo-light.row > div:nth-child(3) > div:nth-child(1) > div > img"
    squadra = soup.select_one(selector).get("title").split(":")[1].strip()
    attributes["Squadra"] = squadra

    # Extract player's trend (UP, DOWN, STABLE)
    selector = "div.col_one_fourth:nth-of-type(n+2) div"
    trend_box = soup.select(selector)[0].find("i")
    if trend_box:
        trend = trend_box.get("class")[1]
        if trend == "icon-arrow-up":
            attributes["Trend"] = "UP"
        else:
            attributes["Trend"] = "DOWN"
    else:
        attributes["Trend"] = "STABLE"

    # Extract player's current season appearances
    selector = "div.col_one_fourth:nth-of-type(2) span.rouge"
    current_presences = soup.select_one(selector).text
    attributes["Presenze campionato corrente"] = current_presences

    return attributes


def compute_fitness(row: pd.DataFrame, max_presences: int) -> float:
    """_summary_

    Args:
        row (pd.DataFrame): _description_
        max_presences (int): _description_

    Returns:
        float: _description_
    """
        # fitness =( Fantamedia anno scorso * Partite giocate anno scorso/38 * peso
    #         + Fantamedia anno corrente * Partite giocate anno corrente/giornata * 100-peso ) * 5
    #         * FANTACALCIOPEDIA_score/100
    #         + skills + altri parametri

    fitness = 0
    # Weighted fantamedia average
    fm_last_y = float(row["Fantamedia anno + 1"])
    presences_last_y = float(row["Presences anno + 1"])
    fm_this_y = float(row["Fantamedia anno + 0"])
    presences_this_y = float(row["Presences anno + 0"])

    if max_presences >= 3:

        if presences_last_y > 0:
            fitness += fm_last_y * presences_last_y / 38 * 0.2
            fitness += fm_this_y * presences_this_y / max_presences * 0.8

        else:
            fitness += fm_this_y * presences_this_y / max_presences * 1
    else:
        fitness = fm_last_y * presences_last_y / 38

    # Include the Fantamedia estimation from the FANTACALCIOPEDIA
    fcp_score = float(row['Punteggio'])
    fitness = fitness * 5 * fcp_score / 100

    # skills
    values = row["Skills"]
    for skill in values:
        fitness += SKILLS[skill]

    if row["Nuovo acquisto"]:
        fitness -= 2
    if int(row["Buon investimento"]) == 60:
        fitness += 3
    if row["Consigliato prossima giornata"]:
        fitness += 1
    if row["Trend"] == "UP":
        fitness += 2
    if row["Infortunato"]:
        fitness -= 1
    if int(row["Resistenza infortuni"]) > 60:
        fitness += 4
    if int(row["Resistenza infortuni"]) == 60:
        fitness += 2

    return fitness


def get_fitness(df: pd.DataFrame) -> pd.DataFrame:
    """_summary_

    Args:
        df (pd.DataFrame): _description_

    Returns:
        pd.DataFrame: _description_
    """
    # Cleaning
    for col in df.columns:
        df.loc[df[col] == "nd", col] = 0

    max_presences = df["Presenze campionato corrente"].astype(int).max()
    return df.apply(compute_fitness, args=(max_presences,), axis=1)


if __name__ == "__main__":
    ROLS = ["Portieri", "Difensori", "Centrocampisti", "Trequartisti", "Attaccanti"]
    SKILLS = {
        "Fuoriclasse": 1,
        "Titolare": 3,
        "Buona Media": 2,
        "Goleador": 4,
        "Assistman": 2,
        "Piazzati": 2,
        "Rigorista": 5,
        "Giovane talento": 2,
        "Panchinaro": -4,
        "Falloso": -2,
        "Outsider": 2,
    }
    OUTPUT_XLSX = "players.xlsx"

    # Get the player URLs
    player_urls = set()
    for rol in ROLS:
        player_urls = player_urls.union(get_players(rol))
    print(f"{len(player_urls)} URLs extracted")

    players = []
    for url in tqdm(player_urls):
        player = get_attributes(url)
        players.append(player)
    df = pd.DataFrame.from_dict(players)
    df.to_excel(OUTPUT_XLSX, index=False, sheet_name="attributes")
    print("Attributes written")

    df["Fitness"] = get_fitness(df)

    # # Resuffle the columns and sort
    # temp = df.columns
    # df = df[
    #     [
    #         temp[11],
    #         temp[0],
    #         temp[18],
    #         temp[1],
    #         temp[21],
    #         temp[19],
    #         temp[12],
    #         temp[20],
    #         temp[6],
    #         temp[2],
    #         temp[5],
    #         temp[7],
    #         temp[3],
    #         temp[4],
    #         temp[16],
    #         temp[17],
    #         temp[8],
    #         temp[9],
    #         temp[10],
    #         temp[13],
    #         temp[14],
    #         temp[15],
    #     ]
    # ]
    df.sort_values(by="Fitness", ascending=False)

    # Print to the excel
    df.to_excel(OUTPUT_XLSX, index=False, sheet_name="fitness")


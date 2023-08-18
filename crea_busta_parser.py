"""
Script to parse the players in the "crea-busta" page to save them in an excel file.
"""
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd


def chrome_appdata_folder():
    """Return the appdata folder for chrome."""
    return os.getenv('LOCALAPPDATA') + r'\Google\Chrome'


def start_driver():
    """Start the driver. Optionally a download folder can be supplied."""
    # Initialise the chrome options
    chromeOptions = webdriver.ChromeOptions()
    prefs = {"profile.default_content_setting_values.notifications": 2} # Disable notifications

    # Get the appData folder to store the user
    app_data = chrome_appdata_folder()
    chromeOptions.add_argument(f"user-data-dir={app_data}/Selenium/profile")

    # Apply the options
    chromeOptions.add_experimental_option("prefs", prefs)

    # Initialize the driver
    ChromeDriverManager().install()

    return webdriver.Chrome(options=chromeOptions)


def fantacalcio_login(driver, usr=None, psw=None, autologin=False):
    """Fill the email and password in Salesforce to make the login."""
    driver.get('https://leghe.fantacalcio.it/far-west-league/area-gioco/crea-busta')


def next_page(driver):
    """Select the "next" icon to go to the next page."""
    # Locate the <a> element with data-paginator="next" using a CSS selector
    next_button_selector = 'a[data-paginator="next"]'
    
    # Wait for the element to be clickable
    wait = WebDriverWait(driver, 10)
    next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, next_button_selector)))

    # Get the parent <li> element
    parent_li = next_button.find_element(By.XPATH, './ancestor::li')

    # Check if the parent <li> has the class "dissabled"
    if "disabled" not in parent_li.get_attribute("class"):
        # Click the element
        next_button.click()
        return True
    else:
        return False


def parse_current_page(driver):
    """Parse the current page to extract the player and the value."""
    html = driver.page_source
    # Create a Beautiful Soup object
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')

    data = []
    for row in table.find_all('tr'):
        cells = row.find_all('td')  # Include header cells (th) as well
        row_data = []
        for cell in cells:
            span = cell.find('span')
            if span:
                input_elem = span.find('input')
                if input_elem:
                    cell_value = input_elem.get('value', '')
                    row_data.append(cell_value)
                else:
                    row_data.append(cell.get_text(strip=True))
        if len(row_data) == 5:
            data.append(row_data)

    # Convert data into a Pandas DataFrame
    headers = ["posizione", "calciatore", "squadra", "games", "prezzo"]
    df = pd.DataFrame(data, columns=headers)
    df["prezzo"] = df["prezzo"].astype(int)
    return df


def parse_all_tables(driver):
    """Keep pressing next until it is not available and parse all the tables."""
    driver.get('https://leghe.fantacalcio.it/far-west-league/area-gioco/crea-busta')
    dfs = []
    while True:
        dfs.append(parse_current_page(driver))
        if not next_page(driver):
            break
    return pd.concat(dfs, ignore_index=True)


def parse_le_tue_buste(driver):
    """Parse the current page to extract the player and the value."""
    driver.get("https://leghe.fantacalcio.it/far-west-league/area-gioco/mercato-buste")
    html = driver.page_source
    # Create a Beautiful Soup object
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find_all('table')[1]

    data = []
    for row in table.find_all('tr'):
        cells = row.find_all('td')  # Include header cells (th) as well
        row_data = []
        for cell in cells:
            span = cell.find('span')
            if span:
                input_elem = span.find('input')
                if input_elem:
                    cell_value = input_elem.get('value', '')
                    row_data.append(cell_value)
                else:
                    row_data.append(cell.get_text(strip=True))
        row_data = row_data[1:-1]
        if len(row_data) == 3:
            data.append(row_data)
    # Convert data into a Pandas DataFrame
    headers = ["calciatore", "squadra", "offerta"]
    df = pd.DataFrame(data, columns=headers)
    return df


def parse_altre_buste(driver):
    """Parse the current page to extract the player and the value."""
    driver.get("https://leghe.fantacalcio.it/far-west-league/area-gioco/mercato-buste")
    html = driver.page_source
    # Create a Beautiful Soup object
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find_all('table')[2]

    data = []
    for row in table.find_all('tr'):
        cells = row.find_all('td')  # Include header cells (th) as well
        row_data = []
        for cell in cells:
            span = cell.find('span')
            if span:
                input_elem = span.find('input')
                if input_elem:
                    cell_value = input_elem.get('value', '')
                    row_data.append(cell_value)
                else:
                    row_data.append(cell.get_text(strip=True))
        row_data = row_data[1:-2]
        if len(row_data) > 0:
            data.append(row_data)

    # Convert data into a Pandas DataFrame
    headers = ["calciatore", "squadra"]
    df = pd.DataFrame(data, columns=headers)
    return df



if __name__ == '__main__':
    driver = start_driver()
    fantacalcio_login(driver)

    df = parse_all_tables(driver)

    df.to_excel('buste_prices.xlsx')

    le_tue_buste = parse_le_tue_buste(driver)
    altre_buste = parse_altre_buste(driver)

    # Extract the best "free" players
    df["free"] = ~df['calciatore'].isin(altre_buste["calciatore"])
    free = df.sort_values(by='prezzo', ascending=False)

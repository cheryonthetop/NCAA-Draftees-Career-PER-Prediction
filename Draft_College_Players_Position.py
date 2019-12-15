from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd

def remove_special_characters(str):
    '''
    Given a string, remove all special characters and return the string with ONLY alphabets and in lower case
    '''
    str=str.lower()
    for s in str:
        if s not in ('qwertyuiopasdfghjklzxcvbnm'): # 26 alphabets
            str=str[:str.index(s)]+str[str.index(s)+1:]
    return str

'''
# url that we are scraping
url = "https://www.basketball-reference.com/players/w/willima01.html"

# this is the html from the given url
html = urlopen(url)

# create a BeautifulSoup object by passing through html to the BeautifulSoup() constructor.
# lxml is a html parser
soup = BeautifulSoup(html, 'lxml')

# We are only scraping career per here
column_header = ['Position']

# Find the position
data_rows = soup.findAll('p')

positions=[]
for i in range(len(data_rows)):  # Iterating through all 'div' tags
    text=data_rows[i].getText()
    if "Position:" in text:
        if "Guard" in text or "Small Forward" in text:
            positions.append('Perimeter')
        else:
            positions.append('Interior')
        break
df = pd.DataFrame(positions,columns=column_header)
#print(df)
'''

# Above is my experiment with a single player, let's turn to all players


# First we will need all the players that are drafted who also went to college
# Import the dataframe we had from a csv I created from another data scraping effort
df_players = pd.read_csv('PER_data_1996_to_2014.csv')
# Create template for bball reference url
url_template = "https://www.basketball-reference.com/players/{first_letter_of_last_name}/{first_5_letters_of_last_name}{first_2_letters_of_first_name}0{number}.html"
# Initialization
url = None
soup = None
positions = []

for k in range(df_players.shape[0]):
    try:
        year = df_players.Draft_Yr[k]  # Year of the draft
    except Exception:
        break
    player = df_players.Player[k]  # Player name
    print(player)
    player_names=player.split(' ') # Players with a name like Luc Mbah a Moute give us a headache
    first_name=''
    last_name=''
    for l in range(len(player_names)):
        if l == 0:
            first_name = player_names[l]
        else:
            last_name = last_name+player_names[l]
    first_name_cleaned=remove_special_characters(first_name) #Need to treat the special cases like D'Angelo. This also convert all characters to lower cases
    last_name_cleaned=remove_special_characters(last_name)
    first_letter_of_last_name = last_name_cleaned[0]
    first_5_letters_of_last_name = last_name_cleaned[:5]
    first_2_letters_of_first_name = first_name_cleaned[:2] # Let's hope we won't have a player with a one-letter first name

    flag = False # Players like Joe Jackson and Josh Jackson have the same url, we are forced to check several urls using a while loop
    number = 0 # This number is used for the url name
    # We limit our attempt to 5 times: players like Ron Artest and Mo Williams are impossible to scrape as they have multiple names
    # and the url is not predictable at all. So we want to avoid an infinite loop
    while flag == False and number < 5:
        number += 1

        # Modifying template
        url = url_template.format(first_letter_of_last_name=first_letter_of_last_name,
                                  first_5_letters_of_last_name=first_5_letters_of_last_name,
                                  first_2_letters_of_first_name=first_2_letters_of_first_name,
                                  number=number)  # get the url
        try:
            html = urlopen(url)  # a weird phenomenon with the url of bballreference forces us to do this,
            # see P.J. Hairston to understand this: the url is ...02, ...not 01 without any reasons.
        except Exception:
            continue

        soup = BeautifulSoup(html, 'html5lib')  # create our BS object
        # we check the year of draft here for the true identity of the given player
        # we pray that no two players in the same draft year have the same name
        for p in soup.findAll('p'):
            for a in p.findAll('a'):
                if ' NBA Draft' in a.getText():
                    if str(year) in a.getText():
                        flag = True

    # Sometimes we just cannot get the correct URL because for example a player
    # changes his name in the middle of his career, we leave these to manual efforts
    # and append a placeholder here
    try:
        html = urlopen(url)
    except:
        positions.append([])
        continue

    data_rows = soup.findAll('p')
    for i in range(len(data_rows)):  # Iterating through all 'div' tags
        text = data_rows[i].getText()
        if "Position:" in text:
            if "Guard" in text or "Small Forward" in text:
                positions.append(['Perimeter'])
                print("Perimeter")
            else:
                positions.append(['Interior'])
                print("Interior")
            break

df_positions = pd.DataFrame(positions,columns=['Position'])
final_df = df_players.join(df_positions) # Now we produce a data frame with player names, college, AND PER!

print(final_df)

final_df.to_csv("Player_Positions.csv")

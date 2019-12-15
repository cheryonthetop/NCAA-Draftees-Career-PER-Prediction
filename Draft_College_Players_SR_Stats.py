from urllib.request import urlopen
from bs4 import BeautifulSoup
from bs4 import Comment
import pandas as pd



def remove_special_characters(str):
    '''
    Given a string, remove all special characters and return the string with ONLY alphabets and in lower case
    '''
    str=str.lower()
    for s in str:
        if s not in ('qwertyuiopasdfghjklzxcvbnm -'): # 26 alphabets and space and dash, which we do not include as special character
            str=str[:str.index(s)]+str[str.index(s)+1:]
    return str

def add_dash(str):
    '''
    :param str:
    :return: replace space str with underscores
    '''
    return str.replace(' ', '-')


# Read the Training Data
training_data = pd.read_csv('PER_data_1996_to_2014.csv')
# Just making sure we are getting the data
# print(training_data.head(5))

# Initialization
html = None
soup = BeautifulSoup()
stats_per_game_all = []
stats_advanced_all = []

# column header of per game statistics
# The line below gets us the column_headers
# column_headers_per_game = [th.getText() for th in soup.find('thead').find('tr').findAll('th')]
column_headers_per_game = ['Season', 'School', 'Conf', 'G', 'GS', 'MP',
                           'FG', 'FGA', 'FG%', '2P', '2PA', '2P%', '3P',
                           '3PA', '3P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB',
                           'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS',
                           '\xa0', 'SOS']
# There is a weird element '\xa0' but we don't worry about it
# We do not want the Season column because the HTML structure makes it more
# trouble to extract the data, plus knowing the season is useless anyway
column_headers_per_game.pop(0)

# For some reason, the advanced stats for players drafted after 2011 is different than before
# This is the column header for advanced stats after 2011
column_headers_advanced = ['Season', 'School', 'Conf', 'G', 'GS', 'MP',
                           'PER', 'TS%', 'eFG%', '3PAr', 'FTr', 'PProd',
                           'ORB%', 'DRB%', 'TRB%', 'AST%', 'STL%', 'BLK%',
                           'TOV%', 'USG%', '', 'OWS', 'DWS', 'WS', 'WS/40',
                           '', 'OBPM', 'DBPM', 'BPM']
# We do not want the Season column because the HTML structure makes it more
# trouble to extract the data, plus knowing the season is useless anyway
column_headers_advanced.pop(0)

# url template
url_template = "https://www.sports-reference.com/cbb/players/{NAME}-{ID}.html"

for k in range(training_data.shape[0]):
    # modifies url_template:

    # the actual url takes the form of for example james-harden-1
    player = training_data.Player[k]
    print(player)

    # first we remove the special character in player's name like P.J. Hairston
    player_no_special_character = remove_special_characters(player)

    # then we add dashes in player's name
    player_dash = add_dash(player_no_special_character)

    # we add a verifier (draft year) for the player because there are lots of players
    # with the same name in the sports reference database, but the ID part of the template is random

    flag = False
    number = 0  # This number is used for the url name
    # We limit our attempt to 5 times: players like Ron Artest and Mo Williams are impossible to scrape as they have multiple names
    # and the url is not predictable at all. So we want to avoid an infinite loop
    while flag == False and number < 5:
        number += 1
        url = url_template.format(NAME = player_dash,
                                  ID = number)  # get the url
        try:
            html = urlopen(url)  # a weird phenomenon with the url of sports reference forces us to do this,
            # see Thomas Robinson to understand this: the url is ...02, ...not 01 without any reasons.
            soup = BeautifulSoup(html, 'lxml')
        except Exception:
            continue

        # we use the draft year as verifier to distinguish players that have same name
        # (see Gerald Henderson for example)

        # the last season of the player's college year should the the draft year
        # e.g 2018-19 Zion Williamson's draft year is 2019
        final_season = soup.find('tbody').findAll('tr')[-1].find('th').getText()
        final_year = int(final_season[:4]) + 1

        if final_year == training_data.Draft_Yr[k] or player == 'P.J. Hairston':
            flag = True

    # In case of players like Luc Richard Mbah Moute whose name does not fit our
    # training data, we ignore them and address them manually later
    try:
        html = urlopen(url)
    except:
        stats_per_game_all.append([' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                   ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                   ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                   ' ', ' ', ' ', ' '])
        stats_advanced_all.append([' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                   ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                   ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                   ' ', ' ', ' ', ' '])
        continue

    # Retrieving the per game statistics
    stats_per_game = [td.getText() for td in soup.find('tfoot').find('tr').findAll('td')]
    stats_per_game_all.append(stats_per_game)

    # Now we want some of that advanced stats
    # Weirdly enough, all the advanced statistics are included as comments in the HTML file
    # Ergo we need to use the below in order to parse through the comments

    # Getting a list of comments
    comments = soup.findAll(text=lambda text:isinstance(text, Comment))
    for c in comments:
        data = BeautifulSoup(c,"lxml")
        # The for loop is confusing here but we are lack of a better way
        # We actually only have one element to iterate through
        for items in data.select("table#players_advanced"):
            # Retrieving the advanced statistics
            stats_advanced = [item.get_text(strip=True) for item in items.find("tfoot").find("tr").select("td")]

            # data must be tended further if draft year is before 2011
            # specfically, PER, OBPM, DBPM, BPM and an empty column are missing
            # we insert blank into respective positions as place holders
            if training_data.Draft_Yr[k] < 2011:
                stats_advanced.insert(5, '')
                for i in range(4):
                    stats_advanced.append('')

            # There are always cases that drive us nuts
            # See the url for joe harris for example
            # We leave these to manual effort later
            if len(stats_advanced) != 28:
                stats_advanced = [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                   ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                   ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ',
                                   ' ', ' ', ' ', ' ']
            stats_advanced_all.append(stats_advanced)
            break

# Constructing the data frame
df_per_game = pd.DataFrame(stats_per_game_all, columns=column_headers_per_game)
df_advanced = pd.DataFrame(stats_advanced_all, columns=column_headers_advanced)

# Some columns are redundant because they are already in per game stats
df_advanced = df_advanced.drop(columns=['School', 'Conf', 'G', 'GS', 'MP'])

# Combining the data frames for both regular(per game) and advanced stats
df_stats_players = pd.DataFrame.join(df_per_game,df_advanced)
# Get the player names
df_stats_players = pd.DataFrame(training_data.Player).join(df_stats_players)
df_stats_players = df_stats_players.drop(columns=['School','Conf','G','GS','PER','PProd','ORB%','DRB%','STL%','OBPM','DBPM','BPM'])
print(df_stats_players.head(5))
print(df_stats_players.columns)

#df_stats_players.to_csv("drafted_players_stats_1996_to_2014.csv")         

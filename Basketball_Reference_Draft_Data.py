from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd

# url that we are scraping
url = "http://www.basketball-reference.com/draft/NBA_2014.html"

# this is the html from the given url
html = urlopen(url)

# create a BeautifulSoup object by passing through html to the BeautifulSoup() constructor.
# lxml is a html parser
soup = BeautifulSoup(html, 'lxml')

# extracts the column headers we want
column_headers = [th.getText() for th in soup.findAll('tr', limit=2)[1].findAll('th')]

# Rk and Pk are redundant
# More importantly, the HTML script does not have text for Rk
column_headers.pop(0)

# skip the first 2 header rows
data_rows = soup.findAll('tr')[2:]

# extracts the player data in the form of a 2D matrix
player_data = [[td.getText() for td in data_rows[i].findAll('td')] for i in range(len(data_rows))]

# Constructing the data frame (2D tabular data structure)
df = pd.DataFrame(player_data, columns=column_headers)

# head() lets us see the 1st 5 rows of our DataFrame by default
print(df.head())

# Getting rid of the useless rows (the 2 rows between 1st rounders and 2nd rounders)
df = df[df.Player.notnull()]

# Renaming the column
df.rename(columns={'WS/48':'WS_per_48'}, inplace=True)

# get the column names and replace all '%' with '_Perc'
df.columns = df.columns.str.replace('%', '_Perc')

# We want to distinguish between career and per game stats
# so we get the columns we want by slicing the list of column names
# and then replace them with the appended names
df.columns.values[14:18] = [df.columns.values[14:18][col] + "_per_G" for col in range(4)]

# Changing the data type of some data (from object to numeric)
# Note convert_objects function have been deprecated (abandoned)
# But we could not care less about good coding practice, and this
# is the easiest way to convert, so just ignore the warning
df = df.convert_objects(convert_numeric=True)

# Dealing with Nan values in data type conversion
# The NaNs in our data indicate that a player has not played in the NBA.
# We should replace these NaNs with 0s to indicate that the player has not accumulated any stats.
df = df[:].fillna(0)

# Converting the columns Yrs, G, MP, PTS, TRB, and AST to integers using astype().
# As it turns out, slicing a dataframe object is quite convenient, we simply use the function loc():
# df.loc[first_row_label:last_row_label , first_col_label:last_col_label]
df.loc[:,'Yrs':'AST'] = df.loc[:,'Yrs':'AST'].astype(int)

# and we have the data types we want
print(df.dtypes)

# Insert a column about draft year
df.insert(0, 'Draft_Yr', 2014)

# Above is a good practice for me to understand how to scrape!
# It is truly fascinating!

# Let's turn to scraping and cleaning data for drafts from 1966 to present!

# Create a template so we can access this in the following for loop
url_template = "http://www.basketball-reference.com/draft/NBA_{year}.html"

# create an empty DataFrame
draft_df = pd.DataFrame()

for year in range(1950, 2019):  # for each year
    url = url_template.format(year=year)  # get the url

    html = urlopen(url)  # get the html
    soup = BeautifulSoup(html, 'html5lib')  # create our BS object

    # get our player data
    data_rows = soup.findAll('tr')[2:]
    player_data = [[td.getText() for td in data_rows[i].findAll('td')]
                   for i in range(len(data_rows))]

    # Turn yearly data into a DatFrame
    year_df = pd.DataFrame(player_data, columns=column_headers)
    # create and insert the Draft_Yr column
    year_df.insert(0, 'Draft_Yr', year)

    # Append to the big dataframe
    draft_df = draft_df.append(year_df, ignore_index=True)

# Convert data to proper data types
draft_df = draft_df.convert_objects(convert_numeric=True)

# Get rid of the rows full of null values
draft_df = draft_df[draft_df.Player.notnull()]

# Replace NaNs with 0s
draft_df = draft_df.fillna(0)

# Rename Columns
draft_df.rename(columns={'WS/48':'WS_per_48'}, inplace=True)
# Change % symbol
draft_df.columns = draft_df.columns.str.replace('%', '_Perc')
# Add per_G to per game stats
draft_df.columns.values[15:19] = [draft_df.columns.values[15:19][col] +
                                  "_per_G" for col in range(4)]

# Changing the Data Types to int
draft_df.loc[:,'Yrs':'AST'] = draft_df.loc[:,'Yrs':'AST'].astype(int)


draft_df['Pk'] = draft_df['Pk'].astype(int) # change Pk to int

draft_df.to_csv("draft_data_1966_to_2018.csv")
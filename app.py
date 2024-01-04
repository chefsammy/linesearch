import streamlit as st
import pandas as pd
import numpy as np
import pybet

# STREAMLIT PREFS
st.set_page_config(layout='wide')

# GLOBAL DATA TO USE
base = pd.read_csv('./current-logs.csv')
ALL_PLAYERS = sorted(list(set(base.Name)))
ALL_PLAYERS.insert(0, 'Any Player')
ALL_TEAMS = sorted(list(set(base.Team)))
scores = pd.read_csv('./current-scoreboard.csv')
offense = pd.read_csv('./current_offense.csv')

# FILTER PLAYERS BY POSITION
def filter_players(df: pd.DataFrame, positions=[]):
   df = df[df['Pos'].isin(positions)]
   return list(df.Player)

# ADD COMBOS TO DATAFRAME
def add_combos(df: pd.DataFrame):
   df['P+R'] = df['Points'] + df['Rebounds']
   df['P+A'] = df['Points'] + df['Assists']
   df['R+A'] = df['Rebounds'] + df['Assists']
   df['P+R+A'] = df['Points'] + df['Rebounds'] + df['Assists']
   df['Stocks'] = df['Steals'] + df['Blocks']
   return df

# UPDATE PLAYER DF
def get_data(
      player="Any Player", opponents=[], min_low=0, min_high=48, home_away='Both', win_loss='Both', mov_min=0, mov_max=100, positions=[], game_split='Full Season'
   ):
   # Take care of log-based data
   df = pd.read_csv('./current-logs.csv').drop(columns=['Unnamed: 0'])
   df = add_combos(df)
   has = scores[['GameId', 'Team', 'TeamScore', 'OppScore', 'Home']].copy()
   has['Win'] = has['TeamScore'] > has['OppScore']
   has['MOV'] = np.abs(has['TeamScore'] - has['OppScore'])
   df = df.merge(has, on=['GameId', 'Team'])
   df = df.sort_values(by='Date', ascending=False)
   # Filter for specific player
   if player != "Any Player":
      df = df[df['Name'] == player]
   # Filter for opponents
   if len(opponents) > 0:
      df = df[df['Opponent'].isin(opponents)]
   # Filter for home/away
   if home_away == 'Home':
      df = df[df['Home'] == True]
   elif home_away == 'Away':
      df = df[df['Home'] == False]
   # Filter for win/loss
   if win_loss == 'Win':
      df = df[df['Win'] == True]
   elif win_loss == 'Loss':
      df = df[df['Win'] == False]
   # Filter for position
   if len(positions) > 0:
      valid_players = filter_players(offense, positions)
      df = df[df['Name'].isin(valid_players)]
   # Adjust for minutes played, margin of victory
   df = df[
      (df['Minutes'] >= min_low) & (df['Minutes'] <= min_high) & (df['MOV'] >= mov_min) & (df['MOV'] <= mov_max)
   ].drop(columns=['GameId', 'MOV'])
   # Filter for games split
   if game_split == 'Last 5':
      return df.head(5)
   elif game_split == 'Last 10':
      return df.head(10)
   elif game_split == 'Last 30':
      return df.head(30)
   else:
      return df

# PAGE HEADER
st.header("2023-24 Player Logs")
st.markdown('''
            Below are all player counting statistics this season. Utilize the filters to parse down
            the data.
            ''')

# FILTERS
with st.form('log_filters'):
   st.markdown('''
               All player positions and advanced statistics come from [Cleaning the Glass](https://cleaningtheglass.com). Note that positions are estimated and may not reflect your best ideas of player positions. If you need help with getting started with research, you can see some examples [here](https://x.com).
               ''')
   # Form Row 1
   row1 = st.columns([1, 1, 1, 1])
   players = row1[0].selectbox('Player', ALL_PLAYERS, placeholder='Choose player') # Filter the player(s)
   opponents = row1[1].multiselect('Opponent', ALL_TEAMS, placeholder='Choose opponents') # Filter the opponent(s)
   min_low = row1[2].number_input('Min. Minutes Played', value=0, step=1)
   min_high = row1[3].number_input('Max. Minutes Played', value=48, step=1)
   # Form Row 2
   row2 = st.columns([2, 2, 2, 1, 1])
   mov_min = row2[0].number_input('Min. Margin of Victory', value=1, step=1)
   mov_max = row2[1].number_input('Max. Margin of Victory', value=100, step=1)
   rest = row2[2].multiselect('Days Rest', ["0", "1", "2", "3+"], placeholder='Days between Games')
   hab = row2[3].radio('Home/Away', ['Home', 'Away', 'Both'])
   wls = row2[4].radio('Win/Loss', ['Win', 'Loss', 'Both'])
   # Form Row 3 (Splits)
   row3 = st.columns([1])
   game_split = row3[0].selectbox('Games Split', ['Last 5', 'Last 10', 'Last 30', 'Full Season'], placeholder='Choose a games split')
   # Form Row 4
   positions = st.multiselect('Position', ['Point', 'Combo', 'Wing', 'Forward', 'Big'], placeholder='Choose positions')
   # Update
   st.form_submit_button('Update Data')
   
# DISPLAY DF
st.dataframe(
   get_data(
      players, opponents, min_low, min_high, hab, wls, mov_min, mov_max, positions,
      game_split
   ),
   use_container_width=True
)

st.markdown('''
   ## Prop Report
   If you'd like to do research on particular prop with the given filters above, set the information here.
''')

# PROP INPUT
with st.form('prop_input'):
   row = st.columns([2, 2, 1, 1])
   prop_type = row[0].selectbox(
      'Prop Type',
      ['Points', 'Rebounds', 'Assists', 'Steals', 'Blocks', 'Threes', 'P+R', 'P+A', 'R+A', 'P+R+A', 'Stocks', 'Turnovers']
   )
   prop_line = row[1].number_input('Line', value=10.5, step=0.5)
   over_odds = row[2].number_input('Over Odds', value=-110, step=10)
   under_odds = row[3].number_input('Under Odds', value=-110, step=10)
   st.form_submit_button('Get Prop Data')
   
# Assemble prop research data
prop_data = get_data(
   players, opponents, min_low, min_high, hab, wls, mov_min, mov_max, positions, game_split
)
prop_data['Game'] = prop_data['Opponent'] + ' ' + prop_data['Date'].astype(str)
hit_rate = np.mean(prop_data[prop_type] > prop_line)

# Display prop research data
st.markdown('### Prop Results')
st.markdown('### ')
prop_information = st.columns([3, 1])
prop_information[0].bar_chart(prop_data, x='Game', y=prop_type)
prop_information[1].markdown(
   f'''
   The over has a hit rate of {round(hit_rate * 100, 1)}% and an implied probability of {round(pybet.implied_probability(over_odds) * 100, 1)}%. This gives an expected profit of \n
   The under has a hit rate of {round((1 - hit_rate) * 100, 1)}% and an implied probability of {round(pybet.implied_probability(under_odds) * 100, 1)}%.
   ''')
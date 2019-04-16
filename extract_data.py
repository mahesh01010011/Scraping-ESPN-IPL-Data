import csv
import os

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm


SUBFOLDER_HTML = 'Downloads'
SUBFOLDER_SUMMARY = 'Match Results'

innings_id = ('gp-inning-00', 'gp-inning-01')

df_batting = pd.DataFrame()
df_bowling = pd.DataFrame()

for season in tqdm(os.listdir(f'{SUBFOLDER_SUMMARY}')[::-1]):
    with open(f'{SUBFOLDER_SUMMARY}/{season}', 'r') as fr:
        matches = list(csv.reader(fr))[1:][::-1]
    
    for match in tqdm(matches):
        file_name = match[-1].split('/')[-1]
        if match[3] in ('abandoned', 'no result', '-'): # '-' is for live match
            continue
        
        with open(f'{SUBFOLDER_HTML}/{file_name}', 'rb') as fr:
            soup = BeautifulSoup(fr.read(), 'lxml')
        match_id = file_name.replace('.html', '')
        
        for k, inning_id in enumerate(innings_id, start=1):
            inning = soup.find('div', {'id': inning_id})
            
            sec_batting = inning.find('div', {'class': 'scorecard-section batsmen'})
            data_batting = [['Match ID', 'Innings', 'Player ID'] + \
                [div.text for div in sec_batting.find('div', {'class': 'wrap header'}).find_all('div')[:-1]]] # last div is empty
            for i in sec_batting.find_all('div', {'class': 'wrap batsmen'}):
                tmp = i.find_all('div')
                data_batting.append([match_id, k, tmp[0].a['href'].split('/')[-1][:-5]] + \
                    [div.text for div in tmp[:-1]]) # last div is empty
            
            sec_bowling = inning.find('div', {'class': 'scorecard-section bowling'}).table
            data_bowling = [['Match ID', 'Innings', 'Player ID'] + \
                [th.text for th in sec_bowling.thead.tr.find_all('th') if len(th.text) > 0]]
            for tr in sec_bowling.tbody.find_all('tr'):
                tmp = tr.find_all('td')
                data_bowling.append([match_id, k, tmp[0].a['href'].split('/')[-1][:-5]] + \
                    [td.text for td in tmp if len(td.text) > 0])
            
            df_batting = df_batting.append(pd.DataFrame(data_batting[1:], columns=data_batting[0]), ignore_index=True, sort=False)
            df_bowling = df_bowling.append(pd.DataFrame(data_bowling[1:], columns=data_bowling[0]), ignore_index=True, sort=False)

df_batting.rename(columns={'': 'Commentary', 'BATSMEN': 'Batsman'}, inplace=True)

df_batting.to_csv('Batting.csv', index=False)
df_bowling.to_csv('Bowling.csv', index=False)

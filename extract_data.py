import argparse
import csv
import os

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm


def parse_summary(inn_summary, extras, match_id, innings, team_info):
    tmp = [i.split() for i in extras.upper()[:-1].split('(')[-1].split(',')]
    if extras == '0':
        extras = dict()
    else:
        extras = {k: int(v) for k, v in tmp}
    
    tmp = inn_summary.split()
    rr = float(tmp[-1][:-1])
        
    overs = float(tmp[-4][1:])
    score = tmp[0].split('/')
    wickets = int(score[1]) if len(score) > 1 else 10
    
    return pd.Series({
        'Match ID': match_id,
        'Innings': innings,
        'Team ID': team_info[0],
        'Team': team_info[1],
        'Total': int(score[0]),
        'Wickets': wickets,
        'Overs': overs,
        'RR': rr,
        **extras,
    })

if __name__ == '__main__':
    SUBFOLDER_HTML = 'Downloads'
    SUBFOLDER_SUMMARY = 'Match Results'
    
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-a', '--all', help='extract all downloaded data', action='store_true')
    # # parser.add_argument('-f', '--force_live', help='force download live match data', action='store_true')
    # args = parser.parse_args()
    
    dfs_batting = []
    dfs_bowling = []
    summaries = []
    
    innings_id = ('gp-inning-00', 'gp-inning-01')
    
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
            
            div_team_info = soup.find_all('div', {'class': 'cscore_truncate'})[:2]
            team_info = [
                (div.a['href'].split('/')[-2], div.span.text) for div in div_team_info
            ]
            
            for inning, inning_id in enumerate(innings_id, start=1):
                div_inning = soup.find('div', {'id': inning_id})
                
                # Batting
                div_batting = div_inning.find('div', {'class': 'scorecard-section batsmen'})
                data_batting = [['Match ID', 'Innings', 'Player ID'] + \
                    [div.text for div in div_batting.find('div', {'class': 'wrap header'}).find_all('div')[:-1]]] # last div is empty
                for i in div_batting.find_all('div', {'class': 'wrap batsmen'}):
                    tmp = i.find_all('div')
                    data_batting.append([match_id, inning, tmp[0].a['href'].split('/')[-1][:-5]] + \
                        [div.text for div in tmp[:-1]]) # last div is empty
                
                # Bowling
                div_bowling = div_inning.find('div', {'class': 'scorecard-section bowling'}).table
                data_bowling = [['Match ID', 'Innings', 'Player ID'] + \
                    [th.text for th in div_bowling.thead.tr.find_all('th') if len(th.text) > 0]]
                for tr in div_bowling.tbody.find_all('tr'):
                    tmp = tr.find_all('td')
                    data_bowling.append([match_id, inning, tmp[0].a['href'].split('/')[-1][:-5]] + \
                        [td.text for td in tmp if len(td.text) > 0])
                
                dfs_batting.append(pd.DataFrame(data_batting[1:], columns=data_batting[0]))
                dfs_bowling.append(pd.DataFrame(data_bowling[1:], columns=data_bowling[0]))
                
                # Summary
                extras = div_inning.find('div', {'class': 'wrap extras'}).find_all('div')[-1].text
                inn_summary = div_inning.find('div', {'class': 'wrap total'}).find_all('div')[-1].text
                summaries.append(parse_summary(inn_summary, extras, match_id, inning, team_info[inning-1]))
    
    df_batting = pd.concat(dfs_batting, sort=False)
    df_bowling = pd.concat(dfs_bowling, sort=False)
    df_misc = pd.DataFrame(summaries)
    
    df_batting.rename(columns={'': 'Commentary', 'BATSMEN': 'Batsman'}, inplace=True)
    
    df_batting.to_csv('Batting.csv', index=False)
    df_bowling.to_csv('Bowling.csv', index=False)
    df_misc.to_csv('Summary.csv', index=False)

import argparse
import csv
import os
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


def fetch_match_results(season, url, force_live=False):
    rh = {
        'Host': 'www.espncricinfo.com',
        'Referer': 'http://stats.espncricinfo.com/ci/engine/records/team/match_results.html?id=12741;type=tournament',
    }
    r = s.get(urljoin(BASE_URL, url), headers=rh)
    soup = BeautifulSoup(r.content, 'lxml')
    next_url = soup.find(text='Match results').parent['href']
    
    rh = {
        'Host': 'stats.espncricinfo.com',
        'Referer': r.url,
    }
    r = requests.get(urljoin(BASE_URL, next_url), headers=rh)
    soup = BeautifulSoup(r.content, 'lxml')
    table = soup.find('table', {'class': 'engineTable'})
    data = [['Season'] + [i.text for i in table.thead.tr.find_all('th')] + ['Match Link']]
    for tr in table.tbody.find_all('tr'):
        tds = tr.find_all('td')
        tmp = [season] + [i.text for i in tds] + [tds[-1].a['href']]
        if tmp[3] == '-' and not force_live:
            continue
        data.append(tmp)
    
    with open(f'{SUBFOLDER_CSV}/{season}.csv', 'w') as f:
        csv.writer(f, lineterminator='\n').writerows(data)
    
    return data, r.url

def download_matches(data, referer, force_live=False):
    rh = {
        'Host': 'www.espncricinfo.com',
        'Referer': referer,
    }
    for row in tqdm(data):
        if row[3] == '-' and not force_live:
            continue
        r = requests.get(urljoin(BASE_URL, row[-1]), headers=rh)
        with open(f'{SUBFOLDER_HTML}/{row[-1].split("/")[-1]}', 'wb') as f:
            f.write(r.content)

if __name__ == '__main__':
    BASE_URL = 'http://stats.espncricinfo.com'
    SUBFOLDER_CSV = 'Match Results'
    SUBFOLDER_HTML = 'Downloads'
    main_links = {
        2019: '/ci/engine/series/1165643.html?view=records',
        2018: '/ci/engine/series/1131611.html?view=records',
        2017: '/ci/engine/series/1078425.html?view=records',
        2016: '/ci/engine/series/968923.html?view=records',
        2015: '/ci/engine/series/791129.html?view=records',
        2014: '/ci/engine/series/695871.html?view=records',
        2013: '/ci/engine/series/586733.html?view=records',
        2012: '/ci/engine/series/520932.html?view=records',
        2011: '/ci/engine/series/466304.html?view=records',
        2010: '/ci/engine/series/418064.html?view=records',
        2009: '/ci/engine/series/374163.html?view=records',
        2008: '/ci/engine/series/313494.html?view=records',
    }
    rh_common = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3734.0 Safari/537.36',
    }
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--all', help='download all match data', action='store_true')
    parser.add_argument('-f', '--force_live', help='force download live match data', action='store_true')
    args = parser.parse_args()
    
    os.makedirs(f'{SUBFOLDER_CSV}', exist_ok=True)
    os.makedirs(f'{SUBFOLDER_HTML}', exist_ok=True)
    
    with requests.Session() as s:
        s.headers.update(rh_common)
        if args.all:
            for season, main_link in main_links.items():
                print(season)
                data, referer = fetch_match_results(season, main_link, force_live=args.force_live)
                download_matches(data[1:], referer, force_live=args.force_live)
        else:
            season = datetime.now().year
            try:
                with open(f'{SUBFOLDER_CSV}/{season}.csv', 'r') as f:
                    downloaded = len(list(csv.reader(f)))
            except FileNotFoundError:
                downloaded = 0
            data, referer = fetch_match_results(season, main_links[season], force_live=args.force_live)
            download_matches(data[downloaded:], referer, force_live=args.force_live)

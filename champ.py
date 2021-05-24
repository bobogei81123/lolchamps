import pandas as pd
import glob
import matplotlib.pyplot as plt
import numpy as np
import requests
import json


CHAMPIONS_URL = ('http://ddragon.leagueoflegends.com/'
                 'cdn/11.8.1/data/en_US/champion.json')


def get_champions_list():
    js = requests.get(CHAMPIONS_URL).json()
    return list(champ['name'] for champ in js['data'].values())


CHAMPIONS = get_champions_list()

ALL_CSV = glob.glob('./csv/*.csv')
LEAGUES = ['NA LCS', 'EU LCS', 'LMS', 'MSI', 'WCS', 'LCK', 'LPL']

df = pd.concat((pd.read_csv(csv, dtype={'patch': str})
                for csv in ALL_CSV), ignore_index=True)
df = df[df.patch.notna()][df.league.isin(LEAGUES)]


def patch_key(p):
    return tuple(int(x) for x in p.split('.'))


patches = sorted(pd.unique(df['patch']), key=patch_key)

patch_counts = (
    df[df.playerid == 100]
    .groupby('patch')
    .size()
    .reset_index(name='counts')
)

t = df
t = t[(t.playerid == 1) | (t.playerid == 6)]
t = pd.concat(
    [t[['patch', f'ban{i}']].rename(columns={f'ban{i}': 'champion'})
     for i in range(1, 6)],
    ignore_index=True,
)
t = t[t.champion.notna()]
banned = (
    t.groupby(['patch', 'champion'])
    .size()
    .reset_index(name='counts')
)


t = df
t = t[t.playerid <= 10]
t = t[['patch', 'champion']]
picked = (
    t.groupby(['patch', 'champion'])
    .size()
    .reset_index(name='counts')
)

# print(picked[picked.champion == 'Aurelion Sol'])
# exit(0)
dt = {}


def champ_stat(prob):
    if prob >= 0.75:
        return 'OP'
    if prob >= 0.35:
        return 'Meta'
    if prob >= 0.1:
        return 'OK'
    return 'Sad'


for champ in CHAMPIONS:
    t = pd.concat([
        banned[banned.champion == champ],
        picked[picked.champion == champ],
    ])
    t = t.groupby(['patch', 'champion']).sum().reset_index()
    t = t[['patch', 'counts']]
    records = {patch: 0 for patch in patches}
    records.update(t.values.tolist())
    records = sorted(records.items(), key=lambda p: patch_key(p[0]))

    X = []
    Y = []
    for patch, count in records:
        pc = patch_counts[patch_counts.patch == patch]['counts'].iloc[0]
        X.append(patch)
        Y.append(count / pc)

    stats = [champ_stat(prob) for prob in Y]

    data = {
        'patch': X,
        'prob': Y,
        'stats': stats,
    }
    dt[champ] = data


with open('data/data.json', 'w') as f:
    json.dump(dt, f)

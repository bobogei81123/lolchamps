import pandas as pd
import glob
import matplotlib.pyplot as plt
import numpy as np

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
t = t[t.playerid <= 10]
t = t[['patch', 'champion']]
patch_champ_counts = (
    t.groupby(['patch', 'champion'])
    .size()
    .reset_index(name='counts')
)

X = []
Y = []

def h(p):
    if p <= 1e-10:
        return 0
    return -p * np.log2(p)

for patch in patches:
    games = patch_counts[patch_counts.patch == patch].iloc[0].counts
    if games <= 50:
        continue

    X.append(patch)
    records = patch_champ_counts[patch_champ_counts.patch == patch]
    l = list(records.counts)
    ent = 0.0
    for x in l:
        prob = x / games
        ent += h(prob) + h(1 - prob)
    Y.append(ent)


def smooth(y, d=1):
    ln = len(y)
    ls = []
    for i in range(ln):
        l, r = max(0, i - d), min(ln, i + d + 1)
        new = (sum(y[l:r]) + y[i]) / (len(y[l:r]) + 1)
        ls.append(new)

    return ls


coefs = np.polyfit(range(len(Y)), Y, 3)
Y_poly = np.polyval(coefs, range(3, len(Y) - 3))

plt.plot(smooth(Y, 1))
plt.xticks(range(len(Y)), X, rotation=80)
plt.show()

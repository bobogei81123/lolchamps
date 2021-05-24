import json
from math import log2
import matplotlib.pyplot as plt
import numpy as np

with open('data.json') as f:
    data = json.load(f)

banned = data['banned']
picked = data['picked']
patches = data['patches']

X = []
Y = []

# for p in patches:
    # patch = p['patch']
    # count = p['count']

    # n_ban = banned['Lulu'].get(patch, 0)
    # n_pick = picked['Lulu'].get(patch, 0)
    # n = n_ban + n_pick
    # prob = n / count

    # if count >= 50 and patch != '__unknown__':
        # X.append(patch)
        # Y.append(prob)

    # print(patch, prob)


def h(p):
    if p <= 1e-10:
        return 0
    return -p * log2(p)


for p in patches:
    patch = p['patch']
    count = p['count']
    ent = 0

    for mp in picked.values():
        # prob = mp.get(patch, 0) / (count * 10)
        # ent += h(prob)
        prob = mp.get(patch, 0) / count
        if patch == '10.17':
            print(prob)
        ent += h(prob) + h(1 - prob)

    print(f'patch {patch} game = {count}, entropy = {ent:.3f}')
    if count >= 60 and patch != '__unknown__':
        X.append(patch)
        Y.append(ent)

# plt.semilogy(Y)

def smooth(y):
    ln = len(y)
    ls = []
    for i in range(ln):
        l, r = max(0, i - 1), min(ln, i + 2)
        new = sum(y[l:r]) / len(y[l:r])
        ls.append(new)

    return ls


coefs = np.polyfit(range(len(Y)), Y, 3)
Y_poly = np.polyval(coefs, range(3, len(Y) - 3))

# plt.plot(smooth(Y))
plt.plot(Y)
plt.plot(range(3, len(Y) - 3), Y_poly)
plt.xticks(range(len(Y)), X, rotation=80)
plt.show()

"""Solve many rule variants and print one JSON line per variant.

Usage: python3 variants.py [--free] > results.jsonl
  --free  also try free placement order (very slow in pure Python)

Each line: game value from the empty board (1 White wins, 0 draw, -1 Black wins),
how many of White's first moves win/draw/lose, and outcome rates when both sides
play uniformly random legal moves.
"""
import sys, json, itertools
from functools import lru_cache
from multiprocessing import Pool
sys.setrecursionlimit(100000)

LINES = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]

def nbrs(diag):
    out = []
    for i in range(9):
        r, c = divmod(i, 3); l = []
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if (dr, dc) == (0, 0): continue
                if not diag and dr and dc: continue
                if 0 <= r+dr < 3 and 0 <= c+dc < 3: l.append((r+dr)*3 + c+dc)
        out.append(tuple(l))
    return out

def analyze(rules):
    diag = rules.get('diag', False); stay = rules.get('stay', False)
    order = rules.get('order', 'desc'); cyclic = rules.get('cyclic', False)
    nocenter = rules.get('nocenter', False); capwin = rules.get('capwin', True)
    pieces = tuple(rules.get('pieces', (2,2,2)))  # counts of 1,2,3
    NB = nbrs(diag)
    sign = (1, -1)

    def beats(a, b):
        if cyclic and a == 1 and b == 3: return True
        if cyclic and a == 3 and b == 1: return False
        return a > b

    def won(b, p):
        s = sign[p]
        return any(b[x]*s > 0 and b[y]*s > 0 and b[z]*s > 0 for x, y, z in LINES)

    def gen(b, hands, p):
        s = sign[p]; h = hands[p]; ms = []
        avail = [v for v in (1,2,3) if h[v-1] > 0]
        if avail:
            if order == 'desc': vals = [max(avail)]
            elif order == 'asc': vals = [min(avail)]
            else: vals = avail
            first = all(x == 0 for x in b)
            for v in vals:
                for i in range(9):
                    if b[i] == 0 and not (nocenter and first and i == 4):
                        ms.append(('P', i, v))
        for i in range(9):
            if b[i]*s > 0:
                for j in NB[i]:
                    if b[j]*s < 0 and beats(abs(b[i]), abs(b[j])):
                        ms.append(('C', i, j))
        return ms

    def play(b, hands, p, m):
        b = list(b); hs = list(hands)
        if m[0] == 'P':
            b[m[1]] = sign[p]*m[2]
            h = list(hs[p]); h[m[2]-1] -= 1; hs[p] = tuple(h)
        else:
            if stay: b[m[2]] = 0
            else: b[m[2]] = b[m[1]]; b[m[1]] = 0
        return tuple(b), tuple(hs), (capwin or m[0] == 'P')

    @lru_cache(maxsize=None)
    def V(b, hands, p, passed):
        ms = gen(b, hands, p)
        if not ms:
            return 0 if passed else V(b, hands, 1-p, True)
        target = 1 if p == 0 else -1
        best = None
        for m in ms:
            nb, nh, canwin = play(b, hands, p, m)
            if canwin and won(nb, p): return target
            v = V(nb, nh, 1-p, False)
            if best is None or (v > best if p == 0 else v < best): best = v
            if best == target: return best
        return best

    @lru_cache(maxsize=None)
    def R(b, hands, p, passed):
        ms = gen(b, hands, p)
        if not ms:
            return (0.0, 1.0, 0.0) if passed else R(b, hands, 1-p, True)
        acc = [0.0, 0.0, 0.0]
        for m in ms:
            nb, nh, canwin = play(b, hands, p, m)
            if canwin and won(nb, p): r = (1.0,0,0) if p == 0 else (0,0,1.0)
            else: r = R(nb, nh, 1-p, False)
            for k in range(3): acc[k] += r[k]
        n = len(ms)
        return tuple(a/n for a in acc)

    b0 = (0,)*9; h0 = (pieces, pieces)
    val = V(b0, h0, 0, False)
    openings = {}
    for m in gen(b0, h0, 0):
        nb, nh, _ = play(b0, h0, 0, m)
        openings[f"{m[2]}@{m[1]}"] = V(nb, nh, 1, False)
    rr = R(b0, h0, 0, False)
    cnt = {k: sum(1 for v in openings.values() if v == k) for k in (1, 0, -1)}
    return dict(rules=rules, value=val, openings_W=cnt[1], openings_D=cnt[0], openings_B=cnt[-1],
                rand_W=round(rr[0],4), rand_D=round(rr[1],4), rand_B=round(rr[2],4), states=V.cache_info().currsize)

if __name__ == '__main__':
    variants = []
    orders = ('desc', 'asc', 'free') if '--free' in sys.argv else ('desc', 'asc')
    for diag, stay, order, cyclic in itertools.product((False, True), (False, True), orders, (False, True)):
        variants.append(dict(diag=diag, stay=stay, order=order, cyclic=cyclic))
    for diag in (False, True):
        variants.append(dict(diag=diag, order='desc', nocenter=True))
        variants.append(dict(diag=diag, order='desc', capwin=False))
    with Pool(8) as pool:
        for res in pool.imap_unordered(analyze, variants):
            print(json.dumps(res), flush=True)

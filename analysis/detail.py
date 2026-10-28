"""Skill and blunder metrics for the fair candidates.

Usage: python3 detail.py A|B|orig
"""
import sys, json
from functools import lru_cache
sys.setrecursionlimit(100000)
from variants import nbrs, LINES

def build(rules):
    diag = rules.get('diag', False); stay = rules.get('stay', False)
    order = rules.get('order', 'desc'); cyclic = rules.get('cyclic', False)
    NB = nbrs(diag); sign = (1, -1)
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
            v = max(avail) if order == 'desc' else min(avail)
            ms += [('P', i, v) for i in range(9) if b[i] == 0]
        for i in range(9):
            if b[i]*s > 0:
                for j in NB[i]:
                    if b[j]*s < 0 and beats(abs(b[i]), abs(b[j])): ms.append(('C', i, j))
        return ms
    def play(b, hands, p, m):
        b = list(b); hs = list(hands)
        if m[0] == 'P':
            b[m[1]] = sign[p]*m[2]; h = list(hs[p]); h[m[2]-1] -= 1; hs[p] = tuple(h)
        else:
            if stay: b[m[2]] = 0
            else: b[m[2]] = b[m[1]]; b[m[1]] = 0
        return tuple(b), tuple(hs)
    @lru_cache(maxsize=None)
    def V(b, hands, p, passed):
        ms = gen(b, hands, p)
        if not ms: return 0 if passed else V(b, hands, 1-p, True)
        t = 1 if p == 0 else -1; best = None
        for m in ms:
            nb, nh = play(b, hands, p, m)
            if won(nb, p): return t
            v = V(nb, nh, 1-p, False)
            if best is None or (v > best if p == 0 else v < best): best = v
            if best == t: return best
        return best
    def child(b, hands, p, m):
        nb, nh = play(b, hands, p, m)
        if won(nb, p): return None, (1 if p == 0 else -1)
        return (nb, nh), V(nb, nh, 1-p, False)
    # mixed: 'opt' side plays a theoretically best move, tie-break by best result vs random; other random
    @lru_cache(maxsize=None)
    def M(b, hands, p, passed, optside):
        ms = gen(b, hands, p)
        if not ms: return (0.0,1.0,0.0) if passed else M(b, hands, 1-p, True, optside)
        res = []
        for m in ms:
            nb, nh = play(b, hands, p, m)
            if won(nb, p): r = (1.0,0,0) if p == 0 else (0,0,1.0); v = 1 if p == 0 else -1
            else: r = M(nb, nh, 1-p, False, optside); v = V(nb, nh, 1-p, False)
            res.append((v, r))
        if p == optside:
            if p == 0: return max(res, key=lambda x: (x[0], x[1][0], x[1][1]))[1]
            return min(res, key=lambda x: (x[0], -x[1][2], -x[1][1]))[1]
        n = len(res); return tuple(sum(x[1][k] for x in res)/n for k in range(3))
    # blunder rate along random play: prob a uniformly random move worsens the side's theoretical result
    @lru_cache(maxsize=None)
    def blunder(b, hands, p, passed):
        """returns (expected #moves, expected #blunders) over a random game from here"""
        ms = gen(b, hands, p)
        if not ms: return (0.0, 0.0) if passed else blunder(b, hands, 1-p, True)
        cur = V(b, hands, p, passed); tm = tb = 0.0
        for m in ms:
            nb, nh = play(b, hands, p, m)
            if won(nb, p): v = 1 if p == 0 else -1; sub = (0.0, 0.0)
            else: v = V(nb, nh, 1-p, False); sub = blunder(nb, nh, 1-p, False)
            bl = 1.0 if v != cur else 0.0
            tm += 1 + sub[0]; tb += bl + sub[1]
        n = len(ms); return (tm/n, tb/n)
    return dict(V=V, M=M, gen=gen, play=play, child=child, blunder=blunder, won=won)

if __name__ == '__main__':
    cands = {'A': dict(diag=True, stay=True, order='asc'),
             'B': dict(diag=True, stay=True, order='desc', cyclic=True),
             'orig': dict(diag=False, stay=False, order='desc')}
    which = sys.argv[1]
    g = build(cands[which]); b0 = (0,)*9; h0 = ((2,2,2),(2,2,2))
    print(which, cands[which])
    print(' value', g['V'](b0, h0, 0, False))
    print(' W optimal vs random B  (W/D/B):', [round(x,4) for x in g['M'](b0, h0, 0, False, 0)])
    print(' random W vs B optimal  (W/D/B):', [round(x,4) for x in g['M'](b0, h0, 0, False, 1)])
    mv, bl = g['blunder'](b0, h0, 0, False)
    print(f' random game: avg moves {mv:.2f}, avg blunders {bl:.2f}')
    # opening -> black's replies: how many hold vs lose
    for i in (4, 0, 1):
        m = g['gen'](b0, h0, 0); m = [x for x in m if x[1] == i][0]
        (b1, h1), v = g['child'](b0, h0, 0, m)
        reps = g['gen'](b1, h1, 1)
        vals = [g['child'](b1, h1, 1, r)[1] for r in reps]
        print(f'  open {m}: value {v}; black replies hold(draw/win) {sum(1 for x in vals if x <= 0)}/{len(vals)}')

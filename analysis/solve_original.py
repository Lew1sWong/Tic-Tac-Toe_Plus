"""Solve the ORIGINAL rules (3,3,2,2,1,1 order, bigger captures smaller).

Usage: python3 solve_original.py [--diag] [--stay]
  --diag  diagonal cells also count as adjacent
  --stay  the capturing piece stays put (default: it moves onto the captured cell)
"""
import sys
from functools import lru_cache
from fractions import Fraction

ORDER = (3,3,2,2,1,1)
W, B = 0, 1
LINES = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]

def neighbors(i, diag):
    r, c = divmod(i, 3)
    out = []
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            if dr == 0 and dc == 0: continue
            if not diag and dr != 0 and dc != 0: continue
            rr, cc = r+dr, c+dc
            if 0 <= rr < 3 and 0 <= cc < 3:
                out.append(rr*3+cc)
    return out

DIAG = "--diag" in sys.argv
STAY = "--stay" in sys.argv
NB = [neighbors(i, DIAG) for i in range(9)]

# board: tuple of 9, each None or (player, value)
def won(board, p):
    return any(all(board[i] is not None and board[i][0] == p for i in L) for L in LINES)

def moves(board, hand, p):
    """hand = (placed_count_W, placed_count_B)"""
    ms = []
    k = hand[p]
    if k < 6:
        v = ORDER[k]
        for i in range(9):
            if board[i] is None:
                ms.append(("place", i, v))
    for i in range(9):
        if board[i] is not None and board[i][0] == p:
            for j in NB[i]:
                if board[j] is not None and board[j][0] != p and board[j][1] < board[i][1]:
                    ms.append(("cap", i, j))
    return ms

def apply(board, hand, p, m):
    b = list(board)
    h = list(hand)
    if m[0] == "place":
        b[m[1]] = (p, m[2]); h[p] += 1
    else:
        if STAY: b[m[2]] = None
        else: b[m[2]] = b[m[1]]; b[m[1]] = None
    return tuple(b), tuple(h)

@lru_cache(maxsize=None)
def value(board, hand, p, passed):
    """value from White's perspective: 1 win, 0 draw, -1 loss. p to move."""
    ms = moves(board, hand, p)
    if not ms:
        if passed: return 0
        return value(board, hand, 1-p, True)
    best = -2 if p == W else 2
    for m in ms:
        nb, nh = apply(board, hand, p, m)
        if won(nb, p):
            v = 1 if p == W else -1
        else:
            v = value(nb, nh, 1-p, False)
        if p == W: best = max(best, v)
        else: best = min(best, v)
        if best == (1 if p == W else -1): break
    return best

@lru_cache(maxsize=None)
def randprob(board, hand, p, passed, mode):
    """returns (P(W win), P(draw), P(B win)).
    mode: 'both' both random; 'Wopt' W optimal (maximize win prob), B random; 'Bopt' W random, B optimal (minimize W win)."""
    ms = moves(board, hand, p)
    if not ms:
        if passed: return (Fraction(0), Fraction(1), Fraction(0))
        return randprob(board, hand, 1-p, True, mode)
    results = []
    for m in ms:
        nb, nh = apply(board, hand, p, m)
        if won(nb, p):
            r = (Fraction(1),Fraction(0),Fraction(0)) if p == W else (Fraction(0),Fraction(0),Fraction(1))
        else:
            r = randprob(nb, nh, 1-p, False, mode)
        results.append(r)
    opt = (mode == 'Wopt' and p == W) or (mode == 'Bopt' and p == B)
    if opt:
        if p == W: return max(results, key=lambda r: (r[0], r[1]))
        else: return max(results, key=lambda r: (r[2], r[1]))
    n = len(results)
    return tuple(sum(r[i] for r in results)/n for i in range(3))

empty = tuple([None]*9)
print("capture:", "eater stays, victim removed" if STAY else "eater moves onto victim square")
print("adjacency:", "8-dir (incl. diagonal)" if DIAG else "4-dir (orthogonal only)")
# Full game value from empty, White first
v0 = value(empty, (0,0), W, False)
print("Game value from empty board (White to move):", {1:"White wins",0:"Draw",-1:"Black wins"}[v0])
# After White places 3 in center
b1, h1 = apply(empty, (0,0), W, ("place", 4, 3))
v1 = value(b1, h1, B, False)
print("After White 3 in center, optimal play:", {1:"White wins",0:"Draw",-1:"Black wins"}[v1])
# all first moves
names = {0:"corner",1:"edge",2:"corner",3:"edge",4:"center",5:"edge",6:"corner",7:"edge",8:"corner"}
for i in range(9):
    bb, hh = apply(empty,(0,0),W,("place",i,3))
    print(f"  White 3 at {i} ({names[i]}):", {1:"White wins",0:"Draw",-1:"Black wins"}[value(bb,hh,B,False)])
for mode, label in [('both','both random'),('Wopt','White optimal vs random Black'),('Bopt','random White vs optimal Black')]:
    pw, pd, pb = randprob(b1, h1, B, False, mode)
    print(f"After center-3, {label}: W win {float(pw):.4f}, draw {float(pd):.4f}, B win {float(pb):.4f}")
# best black replies after center 3
print("Black replies to center-3 (value, W-win prob if both random afterwards):")
for m in moves(b1,h1,B):
    nb, nh = apply(b1,h1,B,m)
    v = value(nb,nh,W,False)
    pw,pd,pb = randprob(nb,nh,W,False,'both')
    print(f"  {m}: {({1:'White wins',0:'Draw',-1:'Black wins'})[v]}, random-play White win={float(pw):.3f}")

INF = 99
@lru_cache(maxsize=None)
def dtm(board, hand, p, passed):
    """plies until White wins with W minimizing, B maximizing; INF if not a forced W win"""
    ms = moves(board, hand, p)
    if not ms:
        if passed: return INF
        return dtm(board, hand, 1-p, True)
    res = []
    for m in ms:
        nb, nh = apply(board, hand, p, m)
        if won(nb, p):
            r = 1 if p == W else INF
        else:
            r = dtm(nb, nh, 1-p, False)
            r = r+1 if r < INF else INF
        res.append((r, m))
    return min(res)[0] if p == W else max(res)[0]

def pv(board, hand, p):
    line = []
    passed = False
    for _ in range(30):
        ms = moves(board, hand, p)
        if not ms: break
        best = None
        for m in ms:
            nb, nh = apply(board, hand, p, m)
            if won(nb, p): r = 1 if p == W else INF
            else:
                r = dtm(nb, nh, 1-p, False); r = r+1 if r < INF else INF
            key = r if p == W else -r
            if best is None or key < best[0]: best = (key, m, nb, nh)
        _, m, board, hand = best
        line.append(("W" if p == W else "B", m))
        if won(board, p): line.append("WIN " + ("W" if p == W else "B")); break
        p = 1-p
    return line, board

d = dtm(b1, h1, B, False)
print("After center-3: White forces a win in", d, "more plies (", (d+1)//2, "more White moves )" if d < INF else "")
line, fb = pv(b1, h1, B)
print("Principal variation (B resists longest, W wins fastest):", line)
def show(b):
    for r in range(3):
        print("   " + " ".join(("." if b[r*3+c] is None else ("w" if b[r*3+c][0]==W else "b")+str(b[r*3+c][1])) for c in range(3)))
show(fb)

function makeEngine(cfg) {
  "use strict";
  const ORDER = cfg.order === "asc" ? [1, 1, 2, 2, 3, 3] : [3, 3, 2, 2, 1, 1];
  const LINES = [0,1,2, 3,4,5, 6,7,8, 0,3,6, 1,4,7, 2,5,8, 0,4,8, 2,4,6];
  const NB = [];
  for (let i = 0; i < 9; i++) {
    const r = (i / 3) | 0, c = i % 3, l = [];
    for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) {
      if (!dr && !dc) continue;
      if (!cfg.diag && dr && dc) continue;
      const rr = r + dr, cc = c + dc;
      if (rr >= 0 && rr < 3 && cc >= 0 && cc < 3) l.push(rr * 3 + cc);
    }
    NB.push(l);
  }
  function beats(a, b) {
    if (cfg.cyclic) { if (a === 1 && b === 3) return true; if (a === 3 && b === 1) return false; }
    return a > b;
  }
  function gen(b, k, p, out) {
    const s = p === 0 ? 1 : -1; let n = 0;
    if (k[p] < 6) for (let i = 0; i < 9; i++) if (b[i] === 0) out[n++] = i;
    for (let i = 0; i < 9; i++) {
      const x = b[i] * s;
      if (x > 0) {
        const nb = NB[i];
        for (let t = 0; t < nb.length; t++) {
          const j = nb[t], y = b[j] * s;
          if (y < 0 && beats(x, -y)) out[n++] = 100 + i * 9 + j;
        }
      }
    }
    return n;
  }
  function wonLine(b, p) {
    const s = p === 0 ? 1 : -1;
    for (let t = 0; t < 24; t += 3) {
      if (b[LINES[t]] * s > 0 && b[LINES[t + 1]] * s > 0 && b[LINES[t + 2]] * s > 0) return [LINES[t], LINES[t + 1], LINES[t + 2]];
    }
    return null;
  }
  function won(b, p) {
    const s = p === 0 ? 1 : -1;
    for (let t = 0; t < 24; t += 3) if (b[LINES[t]] * s > 0 && b[LINES[t + 1]] * s > 0 && b[LINES[t + 2]] * s > 0) return true;
    return false;
  }
  function applyM(b, k, p, m) {
    if (m < 100) { b[m] = (p === 0 ? 1 : -1) * ORDER[k[p]]; k[p]++; return 0; }
    const f = ((m - 100) / 9) | 0, t = (m - 100) % 9, a = b[f], vic = b[t];
    if (cfg.stay) b[t] = 0; else { b[t] = a; b[f] = 0; }
    return (a + 3) * 7 + (vic + 3);
  }
  function undoM(b, k, p, m, u) {
    if (m < 100) { b[m] = 0; k[p]--; return; }
    const f = ((m - 100) / 9) | 0, t = (m - 100) % 9;
    b[f] = ((u / 7) | 0) - 3; b[t] = (u % 7) - 3;
  }
  function keyOf(b, k, p) {
    let h = 0;
    for (let i = 0; i < 9; i++) h = h * 7 + (b[i] + 3);
    return ((h * 49 + k[0] * 7 + k[1]) * 2 + p) + 1;
  }
  function table(bits) {
    const size = 1 << bits, mask = size - 1, shift = 32 - bits;
    const keys = new Uint32Array(size), vals = new Int16Array(size);
    let used = 0;
    return {
      get(key) {
        let i = Math.imul(key, 0x9E3779B1) >>> shift;
        while (true) { const x = keys[i]; if (x === 0) return 999; if (x === key) return vals[i]; i = (i + 1) & mask; }
      },
      put(key, v) {
        if (used > size * 0.7) { keys.fill(0); used = 0; }
        let i = Math.imul(key, 0x9E3779B1) >>> shift;
        while (keys[i] !== 0 && keys[i] !== key) i = (i + 1) & mask;
        if (keys[i] === 0) used++;
        keys[i] = key; vals[i] = v;
      },
      size() { return used; }
    };
  }
  const TV = table(23), TD = table(22);
  const stacks = [];
  for (let d = 0; d < 80; d++) stacks.push(new Int16Array(64));

  // Game value with White = +1, Black = -1, draw = 0. p is the side to move.
  function V(b, k, p, depth) {
    const key = keyOf(b, k, p);
    const c = TV.get(key);
    if (c !== 999) return c;
    const out = stacks[depth];
    const n = gen(b, k, p, out);
    let res;
    if (n === 0) {
      res = gen(b, k, 1 - p, stacks[depth + 1]) === 0 ? 0 : V(b, k, 1 - p, depth + 1);
    } else {
      const target = p === 0 ? 1 : -1;
      let best = p === 0 ? -2 : 2;
      for (let t = 0; t < n; t++) {
        const m = out[t], u = applyM(b, k, p, m);
        const v = won(b, p) ? target : V(b, k, 1 - p, depth + 1);
        undoM(b, k, p, m, u);
        if (p === 0 ? v > best : v < best) best = v;
        if (best === target) break;
      }
      res = best;
    }
    TV.put(key, res);
    return res;
  }
  // Plies until the winning side wins, winner hurrying and loser stalling. 999 when drawn.
  function D(b, k, p, depth) {
    const key = keyOf(b, k, p);
    const c = TD.get(key);
    if (c !== 999) return c;
    const v = V(b, k, p, depth);
    let res;
    if (v === 0) res = 900;
    else {
      const out = stacks[depth];
      const n = gen(b, k, p, out);
      if (n === 0) res = D(b, k, 1 - p, depth + 1);
      else {
        const winner = v === (p === 0 ? 1 : -1);
        let best = winner ? 900 : 0;
        for (let t = 0; t < n; t++) {
          const m = out[t], u = applyM(b, k, p, m);
          let d;
          if (won(b, p)) d = 1;
          else if (winner && V(b, k, 1 - p, depth + 1) !== v) d = -1;
          else d = 1 + D(b, k, 1 - p, depth + 1);
          undoM(b, k, p, m, u);
          if (d < 0) continue;
          if (winner ? d < best : d > best) best = d;
        }
        res = best;
      }
    }
    TD.put(key, res);
    return res;
  }

  const toB = (st) => Int8Array.from(st.b);
  function legal(st) {
    const out = new Int16Array(64);
    const n = gen(toB(st), st.k.slice(), st.p, out);
    return Array.from(out.subarray(0, n));
  }
  function next(st, m) {
    const b = Int8Array.from(st.b), k = st.k.slice(), p = st.p;
    applyM(b, k, p, m);
    const line = wonLine(b, p);
    return { st: { b: Array.from(b), k, p: 1 - p }, line };
  }
  function evalMoves(st) {
    const b = toB(st), k = st.k.slice(), p = st.p, out = new Int16Array(64);
    const n = gen(b, k, p, out), res = [];
    for (let t = 0; t < n; t++) {
      const m = out[t], u = applyM(b, k, p, m);
      const v = won(b, p) ? (p === 0 ? 1 : -1) : V(b, k, 1 - p, 1);
      undoM(b, k, p, m, u);
      res.push({ m, v });
    }
    return { value: V(b, k, p, 0), moves: res };
  }
  function choose(st) {
    const p = st.p, sg = p === 0 ? 1 : -1, b = toB(st), k = st.k.slice();
    const out = new Int16Array(64), n = gen(b, k, p, out), cands = [];
    for (let t = 0; t < n; t++) {
      const m = out[t], u = applyM(b, k, p, m);
      const imm = won(b, p);
      const v = imm ? sg : V(b, k, 1 - p, 1);
      cands.push({ m, s: v * sg, imm, b2: Int8Array.from(b), k2: k.slice() });
      undoM(b, k, p, m, u);
    }
    if (!cands.length) return null;
    const best = Math.max(...cands.map((c) => c.s));
    let pool = cands.filter((c) => c.s === best);
    if (best === 1) {
      const imm = pool.filter((c) => c.imm);
      if (imm.length) pool = imm;
      else {
        for (const c of pool) c.d = D(c.b2, c.k2, 1 - p, 1);
        const md = Math.min(...pool.map((c) => c.d));
        pool = pool.filter((c) => c.d === md);
      }
    } else {
      const o = 1 - p, out2 = new Int16Array(64);
      for (const c of pool) {
        const n2 = gen(c.b2, c.k2, o, out2);
        if (!n2) { c.trap = 0; continue; }
        let good = 0;
        for (let t = 0; t < n2; t++) {
          const m2 = out2[t], u2 = applyM(c.b2, c.k2, o, m2);
          const v2 = won(c.b2, o) ? (o === 0 ? 1 : -1) : V(c.b2, c.k2, p, 2);
          undoM(c.b2, c.k2, o, m2, u2);
          if (v2 * sg > best) good++;
        }
        c.trap = good / n2;
      }
      const mt = Math.max(...pool.map((c) => c.trap));
      pool = pool.filter((c) => Math.abs(c.trap - mt) < 1e-9);
    }
    return pool[Math.floor(Math.random() * pool.length)].m;
  }
  return { ORDER, NB, beats, legal, next, evalMoves, choose, cached: () => TV.size() };
}
